import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from firebase_config import get_firestore_db

# 1. 환경 변수 로드 및 Firebase 초기화
load_dotenv()
db = get_firestore_db()

# 2. In-memory 캐시 (Firestore 읽기 비용 절감 및 초고속 응답)
_rates_cache: Dict[str, Any] = {
    "data": None,
    "timestamp": 0.0,
    "ttl": 300.0  # 5분 캐시 TTL
}


def get_cached_rates() -> List[Dict[str, Any]]:
    """Firestore 환율 데이터를 5분간 캐싱하여 반복 읽기 비용을 방지합니다."""
    now = time.time()
    if _rates_cache["data"] is not None and (now - _rates_cache["timestamp"]) < _rates_cache["ttl"]:
        return _rates_cache["data"]

    docs = db.collection("data").stream()
    data_list = []
    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        data_list.append(item)

    _rates_cache["data"] = data_list
    _rates_cache["timestamp"] = now
    return data_list


def invalidate_cache():
    """데이터 추가/수정/삭제 시 캐시를 즉시 무효화합니다."""
    _rates_cache["data"] = None
    _rates_cache["timestamp"] = 0.0


# 3. FastAPI 앱 초기화
app = FastAPI(
    title="환율 AI 비서 API",
    version="2.1.0",
    description="외환(USD, JPY, EUR) 시계열 통계 및 Claude AI 기반 금융 비서 서비스"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 4. Pydantic 모델 정의 (Pydantic v2 준수)
class RateData(BaseModel):
    date: str
    value: float
    memo: Optional[str] = None
    currency: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "환율 AI 비서 백엔드 서버가 정상적으로 실행 중입니다!",
        "version": "2.1.0"
    }


# 5. 데이터 목록 조회 API (GET /api/data)
@app.get("/api/data")
def get_data(currency: Optional[str] = None):
    all_data = get_cached_rates()
    if currency:
        curr_upper = currency.upper()
        return [item for item in all_data if item.get("currency") == curr_upper]
    return all_data


# 6. 데이터 추가 API (POST /api/data)
@app.post("/api/data", status_code=201)
def add_data(data: RateData):
    doc_ref = db.collection("data").add(data.model_dump())
    invalidate_cache()
    return {"message": "데이터가 성공적으로 추가되었습니다.", "id": doc_ref[1].id}


# 7. 데이터 수정 API (PUT /api/data/{doc_id})
@app.put("/api/data/{doc_id}")
def update_data(doc_id: str, data: RateData):
    doc_ref = db.collection("data").document(doc_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="수정할 데이터를 찾을 수 없습니다.")
    doc_ref.set(data.model_dump())
    invalidate_cache()
    return {"message": f"{doc_id} 데이터가 수정되었습니다."}


# 8. 데이터 삭제 API (DELETE /api/data/{doc_id})
@app.delete("/api/data/{doc_id}")
def delete_data(doc_id: str):
    doc_ref = db.collection("data").document(doc_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="삭제할 데이터를 찾을 수 없습니다.")
    doc_ref.delete()
    invalidate_cache()
    return {"message": f"{doc_id} 데이터가 삭제되었습니다."}


# 9. 기간별 요약 통계 계산 함수 (캐시 적용)
def calculate_summary(
    currency: Optional[str] = None,
    days: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
) -> Dict[str, Any]:
    """기간 및 통화에 따른 요약 통계(평균, 최저, 최고)를 신속하게 계산합니다."""
    all_data = get_cached_rates()
    if not all_data:
        return {"summary": {}, "period": {"description": "데이터가 없습니다."}}

    all_dates = [d["date"] for d in all_data if "date" in d]
    max_db_date = max(all_dates) if all_dates else datetime.now().strftime("%Y-%m-%d")
    min_db_date = min(all_dates) if all_dates else max_db_date

    if period:
        period_lower = str(period).lower()
        if period_lower in ["1w", "7d", "week"]:
            days = 7
        elif period_lower in ["1m", "30d", "month"]:
            days = 30
        elif period_lower in ["3m", "90d", "3months"]:
            days = 90
        elif period_lower in ["6m", "180d", "all"]:
            days = None

    resolved_end_date = end_date or max_db_date
    resolved_start_date = start_date

    if days is not None and not resolved_start_date:
        try:
            ref_dt = datetime.strptime(resolved_end_date, "%Y-%m-%d")
        except ValueError:
            ref_dt = datetime.strptime(max_db_date, "%Y-%m-%d")
        start_dt = ref_dt - timedelta(days=days)
        resolved_start_date = start_dt.strftime("%Y-%m-%d")

    if currency and currency.upper() in ["USD", "JPY", "EUR"]:
        target_currencies = [currency.upper()]
    else:
        target_currencies = ["USD", "JPY", "EUR"]

    summary_stats = {
        c: {"count": 0, "sum": 0.0, "min": float("inf"), "max": 0.0}
        for c in target_currencies
    }

    for item in all_data:
        curr = item.get("currency")
        if curr not in summary_stats:
            continue

        item_date = item.get("date", "")
        if resolved_start_date and item_date < resolved_start_date:
            continue
        if resolved_end_date and item_date > resolved_end_date:
            continue

        val = float(item.get("value", 0))
        summary_stats[curr]["count"] += 1
        summary_stats[curr]["sum"] += val
        if val < summary_stats[curr]["min"]:
            summary_stats[curr]["min"] = val
        if val > summary_stats[curr]["max"]:
            summary_stats[curr]["max"] = val

    result = {}
    for curr in target_currencies:
        stats = summary_stats[curr]
        if stats["count"] > 0:
            avg = round(stats["sum"] / stats["count"], 2)
            result[curr] = {
                "데이터 개수": f"{stats['count']}개",
                "평균 환율": avg,
                "최저 환율": round(stats["min"], 2),
                "최고 환율": round(stats["max"], 2),
            }
        else:
            result[curr] = {
                "데이터 개수": "0개",
                "평균 환율": None,
                "최저 환율": None,
                "최고 환율": None,
            }

    period_desc = (
        f"{resolved_start_date} ~ {resolved_end_date} (최근 {days}일)"
        if days
        else (
            f"{resolved_start_date} ~ {resolved_end_date}"
            if resolved_start_date
            else f"전체 기간 ({min_db_date} ~ {max_db_date})"
        )
    )

    return {
        "period": {
            "days": days,
            "start_date": resolved_start_date or min_db_date,
            "end_date": resolved_end_date,
            "description": period_desc,
        },
        "summary": result,
    }


# 10. 요약 통계 API (GET /api/data/summary)
@app.get("/api/data/summary")
def get_summary(
    currency: Optional[str] = None,
    days: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
):
    return calculate_summary(
        currency=currency,
        days=days,
        start_date=start_date,
        end_date=end_date,
        period=period,
    )


# 11. 인터랙티브 차트용 시계열 데이터 API (GET /api/data/chart)
@app.get("/api/data/chart")
def get_chart_data(
    days: Optional[int] = None,
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Chart.js 시각화를 위해 날짜순으로 정렬된 USD, JPY, EUR 시계열 데이터를 제공합니다."""
    all_data = get_cached_rates()
    if not all_data:
        return {"dates": [], "series": {"USD": [], "JPY": [], "EUR": []}, "period": {"description": "데이터 없음"}}

    all_dates = sorted(list(set(d["date"] for d in all_data if "date" in d)))
    max_db_date = max(all_dates) if all_dates else datetime.now().strftime("%Y-%m-%d")
    min_db_date = min(all_dates) if all_dates else max_db_date

    if period:
        p_lower = str(period).lower()
        if p_lower in ["1w", "7d", "week"]:
            days = 7
        elif p_lower in ["1m", "30d", "month"]:
            days = 30
        elif p_lower in ["3m", "90d", "3months"]:
            days = 90
        elif p_lower in ["6m", "180d", "all"]:
            days = None

    resolved_end_date = end_date or max_db_date
    resolved_start_date = start_date

    if days is not None and not resolved_start_date:
        try:
            ref_dt = datetime.strptime(resolved_end_date, "%Y-%m-%d")
        except ValueError:
            ref_dt = datetime.strptime(max_db_date, "%Y-%m-%d")
        start_dt = ref_dt - timedelta(days=days)
        resolved_start_date = start_dt.strftime("%Y-%m-%d")

    filtered_dates = [
        d for d in all_dates
        if (not resolved_start_date or d >= resolved_start_date)
        and (not resolved_end_date or d <= resolved_end_date)
    ]

    date_map = {d: {"USD": None, "JPY": None, "EUR": None} for d in filtered_dates}
    for item in all_data:
        d = item.get("date")
        c = item.get("currency")
        v = item.get("value")
        if d in date_map and c in date_map[d]:
            date_map[d][c] = round(float(v), 2) if v is not None else None

    period_desc = (
        f"{resolved_start_date} ~ {resolved_end_date} (최근 {days}일)"
        if days
        else (
            f"{resolved_start_date} ~ {resolved_end_date}"
            if resolved_start_date
            else f"전체 기간 ({min_db_date} ~ {max_db_date})"
        )
    )

    return {
        "dates": filtered_dates,
        "series": {
            "USD": [date_map[d]["USD"] for d in filtered_dates],
            "JPY": [date_map[d]["JPY"] for d in filtered_dates],
            "EUR": [date_map[d]["EUR"] for d in filtered_dates],
        },
        "period": {
            "days": days,
            "start_date": resolved_start_date or min_db_date,
            "end_date": resolved_end_date,
            "description": period_desc,
        }
    }


# 12. 대화 목록 조회 API (GET /api/conversations)
@app.get("/api/conversations")
def get_conversations():
    docs = db.collection("conversations").stream()
    results = []
    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        results.append(item)
    results.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return results


# 13. 특정 대화 불러오기 API (GET /api/conversations/{doc_id})
@app.get("/api/conversations/{doc_id}")
def get_conversation(doc_id: str):
    doc = db.collection("conversations").document(doc_id).get()
    if doc.exists:
        return doc.to_dict()
    raise HTTPException(status_code=404, detail="해당 대화를 찾을 수 없습니다.")


# 14. 대화 삭제 API (DELETE /api/conversations/{doc_id})
@app.delete("/api/conversations/{doc_id}")
def delete_conversation(doc_id: str):
    doc_ref = db.collection("conversations").document(doc_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="삭제할 대화를 찾을 수 없습니다.")
    doc_ref.delete()
    return {"message": "대화가 성공적으로 삭제되었습니다."}


# 15. AI 챗봇 API (POST /api/chat)
@app.post("/api/chat")
def chat_with_ai(req: ChatRequest):
    # 1. 다중 기간(7일, 30일, 90일, 전체) 요약 통계 신속 산출 (캐시 활용)
    sum_7d = calculate_summary(days=7)
    sum_30d = calculate_summary(days=30)
    sum_90d = calculate_summary(days=90)
    sum_all = calculate_summary()

    system_prompt = f"""당신은 외환(FX) 시장 분석 전문 AI 비서입니다.
아래에 제공된 기간별 환율 요약 데이터 및 도구(Tools)를 기반으로 사용자의 질문에 친절하고 전문가답게 답변하세요.

[데이터베이스 최신 기준일: {sum_all['period']['end_date']}]

[최근 7일(1주일) 환율 요약] ({sum_7d['period']['description']})
- 달러(USD): {sum_7d['summary'].get('USD')}
- 엔화(JPY): {sum_7d['summary'].get('JPY')}
- 유로(EUR): {sum_7d['summary'].get('EUR')}

[최근 30일(1개월) 환율 요약] ({sum_30d['period']['description']})
- 달러(USD): {sum_30d['summary'].get('USD')}
- 엔화(JPY): {sum_30d['summary'].get('JPY')}
- 유로(EUR): {sum_30d['summary'].get('EUR')}

[최근 90일(3개월) 환율 요약] ({sum_90d['period']['description']})
- 달러(USD): {sum_90d['summary'].get('USD')}
- 엔화(JPY): {sum_90d['summary'].get('JPY')}
- 유로(EUR): {sum_90d['summary'].get('EUR')}

[전체 기간(최근 6개월) 환율 요약] ({sum_all['period']['description']})
- 달러(USD): {sum_all['summary'].get('USD')}
- 엔화(JPY): {sum_all['summary'].get('JPY')}
- 유로(EUR): {sum_all['summary'].get('EUR')}

[답변 가이드라인]
1. 사용자가 '최근 한달', '최근 1주일', '최근 3개월' 등 특정 기간을 문의하면 위 요약 데이터에서 해당 기간의 수치(평균, 최저, 최고)를 정확히 인용하세요.
2. 위 사전자료에 없는 임의의 기간(예: 최근 14일, 2026-05월 등)을 요청받으면 반드시 get_exchange_rate_summary 도구를 호출하여 조회하세요.
3. 통화별 환율 단위:
   - 달러(USD), 유로(EUR): 1단위당 원화(KRW)
   - 엔화(JPY): 100엔당 원화(KRW)
4. 답변 시 수치와 함께 변동폭, 추세 분석 및 간단한 인사이트를 덧붙여 주면 좋습니다.
"""

    tools = [
        {
            "name": "get_exchange_rate_summary",
            "description": "사용자가 요청한 특정 기간(최근 N일 또는 특정 날짜 범위)과 통화의 환율 요약(평균, 최저, 최고 환율)을 계산하여 반환합니다.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "currency": {
                        "type": "string",
                        "enum": ["USD", "JPY", "EUR", "ALL"],
                        "description": "통화 코드 (달러=USD, 엔화=JPY, 유로=EUR, 전체=ALL)",
                    },
                    "days": {
                        "type": "integer",
                        "description": "최근 N일간 기간 (예: 7, 14, 30, 45, 60, 90 등)",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "시작일 (YYYY-MM-DD 형식)",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "종료일 (YYYY-MM-DD 형식)",
                    },
                },
            },
        }
    ]

    # 슬라이딩 윈도우: 최근 10개 메시지로 컨텍스트 길이 유지
    messages = []
    if req.conversation_id:
        doc = db.collection("conversations").document(req.conversation_id).get()
        if doc.exists:
            raw_msgs = doc.to_dict().get("messages", [])
            messages.extend(raw_msgs[-10:])

    messages.append({"role": "user", "content": req.message})

    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
    url = "https://copa.codyssey.kr/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "claude-sonnet-4",
        "max_tokens": 1024,
        "system": system_prompt,
        "tools": tools,
        "messages": messages,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response_data = response.json()
    except Exception as e:
        return {
            "reply": f"AI 서비스 연결 중 오류가 발생했습니다: {str(e)}",
            "conversation_id": req.conversation_id,
        }

    # Tool Use 처리 루프
    if response_data.get("stop_reason") == "tool_use":
        assistant_content = response_data.get("content", [])
        messages.append({"role": "assistant", "content": assistant_content})

        tool_results = []
        for item in assistant_content:
            if item.get("type") == "tool_use":
                t_id = item.get("id")
                t_input = item.get("input", {})
                curr_param = t_input.get("currency")
                if curr_param == "ALL":
                    curr_param = None

                t_summary = calculate_summary(
                    currency=curr_param,
                    days=t_input.get("days"),
                    start_date=t_input.get("start_date"),
                    end_date=t_input.get("end_date"),
                )

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": t_id,
                    "content": json.dumps(t_summary, ensure_ascii=False),
                })

        messages.append({"role": "user", "content": tool_results})
        payload["messages"] = messages

        try:
            res_after_tool = requests.post(url, headers=headers, json=payload, timeout=30)
            response_data = res_after_tool.json()
        except Exception as e:
            return {
                "reply": f"도구 실행 후 답변 생성 중 오류가 발생했습니다: {str(e)}",
                "conversation_id": req.conversation_id,
            }

    ai_reply = ""
    for c in response_data.get("content", []):
        if c.get("type") == "text":
            ai_reply += c.get("text")

    if not ai_reply:
        ai_reply = f"응답을 처리할 수 없습니다: {response_data}"

    # 대화 기록 저장
    stored_messages = []
    if req.conversation_id:
        doc = db.collection("conversations").document(req.conversation_id).get()
        if doc.exists:
            stored_messages = doc.to_dict().get("messages", [])

    stored_messages.append({"role": "user", "content": req.message})
    stored_messages.append({"role": "assistant", "content": ai_reply})

    now_str = datetime.now().isoformat()
    conv_ref = db.collection("conversations")

    if req.conversation_id:
        conv_ref.document(req.conversation_id).update({
            "messages": stored_messages,
            "updated_at": now_str,
        })
        conv_id = req.conversation_id
    else:
        title = req.message[:15] + "..." if len(req.message) > 15 else req.message
        new_doc = conv_ref.add({
            "title": title,
            "messages": stored_messages,
            "updated_at": now_str,
        })
        conv_id = new_doc[1].id

    return {
        "reply": ai_reply,
        "conversation_id": conv_id,
    }