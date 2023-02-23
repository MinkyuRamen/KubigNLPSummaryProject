import requests
from bs4 import BeautifulSoup
import re


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
    title_result = []

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

        # cut too long text to prevent CUDA OOM issue
        # if len(article_contents)>=1500:
        #     article_contents=article_contents[:1500] # 수집 글자수 조절


        article_result.append(article_contents)
 


    return titles, article_result

a,b = news_crwaling('삼성전자')
print(len(a))
print(len(b))

# df = []
# import pandas as pd
# df = pd.DataFrame({'Title':a, 'Content':b})
# print(df)
# news_title, news_if_sr, news_cnt_sr

# 최종 결과  news_title 필요 , news_cnt_sr은 내용물

