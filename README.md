# KUBIG_2023_WIN Project
[23-1 NLP_뉴스기사요약.pdf](https://github.com/MinkyuRamen/KUBIG_2023_WIN/files/11405626/23-1.NLP_.pdf)

목적 : 개인 투자자를 위한 기업 투자정보 요약

### pre-trained model
- SKT-AI/KoBART model
https://github.com/SKT-AI/KoBART

- huggingface/Sentence-transformers
https://huggingface.co/sentence-transformers/paraphrase-distilroberta-base-v1

### fine-tuning
AI Hub 문서요약 텍스트 데이터 활용

- Train Data : 34,242 개
- Test Data  : 8,501  개

=> 직접 크롤링한 데이터에 KoBART를 finetuning한 model을 이용해 뉴스기사 요약 진행

=> 요약이 잘 안된 기사들을 거르기 위해 Title과 Content를 sentenceTransformer를 활용해 인코딩 후 유사도 구함

### service
<img src="https://img.shields.io/badge/html5-E34F26?style=for-the-badge&logo=html5&logoColor=white">

1. 유저가 탐색하고자 한느 기업명 입력 * 국내 상장 기업 중

2. 해당 기업의 최신 뉴스 정보 요약 * 네이버 중권 뉴스

3. 유저에게 요약 결과 전달
