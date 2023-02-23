import pandas as pd
import pandas as np
import time

import re
import requests
from bs4 import BeautifulSoup

from scipy.spatial.distance import cosine

import torch
from transformers import PreTrainedTokenizerFast, BartForConditionalGeneration, BartConfig
from sentence_transformers import SentenceTransformer



def news_crwaling(search):
    headers = {'user-agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}

    # 검색어 설정
    search_query = search

    # 검색 결과 페이지의 URL입니다.
    base_url = 'https://search.naver.com/search.naver'
    url = f"https://search.naver.com/search.naver?query={search_query}"


    # HTTP GET 요청을 보내고 응답을 받습니다.
    news_url = ''
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # 네이버에 원하는 주식명을 검색한 화면에서 증권정보 -> 관련뉴스 탭의 url을 가져옵니다.
    links = soup.find_all("a", href=True)

    for link in links:
        url = link['href']
        if "item/news" in url:   # item/news을 포함한 url은 "관련뉴스"탭의 url을 의미합니다.
            if re.match(r'(http|https)://', url):
                news_url = url

    # url 중 주식 코드만 가져옵니다.
    code = news_url[-6:]

    # 주식 코드 추출 완료

    ##  특정 검색어에 해당하는 관련 뉴스들의 url 가져오기

    # 네이버증권 -> 검색어 검색 -> 뉴스 공시에 해당 하는 웹 페이지로 이동
    url = "https://finance.naver.com/item/news_news.nhn?code=" + code

    # HTTP GET 요청을 보내고 응답을 받습니다.
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")

    links =[]
    for link in soup.find_all("a"):
        url = link.get("href")
        if "article" in url:   # article을 포함한 url만 수집, 뉴스 기사들에 해당
            links.append(url)
    link_result = []

    # 수집된 url에 http를 추가하여 저장
    for link in links: 
        add = 'https://finance.naver.com' + link
        link_result.append(add)
    
    ## 기사 제목 추출

    titles = []
    all_td = soup.findAll('td', {'class' : 'title'})

    for td in all_td:
        titles.append(td.find('a').get_text())

    # link,title 추출 완료 
    ## 뉴스 내용 추출

    article_result = []

    for link_news in link_result:

        article_source_code = requests.get(link_news).text
        article_html = BeautifulSoup(article_source_code, "lxml")
  
    # 뉴스 내용

        article_contents = article_html.select('.scr01')
        article_contents=article_contents[0].get_text()
        article_contents = re.sub('\n','',article_contents)
        article_contents = re.sub('\t','',article_contents)

        # cut extra text after Copyright mark
        if "ⓒ" in article_contents:
            article_contents=article_contents[:article_contents.index("ⓒ")]

        article_result.append(article_contents)
 


    return titles, article_result


def sum_model(news_cnt_sr):

    tokenizer = PreTrainedTokenizerFast.from_pretrained('gogamza/kobart-summarization')

    # 모델 구성을 위한 config 로드
    config = BartConfig.from_json_file("config.json")

    # 사전 학습된 가중치를 포함한 모델 로드
    model = BartForConditionalGeneration.from_pretrained("pytorch_model.bin", config=config)

    news_cnt_sr = news_cnt_sr
    news_sum = []
    summary = ''

    for news_cnt in news_cnt_sr:
        text = news_cnt

        text = text.replace('\n', ' ')

        raw_input_ids = tokenizer.encode(text)
        input_ids = [tokenizer.bos_token_id] + raw_input_ids + [tokenizer.eos_token_id]

        try:
            summary_ids = model.generate(torch.tensor([input_ids]),  num_beams=4,  max_length=512,  eos_token_id=1)
            summary = tokenizer.decode(summary_ids.squeeze().tolist(), skip_special_tokens=True)
            if len(summary) < 200: # 너무 긴 summary는 압축되지 못하는 parsing이 잘못되는 경우가 대부분이다.
                news_sum.append(summary)
            else:
                news_sum.append('')
        except:
            news_sum.append('')
    
    
    return news_sum

def main(search):
    search = search
    news_title, news_cnt_sr =  news_crwaling(search)
    news_sum = sum_model(news_cnt_sr)
    
    df = []
    df = pd.DataFrame({'Title':news_title, 'Content':news_sum})
    df = df[~(df == '').any(axis=1)]
    # 요약시 발생하는 dummy 값이다. 따라서 제거해준다.
    df = df[~(df == '한국토지자원관리공단은 한국토지공사의 지분참여를 통해 일자리 창출을 도모할 예정이다.').any(axis=1)].reset_index(drop=True)
    # summary = dict(zip(df['Title'].values, df['Content'].values))
    summary = {i : string for i,string in enumerate(df.Content.values)}


    return summary

