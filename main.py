import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os
import requests  # openai 대신 추가
from fastapi import FastAPI
from datetime import datetime

# 1. 환경 변수 로드 및 Firebase 연결
load_dotenv()

# 서버가 재시작될 때 Firebase가 중복 실행되는 것을 방지합니다.
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# 2. FastAPI 앱 초기화
app = FastAPI(title="환율 AI 비서 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Pydantic을 활용한 데이터 검증 규칙 (미션 요구사항)
class RateData(BaseModel):
    date: str
    value: float
    memo: Optional[str] = None
    currency: str

@app.get("/")
def read_root():
    return {"message": "환율 AI 비서 백엔드 서버가 정상적으로 실행 중입니다!"}

# 4. 데이터 목록 조회 API 만들기
@app.get("/api/data")
def get_data(currency: Optional[str] = None):
    data_ref = db.collection("data")
    
    # URL에 ?currency=USD 처럼 특정 통화가 지정되면 필터링해서 가져옵니다.
    if currency:
        docs = data_ref.where("currency", "==", currency.upper()).stream()
    else:
        # 지정되지 않으면 전체 데이터를 가져옵니다.
        docs = data_ref.stream()

    results = []
    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id  # 수정/삭제할 때 필요한 문서 고유 ID를 추가합니다.
        results.append(item)
        
    return results

# 5. 데이터 추가 API (POST)
@app.post("/api/data")
def add_data(data: RateData):
    # Pydantic 모델(RateData)로 검증된 데이터를 딕셔너리로 변환하여 저장
    doc_ref = db.collection("data").add(data.dict())
    return {"message": "데이터가 추가되었습니다.", "id": doc_ref[1].id}

# 6. 데이터 수정 API (PUT)
@app.put("/api/data/{doc_id}")
def update_data(doc_id: str, data: RateData):
    # 특정 문서 ID를 찾아 내용 덮어쓰기
    db.collection("data").document(doc_id).set(data.dict())
    return {"message": f"{doc_id} 데이터가 수정되었습니다."}

# 7. 데이터 삭제 API (DELETE)
@app.delete("/api/data/{doc_id}")
def delete_data(doc_id: str):
    # 특정 문서 ID를 찾아 삭제
    db.collection("data").document(doc_id).delete()
    return {"message": f"{doc_id} 데이터가 삭제되었습니다."}

# 8. 데이터 요약 API (GET /api/data/summary) - AI 프롬프트 주입용 핵심 기능!
@app.get("/api/data/summary")
def get_summary():
    docs = db.collection("data").stream()
    
    # 통화별로 통계를 계산하기 위한 빈 바구니 준비
    summary = {
        "USD": {"count": 0, "sum": 0, "min": 99999, "max": 0},
        "JPY": {"count": 0, "sum": 0, "min": 99999, "max": 0},
        "EUR": {"count": 0, "sum": 0, "min": 99999, "max": 0}
    }
    
    # 파이어베이스에서 가져온 데이터를 하나씩 꺼내며 계산
    for doc in docs:
        item = doc.to_dict()
        curr = item.get("currency")
        val = item.get("value", 0)
        
        if curr in summary:
            summary[curr]["count"] += 1
            summary[curr]["sum"] += val
            
            # 최소값, 최대값 갱신
            if val < summary[curr]["min"]:
                summary[curr]["min"] = val
            if val > summary[curr]["max"]:
                summary[curr]["max"] = val
                
    # 계산된 총합(sum)을 개수(count)로 나누어 평균(average) 구하기
    result = {}
    for curr, stats in summary.items():
        if stats["count"] > 0:
            avg = round(stats["sum"] / stats["count"], 2)
            result[curr] = {
                "데이터 개수": f"{stats['count']}개",
                "평균 환율": avg,
                "최저 환율": stats["min"],
                "최고 환율": stats["max"]
            }
    
    return {"summary": result}

    from openai import OpenAI
from datetime import datetime

# 프론트엔드에서 받아올 채팅 요청 데이터 형식
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None  # 기존 대화를 이어갈 때 사용

# 9. 대화 목록 조회 API (GET)
@app.get("/api/conversations")
def get_conversations():
    docs = db.collection("conversations").stream()
    results = []
    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        results.append(item)
    # 최신 대화가 위로 오도록 시간순 정렬
    results.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return results

# 10. 특정 대화 불러오기 API (GET)
@app.get("/api/conversations/{doc_id}")
def get_conversation(doc_id: str):
    doc = db.collection("conversations").document(doc_id).get()
    if doc.exists:
        return doc.to_dict()
    return {"error": "대화를 찾을 수 없습니다."}

# 11. 대화 삭제 API (DELETE)
@app.delete("/api/conversations/{doc_id}")
def delete_conversation(doc_id: str):
    db.collection("conversations").document(doc_id).delete()
    return {"message": "대화가 삭제되었습니다."}

# 12. AI 챗봇 API (POST) - Anthropic(Claude) 규격으로 변경
@app.post("/api/chat")
def chat_with_ai(req: ChatRequest):
    # 1. 요약 데이터 불러오기
    summary_response = get_summary()
    summary_data = summary_response["summary"]

    # 2. 시스템 프롬프트 작성 (Anthropic은 이를 별도로 분리해서 보냅니다)
    system_prompt = f"""
    당신은 외환(FX) 시장 분석 AI 비서입니다.
    아래의 최신 환율 요약 데이터를 바탕으로 사용자의 질문에 친절하고 전문가처럼 답변하세요.
    
    [현재 환율 요약 데이터]
    - 달러(USD): {summary_data.get('USD')}
    - 엔화(JPY): {summary_data.get('JPY')}
    - 유로(EUR): {summary_data.get('EUR')}
    
    사용자의 질문에 위 데이터를 인용하여 객관적인 수치와 함께 답변해 주세요.
    """

    # 3. 대화 기록 구성하기 (시스템 프롬프트 제외)
    messages = []
    
    if req.conversation_id:
        doc = db.collection("conversations").document(req.conversation_id).get()
        if doc.exists:
            messages.extend(doc.to_dict().get("messages", []))
            
    # 사용자의 새로운 질문 추가
    messages.append({"role": "user", "content": req.message})

    # 4. Anthropic API 호출 설정
    url = "https://copa.codyssey.kr/v1/messages"
    headers = {
        # 따옴표로 감싸진 긴 키를 지우고 아래처럼 바꿉니다.
        "x-api-key": os.getenv("ANTHROPIC_API_KEY"),
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "claude-sonnet-4",
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": messages
    }

    # 5. API 요청 및 응답 처리
    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    
    # 정상적으로 응답이 왔을 경우 텍스트 추출
    if "content" in response_data:
        ai_reply = response_data["content"][0]["text"]
    else:
        # 에러 발생 시 에러 메시지 반환
        return {"reply": f"API 에러 발생: {response_data}", "conversation_id": req.conversation_id}

    # 6. 파이어베이스에 저장할 대화 내역 갱신
    messages.append({"role": "assistant", "content": ai_reply})
    now_str = datetime.now().isoformat()
    conv_ref = db.collection("conversations")
    
    if req.conversation_id:
        conv_ref.document(req.conversation_id).update({
            "messages": messages,
            "updated_at": now_str
        })
        conv_id = req.conversation_id
    else:
        title = req.message[:15] + "..." if len(req.message) > 15 else req.message
        new_doc = conv_ref.add({
            "title": title,
            "messages": messages,
            "updated_at": now_str
        })
        conv_id = new_doc[1].id

    # 7. 프론트엔드로 반환
    return {
        "reply": ai_reply,
        "conversation_id": conv_id
    }