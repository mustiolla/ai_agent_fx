import os
import json
import time
import math
import io
import csv
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
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

_briefing_cache: Dict[str, Any] = {
    "text": None,
    "date": None,
    "timestamp": 0.0,
    "ttl": 3600.0  # 1시간 브리핑 캐시
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
    _briefing_cache["text"] = None


# 3. FastAPI 앱 초기화
app = FastAPI(
    title="환율 AI 비서 API",
    version="2.4.0",
    description="외환(USD, EUR, JPY) 시계열 통계, 표준편차 분석, 실시간 동기화, 환전 계산기, CSV/JSON 내보내기, MCP 서버 지원 및 Claude AI 금융 에이전트 서비스"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 4. Pydantic 모델 정의
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
        "version": "2.4.0"
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


# 9. 기간별 요약 통계 계산 함수 (등락률, 표준편차 및 가격변동폭 확장)
def calculate_summary(
    currency: Optional[str] = None,
    days: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = None,
) -> Dict[str, Any]:
    """기간 및 통화에 따른 요약 통계(평균, 최저, 최고, 표준편차, 변동폭) 및 전일 대비 등락폭/등락률을 계산합니다."""
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

    if currency and currency.upper() in ["USD", "EUR", "JPY"]:
        target_currencies = [currency.upper()]
    else:
        target_currencies = ["USD", "EUR", "JPY"]

    # 전일 대비 최신 등락폭 사전 계산 (전체 시계열 기준)
    delta_info = {}
    for curr in target_currencies:
        curr_items = [d for d in all_data if d.get("currency") == curr and "date" in d and "value" in d]
        curr_items.sort(key=lambda x: x["date"])
        if len(curr_items) >= 2:
            latest = curr_items[-1]
            prev = curr_items[-2]
            l_val = float(latest["value"])
            p_val = float(prev["value"])
            diff = round(l_val - p_val, 2)
            pct = round((diff / p_val) * 100, 2) if p_val > 0 else 0.0
            direction = "up" if diff > 0 else ("down" if diff < 0 else "same")
            delta_info[curr] = {
                "latest_value": l_val,
                "latest_date": latest["date"],
                "prev_value": p_val,
                "diff": diff,
                "percent": pct,
                "direction": direction,
            }
        elif len(curr_items) == 1:
            l_val = float(curr_items[0]["value"])
            delta_info[curr] = {
                "latest_value": l_val,
                "latest_date": curr_items[0]["date"],
                "prev_value": l_val,
                "diff": 0.0,
                "percent": 0.0,
                "direction": "same",
            }
        else:
            delta_info[curr] = {
                "latest_value": None,
                "latest_date": None,
                "prev_value": None,
                "diff": 0.0,
                "percent": 0.0,
                "direction": "same",
            }

    # 선택된 기간 내의 요약 통계 계산
    summary_stats = {
        c: {"count": 0, "sum": 0.0, "min": float("inf"), "max": 0.0, "values": []}
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
        summary_stats[curr]["values"].append(val)
        if val < summary_stats[curr]["min"]:
            summary_stats[curr]["min"] = val
        if val > summary_stats[curr]["max"]:
            summary_stats[curr]["max"] = val

    result = {}
    for curr in target_currencies:
        stats = summary_stats[curr]
        d_stat = delta_info.get(curr, {})
        cnt = stats["count"]
        if cnt > 0:
            avg = round(stats["sum"] / cnt, 2)
            # 보너스 과제 지표: 표준편차, 변동폭, 변동계수(CV)
            variance = sum((v - avg) ** 2 for v in stats["values"]) / cnt
            std_dev = round(math.sqrt(variance), 2)
            price_gap = round(stats["max"] - stats["min"], 2)
            cv = round((std_dev / avg) * 100, 2) if avg > 0 else 0.0

            result[curr] = {
                "데이터 개수": f"{cnt}개",
                "평균 환율": avg,
                "최저 환율": round(stats["min"], 2),
                "최고 환율": round(stats["max"], 2),
                "최신 환율": d_stat.get("latest_value"),
                "최신 기준일": d_stat.get("latest_date"),
                "전일 환율": d_stat.get("prev_value"),
                "등락폭": d_stat.get("diff", 0.0),
                "등락률": d_stat.get("percent", 0.0),
                "등락구분": d_stat.get("direction", "same"),
                # 추가 통계 지표 (보너스 과제)
                "표준편차": std_dev,
                "가격변동폭": price_gap,
                "변동계수": f"{cv}%"
            }
        else:
            result[curr] = {
                "데이터 개수": "0개",
                "평균 환율": None,
                "최저 환율": None,
                "최고 환율": None,
                "최신 환율": d_stat.get("latest_value"),
                "최신 기준일": d_stat.get("latest_date"),
                "전일 환율": d_stat.get("prev_value"),
                "등락폭": 0.0,
                "등락률": 0.0,
                "등락구분": "same",
                "표준편차": 0.0,
                "가격변동폭": 0.0,
                "변동계수": "0.0%"
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


# 11. 심층 통계 분석 API (GET /api/data/statistics) (보너스 과제 추가 지표)
@app.get("/api/data/statistics")
def get_statistics(
    days: Optional[int] = 30,
    period: Optional[str] = None
):
    """
    환율의 변동성(표준편차), 고저 밴드 괴리율, 변동계수(CV), 시장 안정도 등 심층 통계 지표를 제공합니다.
    """
    summary_data = calculate_summary(days=days, period=period)
    sum_dict = summary_data.get("summary", {})
    stats_result = {}

    for curr, s in sum_dict.items():
        avg = s.get("평균 환율")
        std = s.get("표준편차", 0.0)
        gap = s.get("가격변동폭", 0.0)
        latest = s.get("최신 환율")

        # 7일/기간 평균 대비 괴리율
        disparity = round(((latest - avg) / avg) * 100, 2) if avg and latest else 0.0
        
        # 변동성 안정도 평가
        cv_val = float(str(s.get("변동계수", "0")).replace("%", ""))
        stability = "매우 안정" if cv_val < 1.0 else ("보통" if cv_val < 2.5 else "변동성 높음")

        stats_result[curr] = {
            "최신환율": latest,
            "평균환율": avg,
            "최저환율": s.get("최저 환율"),
            "최고환율": s.get("최고 환율"),
            "가격변동폭(Gap)": gap,
            "표준편차(Volatility)": std,
            "변동계수(CV)": f"{cv_val}%",
            "평균대비괴리율": f"{disparity:+0.2f}%",
            "시장안정도": stability
        }

    return {
        "period": summary_data.get("period"),
        "statistics": stats_result
    }


# 12. 인터랙티브 차트용 시계열 데이터 API (GET /api/data/chart)
@app.get("/api/data/chart")
def get_chart_data(
    days: Optional[int] = None,
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Chart.js 시각화를 위해 날짜순으로 정렬된 USD, EUR, JPY 시계열 데이터를 제공합니다."""
    all_data = get_cached_rates()
    if not all_data:
        return {"dates": [], "series": {"USD": [], "EUR": [], "JPY": []}, "period": {"description": "데이터 없음"}}

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

    date_map = {d: {"USD": None, "EUR": None, "JPY": None} for d in filtered_dates}
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
            "EUR": [date_map[d]["EUR"] for d in filtered_dates],
            "JPY": [date_map[d]["JPY"] for d in filtered_dates],
        },
        "period": {
            "days": days,
            "start_date": resolved_start_date or min_db_date,
            "end_date": resolved_end_date,
            "description": period_desc,
        }
    }


# 13. 최신 환율 증분 동기화 API (POST /api/data/sync)
@app.post("/api/data/sync")
def sync_latest_rates():
    """Yahoo Finance에서 최근 1개월간의 최신 환율 데이터를 수집하여 Firestore에 증분 저장합니다."""
    import yfinance as yf

    tickers = {"USD": "KRW=X", "EUR": "EURKRW=X", "JPY": "JPYKRW=X"}
    all_data = get_cached_rates()
    existing_keys = {(d.get("currency"), d.get("date")) for d in all_data}

    new_docs = []
    latest_dates = []

    for currency, ticker_symbol in tickers.items():
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="1mo")
            for date_idx, row in hist.iterrows():
                date_str = date_idx.strftime("%Y-%m-%d")
                latest_dates.append(date_str)
                if (currency, date_str) in existing_keys:
                    continue
                val = float(row["Close"])
                if currency == "JPY":
                    val = val * 100
                doc_data = {
                    "date": date_str,
                    "value": round(val, 2),
                    "currency": currency,
                    "memo": "자동 동기화",
                }
                db.collection("data").add(doc_data)
                existing_keys.add((currency, date_str))
                new_docs.append(doc_data)
        except Exception as e:
            print(f"[동기화 오류] {currency}: {e}")

    invalidate_cache()
    max_date = max(latest_dates) if latest_dates else datetime.now().strftime("%Y-%m-%d")

    return {
        "status": "success",
        "message": f"최신 환율 동기화 완료! 신규 {len(new_docs)}건의 데이터가 갱신되었습니다.",
        "new_count": len(new_docs),
        "latest_date": max_date,
    }


# 14. AI 오늘의 외환 시장 한 줄 데일리 브리핑 (GET /api/market/briefing)
@app.get("/api/market/briefing")
def get_market_briefing():
    """Claude AI를 통해 분석된 오늘의 외환 시장 핵심 동향과 환전 팁을 제공합니다 (1시간 캐시)."""
    now = time.time()
    if _briefing_cache["text"] and (now - _briefing_cache["timestamp"]) < _briefing_cache["ttl"]:
        return {
            "status": "success",
            "briefing": _briefing_cache["text"],
            "date": _briefing_cache["date"],
            "cached": True
        }

    summary_7d = calculate_summary(days=7)
    sum_data = summary_7d.get("summary", {})
    period_info = summary_7d.get("period", {})

    usd_info = sum_data.get("USD", {})
    eur_info = sum_data.get("EUR", {})
    jpy_info = sum_data.get("JPY", {})

    market_context = f"""
    - 기준일: {period_info.get('end_date')}
    - 달러(USD): 최신 {usd_info.get('최신 환율')}원 (전일비 {usd_info.get('등락폭')}원, {usd_info.get('등락률')}%, 최근 7일 평균 {usd_info.get('평균 환율')}원, 표준편차 {usd_info.get('표준편차')}원)
    - 유로(EUR): 최신 {eur_info.get('최신 환율')}원 (전일비 {eur_info.get('등락폭')}원, {eur_info.get('등락률')}%, 최근 7일 평균 {eur_info.get('평균 환율')}원, 표준편차 {eur_info.get('표준편차')}원)
    - 엔화(JPY 100엔당): 최신 {jpy_info.get('최신 환율')}원 (전일비 {jpy_info.get('등락폭')}원, {jpy_info.get('등락률')}%, 최근 7일 평균 {jpy_info.get('평균 환율')}원, 표준편차 {jpy_info.get('표준편차')}원)
    """

    prompt = f"""당신은 외환(FX) 시장 수석 애널리스트입니다.
아래의 오늘 최신 환율 및 최근 7일간의 변동 지표를 바탕으로, 투자자와 해외 환전 이용자를 위한 '오늘의 외환 시장 데일리 브리핑'을 작성하세요.

[최신 외환 지표]
{market_context}

[작성 지침]
1. 달러, 유로, 엔화의 전일 대비 등락 흐름과 7일 평균 대비 현재 수준을 종합 분석하세요.
2. 실용적인 환전 및 매수/매도 팁을 곁들여 2~3문장(약 120~180자 내외)으로 작성하세요.
3. 신뢰감 있고 친절한 전문 금융 비서 어조로 작성하며 적절한 이모지를 사용하세요.
4. 인사말이나 불필요한 설명 없이 바로 브리핑 본문만 출력하세요.
"""

    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
    url = "https://copa.codyssey.kr/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "claude-sonnet-4",
        "max_tokens": 300,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        res_data = res.json()
        briefing_text = res_data["content"][0]["text"].strip()
    except Exception as e:
        briefing_text = f"환율 시장 데이터를 분석 중입니다. (달러: {usd_info.get('최신 환율')}원, 엔화: {jpy_info.get('최신 환율')}원, 유로: {eur_info.get('최신 환율')}원)"

    _briefing_cache["text"] = briefing_text
    _briefing_cache["date"] = period_info.get("end_date")
    _briefing_cache["timestamp"] = now

    return {
        "status": "success",
        "briefing": briefing_text,
        "date": period_info.get("end_date"),
        "cached": False
    }


# 15. 통화 환전 계산 엔진 (추천 기능 4번)
def compute_exchange(
    amount: float,
    from_currency: str,
    to_currency: str,
    preferential_rate: float = 0.0  # 0.0 ~ 1.0 (예: 0.8 = 80% 우대)
) -> Dict[str, Any]:
    """
    최신 환율을 기준으로 환전 금액, 매매기준율 환산액, 우대율 적용 수수료 절감액을 계산합니다.
    """
    from_curr = from_currency.upper().strip()
    to_curr = to_currency.upper().strip()

    valid_currencies = ["KRW", "USD", "EUR", "JPY"]
    if from_curr not in valid_currencies or to_curr not in valid_currencies:
        raise ValueError(f"지원하지 않는 통화입니다. (가능 통화: {', '.join(valid_currencies)})")

    if from_curr == to_curr:
        return {
            "amount": amount,
            "from_currency": from_curr,
            "to_currency": to_curr,
            "converted_amount": amount,
            "preferential_rate": preferential_rate,
            "saved_amount": 0.0,
            "rate_date": datetime.now().strftime("%Y-%m-%d"),
            "formula": f"동일 통화 환전 (1 {from_curr} = 1 {to_curr})"
        }

    # 최신 환율 정보 획득
    summary = calculate_summary(days=7)
    rates_info = summary.get("summary", {})
    rate_date = summary.get("period", {}).get("end_date", datetime.now().strftime("%Y-%m-%d"))

    # 1단위 외화의 KRW 매매기준율 환산가 (JPY는 1엔당 기준)
    krw_per_unit = {
        "KRW": 1.0,
        "USD": float(rates_info.get("USD", {}).get("최신 환율") or 1370.0),
        "EUR": float(rates_info.get("EUR", {}).get("최신 환율") or 1520.0),
        "JPY": float(rates_info.get("JPY", {}).get("최신 환율") or 880.0) / 100.0,  # 1엔당
    }

    # 은행 기본 환전 스프레드율 (통상 1.75%)
    base_spread = 0.0175
    effective_spread = base_spread * (1.0 - min(max(preferential_rate, 0.0), 1.0))

    # 1. 출발 통화 금액을 KRW 매매기준율로 변환
    base_krw = amount * krw_per_unit[from_curr]

    # 2. 목표 통화로 변환
    if to_curr == "KRW":
        regular_krw = base_krw * (1.0 - base_spread)
        preferential_krw = base_krw * (1.0 - effective_spread)
        converted_amount = round(preferential_krw, 2)
        market_standard = round(base_krw, 2)
        saved_amount = round(preferential_krw - regular_krw, 2)
        applied_rate = round(krw_per_unit[from_curr] * (1.0 - effective_spread), 2)
        formula = f"1 {from_curr} 당 약 {applied_rate} KRW 적용 (우대율 {int(preferential_rate * 100)}%)"

    elif from_curr == "KRW":
        unit_price_regular = krw_per_unit[to_curr] * (1.0 + base_spread)
        unit_price_pref = krw_per_unit[to_curr] * (1.0 + effective_spread)
        converted_amount = round(amount / unit_price_pref, 2)
        market_standard = round(amount / krw_per_unit[to_curr], 2)
        saved_amount = round((amount / unit_price_pref) - (amount / unit_price_regular), 2)
        applied_rate = round(unit_price_pref, 2)
        formula = f"1 {to_curr} 당 약 {applied_rate} KRW 적용 (우대율 {int(preferential_rate * 100)}%)"

    else:
        market_standard = round(base_krw / krw_per_unit[to_curr], 2)
        converted_amount = round(market_standard * (1.0 - effective_spread), 2)
        saved_amount = round(market_standard * (base_spread - effective_spread), 2)
        applied_rate = round(krw_per_unit[from_curr] / krw_per_unit[to_curr], 4)
        formula = f"1 {from_curr} ≈ {applied_rate} {to_curr} (크로스 환율, 우대율 {int(preferential_rate * 100)}%)"

    return {
        "status": "success",
        "amount": amount,
        "from_currency": from_curr,
        "to_currency": to_curr,
        "preferential_rate": preferential_rate,
        "preferential_percent": f"{int(preferential_rate * 100)}%",
        "converted_amount": converted_amount,
        "market_standard_amount": market_standard,
        "saved_amount": saved_amount,
        "base_rate": round(krw_per_unit[from_curr] if to_curr == "KRW" else krw_per_unit[to_curr], 2),
        "rate_date": rate_date,
        "formula": formula
    }


# 16. 환전 계산기 API (GET /api/exchange/calculate) (추천 기능 4번)
@app.get("/api/exchange/calculate")
def get_exchange_calculation(
    amount: float,
    from_currency: str = "USD",
    to_currency: str = "KRW",
    preferential_rate: float = 0.0
):
    try:
        return compute_exchange(
            amount=amount,
            from_currency=from_currency,
            to_currency=to_currency,
            preferential_rate=preferential_rate
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# 17. 환율 데이터 CSV 내보내기 API (GET /api/data/export/csv) (추천 기능 6번)
@app.get("/api/data/export/csv")
def export_rates_csv(
    period: Optional[str] = "30d",
    currency: Optional[str] = None
):
    all_data = get_cached_rates()
    if not all_data:
        raise HTTPException(status_code=404, detail="내보낼 환율 데이터가 없습니다.")

    all_dates = sorted(list(set(d["date"] for d in all_data if "date" in d)))
    max_db_date = max(all_dates) if all_dates else datetime.now().strftime("%Y-%m-%d")

    days = None
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

    start_date = None
    if days is not None:
        try:
            ref_dt = datetime.strptime(max_db_date, "%Y-%m-%d")
        except ValueError:
            ref_dt = datetime.now()
        start_date = (ref_dt - timedelta(days=days)).strftime("%Y-%m-%d")

    filtered = []
    for item in all_data:
        curr = item.get("currency")
        d = item.get("date")
        if currency and curr != currency.upper():
            continue
        if start_date and d < start_date:
            continue
        filtered.append(item)

    curr_order = {"USD": 1, "EUR": 2, "JPY": 3}
    filtered.sort(key=lambda x: (x.get("date", ""), curr_order.get(x.get("currency", ""), 99)))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["날짜", "통화", "환율(KRW)", "기준단위", "메모"])

    unit_map = {
        "USD": "1 달러(USD)",
        "EUR": "1 유로(EUR)",
        "JPY": "100 엔(JPY)"
    }

    for row in filtered:
        c = row.get("currency", "")
        writer.writerow([
            row.get("date", ""),
            c,
            row.get("value", 0.0),
            unit_map.get(c, "1 단위"),
            row.get("memo", "수집데이터")
        ])

    csv_content = "\ufeff" + output.getvalue()
    today_str = datetime.now().strftime("%Y%m%d")
    filename = f"exchange_rates_{period or 'all'}_{today_str}.csv"

    return Response(
        content=csv_content.encode("utf-8"),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


# 18. 환율 데이터 JSON 내보내기 API (GET /api/data/export/json) (보너스 과제)
@app.get("/api/data/export/json")
def export_rates_json(
    period: Optional[str] = "30d",
    currency: Optional[str] = None
):
    """
    선택된 기간의 환율 시계열 데이터를 JSON 파일로 다운로드합니다.
    """
    all_data = get_cached_rates()
    if not all_data:
        raise HTTPException(status_code=404, detail="내보낼 데이터가 없습니다.")

    all_dates = sorted(list(set(d["date"] for d in all_data if "date" in d)))
    max_db_date = max(all_dates) if all_dates else datetime.now().strftime("%Y-%m-%d")

    days = None
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

    start_date = None
    if days is not None:
        try:
            ref_dt = datetime.strptime(max_db_date, "%Y-%m-%d")
        except ValueError:
            ref_dt = datetime.now()
        start_date = (ref_dt - timedelta(days=days)).strftime("%Y-%m-%d")

    filtered = []
    for item in all_data:
        curr = item.get("currency")
        d = item.get("date")
        if currency and curr != currency.upper():
            continue
        if start_date and d < start_date:
            continue
        filtered.append({
            "date": d,
            "currency": curr,
            "value": item.get("value"),
            "memo": item.get("memo", "수집데이터")
        })

    filtered.sort(key=lambda x: (x["date"], x["currency"]))
    today_str = datetime.now().strftime("%Y%m%d")
    filename = f"exchange_rates_{period or 'all'}_{today_str}.json"
    json_bytes = json.dumps(filtered, ensure_ascii=False, indent=2).encode("utf-8")

    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


# 19. 대화 목록 조회 API (GET /api/conversations) (추천 기능 5번 연동)
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


# 20. 특정 대화 불러오기 API (GET /api/conversations/{doc_id}) (추천 기능 5번 연동)
@app.get("/api/conversations/{doc_id}")
def get_conversation(doc_id: str):
    doc = db.collection("conversations").document(doc_id).get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    raise HTTPException(status_code=404, detail="해당 대화를 찾을 수 없습니다.")


# 21. 대화 삭제 API (DELETE /api/conversations/{doc_id}) (추천 기능 5번 연동)
@app.delete("/api/conversations/{doc_id}")
def delete_conversation(doc_id: str):
    doc_ref = db.collection("conversations").document(doc_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="삭제할 대화를 찾을 수 없습니다.")
    doc_ref.delete()
    return {"message": "대화가 성공적으로 삭제되었습니다."}


# 22. AI 챗봇 API (POST /api/chat) - 멀티 도구 호출(Tool Calling) 연동
@app.post("/api/chat")
def chat_with_ai(req: ChatRequest):
    sum_7d = calculate_summary(days=7)
    sum_30d = calculate_summary(days=30)
    sum_90d = calculate_summary(days=90)
    sum_all = calculate_summary()

    system_prompt = f"""당신은 외환(FX) 시장 분석 및 환전 상담 전문 AI 수석 비서입니다.
아래에 제공된 기간별 환율 요약 데이터 및 도구(Tools)를 기반으로 사용자의 질문에 친절하고 전문가답게 답변하세요.

[데이터베이스 최신 기준일: {sum_all['period']['end_date']}]

[최근 7일(1주일) 환율 요약] ({sum_7d['period']['description']})
- 달러(USD): {sum_7d['summary'].get('USD')}
- 유로(EUR): {sum_7d['summary'].get('EUR')}
- 엔화(JPY): {sum_7d['summary'].get('JPY')}

[최근 30일(1개월) 환율 요약] ({sum_30d['period']['description']})
- 달러(USD): {sum_30d['summary'].get('USD')}
- 유로(EUR): {sum_30d['summary'].get('EUR')}
- 엔화(JPY): {sum_30d['summary'].get('JPY')}

[최근 90일(3개월) 환율 요약] ({sum_90d['period']['description']})
- 달러(USD): {sum_90d['summary'].get('USD')}
- 유로(EUR): {sum_90d['summary'].get('EUR')}
- 엔화(JPY): {sum_90d['summary'].get('JPY')}

[전체 기간(최근 6개월) 환율 요약] ({sum_all['period']['description']})
- 달러(USD): {sum_all['summary'].get('USD')}
- 유로(EUR): {sum_all['summary'].get('EUR')}
- 엔화(JPY): {sum_all['summary'].get('JPY')}

[답변 가이드라인]
1. 사용자가 '최근 한달', '최근 1주일', '최근 3개월' 등 특정 기간을 문의하면 위 요약 데이터에서 해당 기간의 수치(평균, 최저, 최고, 전일대비 등락, 표준편차)를 정확히 인용하세요.
2. 위 사전자료에 없는 임의의 기간(예: 최근 14일, 특정 월 등)을 요청받으면 반드시 get_exchange_rate_summary 도구를 호출하여 조회하세요.
3. 사용자가 "100만원 환전하면 엔화로 얼마야?", "500달러를 원화로 바꾸면?" 등 환전 계산을 문의할 경우 반드시 calculate_exchange 도구를 호출하여 정확한 환산 금액과 우대 팁을 안내하세요.
4. 사용자가 "변동성이 어떤가요?", "표준편차나 가격 갭을 분석해줘" 등 심층 통계를 문의하면 get_market_statistics 도구를 호출하세요.
5. 통화별 환율 단위:
   - 달러(USD), 유로(EUR): 1단위당 원화(KRW)
   - 엔화(JPY): 100엔당 원화(KRW)
6. 답변 시 마크다운 표, 글머리 기호, 이모지를 적절히 활용하여 가독성 높게 작성하세요.
"""

    tools = [
        {
            "name": "get_exchange_rate_summary",
            "description": "사용자가 요청한 특정 기간(최근 N일 또는 특정 날짜 범위)과 통화의 환율 요약(평균, 최저, 최고 환율, 표준편차)을 계산하여 반환합니다.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "currency": {
                        "type": "string",
                        "enum": ["USD", "EUR", "JPY", "ALL"],
                        "description": "통화 코드 (달러=USD, 유로=EUR, 엔화=JPY, 전체=ALL)",
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
        },
        {
            "name": "calculate_exchange",
            "description": "원화(KRW)와 외화(USD, EUR, JPY) 간의 최신 환율 기준 환전 금액 및 우대 수수료를 정밀하게 계산합니다.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "환전하고자 하는 금액 수치 (예: 1000, 1000000)"
                    },
                    "from_currency": {
                        "type": "string",
                        "enum": ["KRW", "USD", "EUR", "JPY"],
                        "description": "출발 통화"
                    },
                    "to_currency": {
                        "type": "string",
                        "enum": ["KRW", "USD", "EUR", "JPY"],
                        "description": "도착(환전받을) 통화"
                    },
                    "preferential_rate": {
                        "type": "number",
                        "description": "환전 수수료 우대율 (0.0 ~ 1.0 사이, 미지정시 0.0, 예: 80% 우대시 0.8)",
                        "default": 0.0
                    }
                },
                "required": ["amount", "from_currency", "to_currency"]
            }
        },
        {
            "name": "get_market_statistics",
            "description": "최근 기간 동안의 환율 변동성(표준편차), 가격 변동폭(Gap), 변동계수(CV), 시장 안정도 등 심층 금융 통계 지표를 반환합니다.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "분석 기간 일수 (기본값: 30)"
                    }
                }
            }
        }
    ]

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
                t_name = item.get("name")
                t_input = item.get("input", {})

                if t_name == "calculate_exchange":
                    res_calc = compute_exchange(
                        amount=float(t_input.get("amount", 0)),
                        from_currency=t_input.get("from_currency", "USD"),
                        to_currency=t_input.get("to_currency", "KRW"),
                        preferential_rate=float(t_input.get("preferential_rate", 0.0))
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": t_id,
                        "content": json.dumps(res_calc, ensure_ascii=False)
                    })

                elif t_name == "get_exchange_rate_summary":
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

                elif t_name == "get_market_statistics":
                    t_days = int(t_input.get("days", 30))
                    t_stats = get_statistics(days=t_days)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": t_id,
                        "content": json.dumps(t_stats, ensure_ascii=False),
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