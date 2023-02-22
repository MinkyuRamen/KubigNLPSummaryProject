import pandas as pd
import pandas as np
import time

import re
import requests
from bs4 import BeautifulSoup

from scipy.spatial.distance import cosine

import torch
from transformers import PreTrainedTokenizerFast, BartForConditionalGeneration
from sentence_transformers import SentenceTransformer

def news_crwaling(search):
    headers = {'user-agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}

    # 검색어 설정
    search_query = search

    # 검색 결과 페이지의 URL입니다.
    base_url = 'https://search.naver.com/search.naver'
    url = f"https://search.naver.com/search.naver?query={search_query}"

    # HTTP GET 요청을 보내고 응답을 받습니다.
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # 뉴스 메뉴의 탭 요소를 가져옵니다.
    news_menu = soup.find("div", {"class": "lnb_group"}).find("ul").find_all("a")

    # 뉴스 메뉴의 탭의 링크 URL을 불러온다.
    for menu in news_menu:
        if menu.text=='뉴스':
            url = base_url + menu.get('href')
            break
    
    # parsing
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    news_list = soup.find_all('a', 'news_tit')
    news_info = soup.find_all('div', 'news_info')

    news_title = []
    news_url = []
    news_if = []

    for news_box in news_list:
        news_title.append(news_box.get_text())
    for url in news_list:
        news_url.append(url['href'])
    for info in news_info:
        news_if.append(info.get_text())

    news_content = []

    for url in news_url:
        # 본문 내용 가져오기
        try:
            response = requests.get(url, headers=headers)
        except:
            pass
        soup = BeautifulSoup(response.text, 'html.parser')

        # 본문 내용 추출
        content = ''
        for p in soup.find_all('p'):
            content += p.get_text()
        news_content.append(content)
    
    # 본문 전처리 >> 기사마다 HTML 구성이 다 다르다. 하나하나 다 전처리하기는 사실상 불가능하다.
    # 따라서 전처리가 잘 되지 않은 기사들은 cossim_model에서 걸러내기로 하였다.
    news_cnt_sr = []

    for news in news_content:
        d = re.sub(r'(\d{3})-(\d{4})-(\d{4})', ' ', news)
        d = re.sub(r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})', ' ', d)
        d = re.sub(r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})', ' ', d)
        d = re.sub(r'(\d{4})-(\d{2})-(\d{2})', ' ', d)
        d = re.sub(r'(\d{4}).(\d{2}).(\d{2})', ' ', d)
        d = re.sub(r'(\d{4}):(\d{2}):(\d{2})', ' ', d)
        d = re.sub(r'(\d{4})-(\d{4})', ' ', d)
        d = re.sub(r'[\n\t\r]', '', d)
        d = d.split('@')[0]
        news_cnt_sr.append(d)

    # 뉴스정보 전처리
    news_if_sr = []
    
    for info in news_if:
        info = ''.join(str(info).split()[-3:]).split()
        info = info[0][:-5].split('선정')
        news_if_sr.append(info)
    news_if_sr    

    return news_title, news_if_sr, news_cnt_sr

def sum_model(news_cnt_sr):

    tokenizer = PreTrainedTokenizerFast.from_pretrained('gogamza/kobart-summarization')
    model = BartForConditionalGeneration.from_pretrained('gogamza/kobart-summarization')

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

def cossim_model(news_title, news_sum):
    news_title = news_title
    news_sum = news_sum
    cos_sim = []

    model = SentenceTransformer('paraphrase-distilroberta-base-v1')
    # 문장 입력
    for i in range(len(news_title)):
        sentence1 = news_title[i]
        sentence2 = news_sum[i]

        # 두 문장을 벡터로 변환
        embeddings1 = model.encode(sentence1, convert_to_tensor=True)
        embeddings2 = model.encode(sentence2, convert_to_tensor=True)

        # 두 벡터 간 코사인 유사도를 계산
        cosine_similarity = 1 - cosine(embeddings1, embeddings2)

        # 유사도가 0.5 이상만 추출 >> 본문과 요약문이 동떨어진 기사 제거
        if cosine_similarity >= 0.5:
            cos_sim.append(cosine_similarity)
        else: cos_sim.append('')
    return cos_sim

def main(search):
    search = search
    news_title, news_if_sr, news_cnt_sr =  news_crwaling(search)
    news_sum = sum_model(news_cnt_sr)
    cos_sim = cossim_model(news_title, news_sum)
    
    df = []
    df = pd.DataFrame({'Title':news_title, 'Content':news_sum, 'Similiarity':cos_sim})
    df = df[~(df == '').any(axis=1)]
    # 요약시 발생하는 dummy 값이다. 따라서 제거해준다.
    df = df[~(df == '한국토지자원관리공단은 한국토지공사의 지분참여를 통해 일자리 창출을 도모할 예정이다.').any(axis=1)].reset_index(drop=True)
    # summary = dict(zip(df['Title'].values, df['Content'].values))
    summary = {i : string for i,string in enumerate(df.Content.values)}


    return summary

# def main(search):
#     # summary = {"뉴진스, 데뷔음반도 밀리언셀러…'OMG' 이어 두 번째": "뉴진스는 데뷔음반도 밀리언셀러...'OMG' 이어 두 번째 등록을 마쳤으며 08:19:27에 09번째 등록을 마쳤다.",'하이브 작년 매출 1.7조 역대 최대…"지민 3월 솔로 앨범"(종합2보)': '그룹 방탄소년단(BTS)의 소속사 하이브가 글로벌 팬덤 확장과 신인의 성공적인 데뷔 등으로 지난해 창사 이래 최대 매출을 올렸으며 21일 오후 국내·외 증권사 애널리스트와 주요 기관 투자자를 대상으로 기업 설명회를 개최했다.',"뉴진스, 미국 누적 앨범 판매량 10만장 돌파..민희진도 '축하'": '스타뉴스 가요 담당 윤상근 기자입니다.','"그게 사실은…" 뉴진스 민지, 레전드 \'비눗방울\' 직캠 비하인드 공개': "그룹 뉴진스 멤버 민지가 유튜브 '엘르 코리아' 채널에 출연해 'Attention' 무대에서 특수효과로 뿌려진 비눗방울을 톡 터트리며 센스있게 안무를 소화한 비하인드를 공개했다.",'뉴진스 민지, 배우 분위기 비결은 “톤온톤 사복 패션?”': '20일 매거진 엘르 코리아 유튜브 채널에는 ‘강해린 이상하다’ ESTJ 민지의 멤버 분석?! 뉴진스 민지의 #ASKMEANYTHING’이라는 제목의 영상이 올라왔다.'}

#     summary = {0: "삼성전자는 202 TV 신제품에 인공지능(AI) 기술을 적용해 최상의 화질을 제공하고 다양한 기기와의 연결 경험을 극대화한 '네오 QLED 8K' 등 2023년형 TV 신제품을 다음 달 9일 출시한다.", 1: '삼성전자가 잠정 4분기 매출 70조원, 영업이익 4조3000억원을 달성했다고 밝혔는데, 매출은 전년 대비 8.6% 줄었고, 영업이익은 전년 대비 69% 감소했다.', 2: "삼성전자[005930]는 3월 9일 공식 출시에 앞서 QLED 8K, 네오 QLED, OLED 모델을 먼저 판매하고 3월 1일부터 삼성 삼성 디지털프라자와 백화점에서 사전 구매 고객에게는 휴대용 프로젝터 '더 프리스타일', JBL 게이밍 헤드셋, 티빙 프리미엄 이용권 등 다양한 혜택을 제공한다.", 3: '10:54집닥이 삼성전자와 함께 집닥 인테리어 고객에게 TV, 세탁기, 인덕션, 에어컨 등 삼성전자 가전제품 인기 상품을 최대 43% 할인된 가격으로 제공하는 제휴 이벤트를 진행한다.', 4: '20일 LG전전자는 유럽경제위원회 회원국에 차량을 판매하는 완성차 고객에게 검증된 사이버보안을 갖춘 인포테인먼트 시스템과 텔레매틱스 부품을 안정적으로 공급하게 되면서 글로벌 전장 시장 공략에 힘이 더 실릴 전망이다.'}
#     return summary