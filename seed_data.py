import yfinance as yf
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# 1. 환경 변수(.env) 불러오기
load_dotenv()
key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

# 2. 파이어베이스 로그인 및 연결
cred = credentials.Certificate(key_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

# 3. 달러, 엔화, 유로 심볼 설정
tickers = {"USD": "KRW=X", "JPY": "JPYKRW=X", "EUR": "EURKRW=X"}

print("데이터 다운로드 및 저장을 시작합니다... (약 1~2분 소요)")

for currency, ticker in tickers.items():
    # 최근 6개월 데이터 가져오기
    data = yf.Ticker(ticker).history(period="6mo")
    
    for date, row in data.iterrows():
        # 날짜를 YYYY-MM-DD 문자로 변환
        date_str = date.strftime("%Y-%m-%d")
        value = float(row["Close"])
        
        # 엔화는 100엔 기준으로 맞추기 위해 100 곱하기
        if currency == "JPY":
            value = value * 100
            
        # 파이어베이스에 저장할 데이터 구조 만들기
        doc_data = {
            "date": date_str,
            "value": round(value, 2),
            "memo": "초기 데이터",
            "currency": currency
        }
        
        # Firestore의 'data' 컬렉션(폴더)에 추가하기
        db.collection("data").add(doc_data)
        
    print(f"{currency} 데이터 저장 완료!")

print("모든 작업이 성공적으로 끝났습니다! Firebase 콘솔에서 확인해보세요.")