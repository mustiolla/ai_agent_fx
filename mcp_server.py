#!/usr/bin/env python
"""
Model Context Protocol (MCP) Server for Foreign Exchange (FX) Analysis
외부 클라이언트(Claude Desktop, Cursor, Custom Agents 등)에서 본 FX 백엔드 도구를 호출할 수 있도록
표준 stdio 기반 JSON-RPC 2.0 프로토콜을 구현한 독립 MCP 서버입니다.
"""

import sys
import json
import os

# 현재 디렉토리를 sys.path에 추가하여 main 모듈 로드
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import calculate_summary, compute_exchange, get_statistics, get_market_briefing


# 지원하는 MCP 도구 스키마 정의
TOOLS = [
    {
        "name": "get_rates_summary",
        "description": "달러(USD), 유로(EUR), 엔화(JPY)의 기간별(7일, 30일, 90일, 전체) 평균, 최저, 최고 환율 및 전일비 등락폭, 표준편차를 조회합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["7d", "30d", "90d", "all"],
                    "description": "조회 기간 (7d: 1주일, 30d: 1개월, 90d: 3개월, all: 전체)",
                    "default": "30d"
                },
                "currency": {
                    "type": "string",
                    "enum": ["USD", "EUR", "JPY", "ALL"],
                    "description": "특정 통화 선택 (기본: ALL)"
                }
            }
        }
    },
    {
        "name": "calculate_exchange",
        "description": "최신 환율과 은행 우대율(0%~100%)을 적용하여 원화(KRW)와 외화(USD, EUR, JPY) 간의 실질 환전 수령액과 절감 혜택을 계산합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "환전하고자 하는 금액 수치"
                },
                "from_currency": {
                    "type": "string",
                    "enum": ["KRW", "USD", "EUR", "JPY"],
                    "description": "출발 통화"
                },
                "to_currency": {
                    "type": "string",
                    "enum": ["KRW", "USD", "EUR", "JPY"],
                    "description": "도착 통화"
                },
                "preferential_rate": {
                    "type": "number",
                    "description": "수수료 우대율 (0.0: 우대없음, 0.8: 80% 우대, 0.9: 90% 우대, 1.0: 무료)",
                    "default": 0.8
                }
            },
            "required": ["amount", "from_currency", "to_currency"]
        }
    },
    {
        "name": "get_market_statistics",
        "description": "환율의 변동성(표준편차), 가격 변동폭(High-Low Gap), 변동계수(CV), 시장 안정도 등 심층 통계 분석 지표를 제공합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "분석 기간 일수 (기본 30일)",
                    "default": 30
                }
            }
        }
    },
    {
        "name": "get_market_briefing",
        "description": "외환 시장 수석 애널리스트 어조의 '오늘의 외환 시장 데일리 모닝 브리핑' 및 환전 조언을 반환합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


def handle_tool_call(name: str, arguments: dict) -> dict:
    """도구 호출 라우팅 및 결과 생성"""
    if name == "get_rates_summary":
        period = arguments.get("period", "30d")
        curr = arguments.get("currency")
        if curr == "ALL":
            curr = None
        data = calculate_summary(period=period, currency=curr)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(data, ensure_ascii=False, indent=2)
                }
            ]
        }

    elif name == "calculate_exchange":
        amt = float(arguments.get("amount", 0))
        from_c = arguments.get("from_currency", "USD")
        to_c = arguments.get("to_currency", "KRW")
        pref = float(arguments.get("preferential_rate", 0.8))
        res = compute_exchange(amount=amt, from_currency=from_c, to_currency=to_c, preferential_rate=pref)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(res, ensure_ascii=False, indent=2)
                }
            ]
        }

    elif name == "get_market_statistics":
        days = int(arguments.get("days", 30))
        stats = get_statistics(days=days)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(stats, ensure_ascii=False, indent=2)
                }
            ]
        }

    elif name == "get_market_briefing":
        briefing = get_market_briefing()
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(briefing, ensure_ascii=False, indent=2)
                }
            ]
        }

    else:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"알 수 없는 도구: {name}"}]
        }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")

    # 테스트 플래그 확인
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("=== MCP Server Standalone Test ===")
        print("1. Tools list:")
        print(json.dumps([t["name"] for t in TOOLS], indent=2))
        print("\n2. Test calculate_exchange:")
        res = handle_tool_call("calculate_exchange", {"amount": 1000, "from_currency": "USD", "to_currency": "KRW", "preferential_rate": 0.8})
        print(res["content"][0]["text"][:200])
        print("\n3. Test get_market_statistics:")
        res2 = handle_tool_call("get_market_statistics", {"days": 30})
        print(res2["content"][0]["text"][:200])
        print("\n✅ MCP Server Self-Test Success!")
        return

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except Exception as e:
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": "fx-ai-mcp",
                        "version": "1.0.0"
                    },
                    "capabilities": {
                        "tools": {}
                    }
                }
            }
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()

        elif method == "notifications/initialized":
            # 알림이므로 응답 불필요
            pass

        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": TOOLS
                }
            }
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            call_res = handle_tool_call(tool_name, tool_args)
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": call_res
            }
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()

        else:
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
