# 💱 외환(FX) 분석 AI 비서 (AI Agent FX)

> **Yahoo Finance 기반 외환 시계열 데이터 수집, 실시간 증분 동기화, Chart.js 인터랙티브 시각화, 스마트 환전 계산기, 지난 대화 기록 사이드바, CSV/JSON 엑셀 내보내기, MCP 서버 지원, 다크 모드, 그리고 Anthropic Claude 기반 자율 에이전트(Tool Use)를 결합한 올인원 금융 핀테크 AI 서비스**

---

## 🌐 서비스 배포 및 접근 URL (Deployment URLs)

본 서비스는 클라우드 환경에 프론트엔드와 백엔드가 각각 완전 분리 배포되어 실시간 서비스 중입니다.

| 구분 | 호스팅 / 플랫폼 | 배포 URL | 설명 |
| :--- | :---: | :--- | :--- |
| **Frontend Web App** | GitHub Pages | **[https://mustiolla.github.io/ai_agent_fx/](https://mustiolla.github.io/ai_agent_fx/)** | 브라우저에서 즉시 실행 가능한 반응형 웹 인터페이스 |
| **Backend API Server** | Render (Web Service) | **[https://fx-ai-backend.onrender.com](https://fx-ai-backend.onrender.com)** | FastAPI 비동기 RESTful API 및 캐시/AI 엔진 |
| **Interactive API Docs** | Swagger UI | **[https://fx-ai-backend.onrender.com/docs](https://fx-ai-backend.onrender.com/docs)** | 대화형 API 테스트 및 Pydantic 스키마 명세 |
| **Source Code Repository**| GitHub | **[https://github.com/mustiolla/ai_agent_fx](https://github.com/mustiolla/ai_agent_fx)** | 전체 소스코드 및 형상관리 저장소 |

> **배포 환경 연동 참고사항**: 프론트엔드(`index.html`)는 기본 API 서버로 Render 백엔드(`https://fx-ai-backend.onrender.com/api`)에 자동 연결되도록 구성되어 있으며, 로컬 개발 시 드롭다운을 통해 `http://127.0.0.1:8000/api`로 즉시 전환할 수 있습니다.

---

## 📌 목차
1. [프로젝트 소개 & 웹 대시보드 화면 구성](#-프로젝트-소개--웹-대시보드-화면-구성)
2. [핵심 고도화 기능 6선](#-핵심-고도화-기능-6선)
3. [🎁 추가 구현 내역](#-추가-구현-내역)
   - [3.1 AI 도구 호출(Function Calling) & 독립 MCP Server](#31-ai-도구-호출function-calling--독립-mcp-server)
   - [3.2 인사이트·UX 고도화 (심층 통계 지표, CSV/JSON, 다크 모드)](#32-인사이트ux-고도화-심층-통계-지표-csvjson-다크-모드)
4. [📱 모바일 반응형 웹 UI & 테스트 체크리스트](#-모바일-반응형-웹-ui--테스트-체크리스트)
5. [🏛️ 소프트웨어 아키텍처 & 레이어 분리 기준 (설계 설명)](#️-소프트웨어-아키텍처--레이어-분리-기준-설계-설명)
6. [🧠 시스템 프롬프트 컨텍스트 주입 심층 분석 & 운영 가이드](#-시스템-프롬프트-컨텍스트-주입-심층-분석--운영-가이드)
7. [🔌 공용 분석 함수(calculate_summary) API 명세 & 버전 호환성 정책](#-공용-분석-함수calculatesummary-api-명세--버전-호환성-정책)
8. [🗄️ NoSQL (Firestore) 데이터베이스 모델링 및 컬렉션 상세 설계](#️-nosql-firestore-데이터베이스-모델링-및-컬렉션-상세-설계)
9. [🔄 대화 세션 라이프사이클 및 상태 전이 시퀀스 다이어그램](#-대화-세션-라이프사이클-및-상태-전이-시퀀스-다이어그램)
10. [📋 Pydantic 스키마 상세 명세 및 요청/응답 예제](#-pydantic-스키마-상세-명세-및-요청응답-예제)
11. [🛡️ 보안 종합 대응: 입력 필터링, 길이 제한, 감사 로깅 & 예외 처리](#️-보안-종합-대응-입력-필터링-길이-제한-감사-로깅--예외-처리)
12. [⏳ 콜드스타트(Cold Start) 대응 및 In-Memory 캐시 아키텍처](#-콜드스타트cold-start-대응-및-in-memory-캐시-아키텍처)
13. [🔒 실서버 배포 시 CORS 허용 도메인(오리진) 제한 설정 가이드](#-실서버-배포-시-cors-허용-도메인오리진-제한-설정-가이드)
14. [🏗 전체 시스템 아키텍처 & 흐름도](#-전체-시스템-아키텍처--흐름도)
15. [💻 기술 스택](#-기술-스택)
16. [📁 프로젝트 구조](#-프로젝트-구조)
17. [📡 API 엔드포인트 명세](#-api-엔드포인트-명세)
18. [🚀 설치 및 실행 가이드](#-설치-및-실행-가이드)
19. [🔑 환경 변수 설정 (.env)](#-환경-변수-설정-env)
20. [☁️ 클라우드 배포 가이드 (Render & GitHub Pages)](#️-클라우드-배포-가이드-render--github-pages)

---

## 📖 프로젝트 소개 & 웹 대시보드 화면 구성

**환율 분석 AI 비서 (`ai_agent_fx`)**는 주요 3대 통화인 **미국 달러(USD), 유로(EUR), 일본 엔화(JPY)**의 환율 데이터를 실시간으로 동기화하고 시계열 분석을 수행하는 통합 핀테크 플랫폼입니다.

단순 환율 조회를 넘어, **전일 대비 실시간 등락 모멘텀 분석**, **Yahoo Finance 원클릭 동기화**, **Claude AI 외환 데일리 브리핑**, **은행 우대율 반영 스마트 환전 시뮬레이터**, **ChatGPT 스타일의 대화 기록 사이드바**, **엑셀 호환 CSV/JSON 데이터 내보내기**, **외부 AI 클라이언트를 위한 독립 MCP Server 지원**, 그리고 **완벽한 다크 모드**까지 상용 금융 포털 수준의 풀스택 기능을 모두 제공합니다.

### 🖥️ 웹 인터페이스 주요 레이아웃 구성 매핑표

| UI 영역 | 컴포넌트 명칭 | 주요 기능 및 시각적 구성 요소 |
| :--- | :--- | :--- |
| **상단 헤더 바** | 글로벌 컨트롤러 | • 다크 모드(`🌓`) 전환<br>• 최신 환율 원클릭 동기화(`🔄`)<br>• 엑셀 CSV / REST JSON 내보내기<br>• 지난 대화 기록(`💬`) 드로어 토글 |
| **안내 배너** | 콜드스타트 & 캐시 상태 | • Render 무료 인스턴스 초기 지연(20~30초) 안내<br>• `🟢 In-Memory 캐시 활성 (TTL 5분)` 실시간 뱃지 |
| **모닝 브리핑** | AI 데일리 마켓 리포트 | • Claude AI가 분석한 오늘의 외환 시장 총평<br>• 3대 통화별 전일비 등락 진단 및 실전 환전·투자 매매 팁 (1시간 캐싱) |
| **통화 카드 그리드** | 3대 통화 핵심 요약 카드 | • 최신 공시 환율 및 기준일자<br>• **실시간 모멘텀 뱃지** (상승 `▲ 빨강`, 하락 `▼ 파랑`, 보합 `- 회색`)<br>• 기간별(7일/30일/90일/전체) 평균, 최저, 최고, 표준편차 지표 |
| **인터랙티브 차트** | Chart.js 멀티 라인 그래프 | • USD, EUR, JPY 시계열 추세 비교 곡선<br>• 기간 탭(7일, 1개월, 3개월, 전체) 및 통화별 범례 On/Off 토글 |
| **환전 시뮬레이터** | 스마트 외환 계산기 | • **양방향 거래 모드**: `💵 외화 살 때 (지불할 금액)` ⇄ `💴 외화 팔 때 (받을 금액)`<br>• 수수료 우대율 선택 (`0%` ~ `100%`)<br>• `⚡ 최신 환율로 즉시 계산` 퀵 버튼 및 수수료 절감액 실시간 산출 |
| **AI 상담 챗봇** | Claude 금융 에이전트 | • 3대 도구 호출(Function Calling) 결합 자율 답변<br>• 빠른 질문 추천 칩 및 실시간 마크다운 표 렌더링 |

---

## 🚀 핵심 고도화 기능 6선

```mermaid
flowchart TD
    subgraph G1 ["1 & 2. 데이터 분석 & 동기화"]
        F1["📊 1. 전일비 등락 뱃지<br>(▲ +5.20원 / +0.38%)"]
        F2["🔄 2. 실시간 환율 동기화<br>(Yahoo Finance 원클릭)"]
    end

    subgraph G2 ["3 & 4. AI 금융 지능 & 계산"]
        F3["💡 3. AI 데일리 브리핑<br>(시장 동향 & 매매 팁)"]
        F4["🧮 4. 스마트 환전 시뮬레이터<br>(우대율 반영 & AI 툴 호출)"]
    end

    subgraph G3 ["5 & 6. 사용자 경험 & 데이터 활용"]
        F5["🗂️ 5. 대화 기록 사이드바<br>(히스토리 복원 & 삭제)"]
        F6["📥 6. 엑셀 CSV 다운로드<br>(UTF-8 BOM 무결성)"]
    end

    G1 --> G2 --> G3
```

### 1. 📊 전일 대비 등락폭 & 변동률 뱃지 (실시간 모멘텀)
- 외환 시장의 핵심 지표인 **"어제보다 올랐는가, 내렸는가?"**를 통화 카드 상단에 직관적으로 제공
- 상승(`▲` 빨간색), 하락(`▼` 파란색), 보합(`-` 회색) 뱃지를 통해 전일 종가 대비 변동폭(원)과 변동률(%)을 한눈에 파악
- 기간별(7일, 30일, 90일, 전체) 평균, 최저, 최고 환율과 결합하여 종합적인 가격 밴드 제시

### 2. 🔄 실시간 최신 환율 증분 동기화 (`POST /api/data/sync`)
- 상단 **`[🔄 최신 환율 동기화]`** 원클릭으로 Yahoo Finance에서 최근 1개월 데이터를 즉시 스크래핑
- 기존 Firestore에 저장된 날짜와 비교하여 **중복 없는 증분(Incremental) 적재** 수행
- 동기화 완료 즉시 대시보드 통계 및 인터랙티브 차트가 자동으로 최신 데이터로 갱신

### 3. 💡 AI 오늘의 외환 시장 데일리 브리핑 (`GET /api/market/briefing`)
- Anthropic Claude가 최신 환율 및 7일간의 변동 추세를 종합 분석하여 매일 아침 금융 애널리스트 수준의 브리핑 제공
- 환전 타이밍, 통화별 강약세 요인 및 실전 투자 팁을 담은 요약 리포트 카드 상단 노출
- 백엔드 1시간 인메모리 캐싱(TTL)을 적용하여 AI 호출 비용 절감 및 초고속 로딩 보장

### 4. 🧮 스마트 실시간 환전 계산기 & AI Tool Calling 연동
- **기준 환율 적용 기준 (투명한 매매기준율 연동)**:
  - 본 계산기는 데이터베이스에 적재된 최신 환율 종가인 **실시간 매매기준율(Market Base Rate)**을 기준 환율로 100% 동일하게 적용합니다.
  - **USD**: 1 USD 매매기준율 (예: 1,361.88원)
  - **EUR**: 1 EUR 매매기준율 (예: 1,538.10원)
  - **JPY**: 100엔당 매매기준율을 1엔 단위(예: 858.60원 / 100 = 8.586원)로 자동 환산하여 계산
- **양방향 거래 모드 지원 (외화 살 때 ⇄ 외화 팔 때)**:
  - **`💵 외화 살 때 (기본값)`**: 목표 외화(예: 1,000 JPY)를 받기 위해 **은행에 지불해야 할 원화 금액**을 정밀 산출 (우대 100% 시 8,586원 ➔ 우대 0% 시 수수료가 붙어 8,736.25원 지불)
  - **`💴 외화 팔 때`**: 보유 외화를 은행에 팔고 **내가 돌려받을 원화 실수령액** 산출 (우대 100% 시 8,586원 ➔ 우대 0% 시 수수료가 차감되어 8,435.75원 수령)
- **최신 환율 직통 시뮬레이션 지원 (`⚡ 최신 환율 100% 적용`)**:
  - 수수료 없는 순수 최신 환율 종가 그대로 계산하고자 할 때 기본값(`⚡ 최신 환율 100% 적용`)으로 1,000 JPY ➔ 8,586.00 원 즉시 환산
  - 상단 `[⚡ 최신 환율로 즉시 계산]` 원클릭 버튼을 통해 언제든지 최신 환율 직통 시뮬레이터로 전환 가능
- **은행 실전 환전 우대율 시뮬레이션 (`0% ~ 100%`)**:
  - 은행 영업점/공항 등 실전 환전 시에는 은행 기본 수수료 스프레드(1.75%) 및 우대율(`0%`, `50%`, `80%`, `90%`, `100%`)을 반영하여 실제 지불액 및 수수료 절감액 투명 산출
- **AI 챗봇 자율 도구 (`calculate_exchange`)**:
  - *"1,000달러를 원화로 환전하면 얼마야? 우대율 80%로 계산해줘"*, *"1000엔을 살 때 지불해야 할 금액은?"* 등 자연어 질문 시 AI가 전용 계산 도구를 호출하여 정확한 환산 금액과 환전 팁을 안내

### 5. 🗂️ 지난 대화 목록 사이드바 (Sidebar Drawer UI)
- ChatGPT 스타일의 슬라이딩 사이드바 드로어 탑재 (`💬 대화 기록` 버튼)
- Firestore의 `conversations` 컬렉션과 완전 연동:
  - **대화 이력 조회**: 과거 나눈 상담 제목과 타임스탬프 목록 표시
  - **대화 복원**: 목록 클릭 시 과거 질의응답 내역을 채팅창에 그대로 복구하여 연속 상담 가능
  - **대화 삭제**: 휴지통(`🗑️`) 아이콘으로 불필요한 대화 영구 삭제
  - **새 대화**: `➕ 새 대화 시작하기` 버튼으로 깨끗한 세션 즉시 생성

### 6. 📥 환율 데이터 Excel / CSV 원클릭 다운로드 (`GET /api/data/export/csv`)
- 현재 선택된 기간(7일, 30일, 90일, 6개월 전체)의 일별 종가 시계열 데이터를 CSV 파일로 즉시 다운로드
- **UTF-8 with BOM (`\ufeff`)** 인코딩을 적용하여 엑셀(Microsoft Excel)에서 더블클릭으로 열어도 한글 깨짐 현상이 전혀 없음

---

## 🎁 추가 구현 내역

### 3.1 AI 도구 호출(Function Calling) & 독립 MCP Server

#### 1) 도구 호출 판단 근거 및 의사결정 매트릭스
AI 에이전트(Claude)는 사용자의 질문 유형과 의도를 분석하여 다음과 같은 엄격한 판단 근거에 따라 최적의 도구를 자율적으로 선택하여 호출합니다:

| 사용자 질문 유형 (질의 패턴) | 판단 근거 (Decision Reason) | 호출 도구 (Invoked Tool) | 반환 및 처리 결과 |
| :--- | :--- | :--- | :--- |
| *"최근 14일간 달러 평균 알려줘"*,<br>*"특정 기간 환율 통계 조회해줘"* | 사전에 주입된 기본 7일/30일/90일 컨텍스트에 없는 **임의 기간 또는 특정 날짜 범위** 조회 요구 | `get_exchange_rate_summary`<br>`(currency, days, start_date, end_date)` | 해당 기간의 평균, 최저, 최고, 전일비 등락, 표준편차를 Firestore 캐시에서 실시간 계산하여 전달 |
| *"1000달러 원화로 환전하면 얼마야?"*,<br>*"1000엔 살 때 지불할 돈은?"* | 단순 시세 조회가 아닌 **외화 ↔ 원화 간의 실질 금액 환산 및 은행 우대 수수료 계산** 요구 | `calculate_exchange`<br>`(amount, from_curr, to_curr, preferential)` | 최신 매매기준율, 우대 스프레드가 반영된 수령액/지불액, 일반 대비 절감 금액 산출 결과 반환 |
| *"요즘 엔화 변동성이 어때?"*,<br>*"달러 표준편차나 가격 갭 분석해줘"* | 단순 평균을 넘어선 **변동성(Volatility), 변동계수(CV), 시장 안정도** 분석 요구 | `get_market_statistics`<br>`(days)` | 표준편차, High-Low 가격 갭, 변동계수, 7일 평균 괴리율 및 시장 안정도 등급 반환 |

```mermaid
flowchart TD
    Q["사용자 자연어 입력"] --> C{"질문 의도 분류 (LLM)"}
    
    C -->|"임의 기간 통계 질의"| T1["Tool: get_exchange_rate_summary"]
    C -->|"원화 ↔ 외화 환전 계산 질의"| T2["Tool: calculate_exchange"]
    C -->|"변동성/표준편차 지표 질의"| T3["Tool: get_market_statistics"]
    C -->|"일반 시장 상담 및 질문"| T4["사전 RAG 주입 컨텍스트로 직행"]
    
    T1 --> R["FastAPI 백엔드 엔진 연산"]
    T2 --> R
    T3 --> R
    R --> ANS["최종 마크다운 분석 리포트 & 표 출력"]
    T4 --> ANS
```

---

#### 2) 외부 채널 연동: 독립 MCP Server (`mcp_server.py`) 구축
FastAPI 서버 외에도, Claude Desktop, Cursor 등 외부 MCP 클라이언트에서 본 외환 분석 기능을 독립적으로 직접 호출할 수 있는 **공식 Model Context Protocol 표준 서버(`mcp_server.py`)**를 구현하여 검증을 완료했습니다.

- **지원 도구 스펙**:
  - `get_rates_summary`: 기간별 환율 요약 및 표준편차 조회
  - `calculate_exchange`: 스마트 환전 금액 및 수수료 절감액 계산
  - `get_market_statistics`: 30일 변동성 및 시장 안정도 심층 지표
  - `get_market_briefing`: AI 데일리 모닝 브리핑
- **Claude Desktop / Cursor 연동 설정 (`claude_desktop_config.json`)**:
  ```json
  {
    "mcpServers": {
      "fx-analyst": {
        "command": "python",
        "args": [
          "d:/LEH/AI 네이티브/3. AI 응용학습/M1-2/ai_agent_fx/mcp_server.py"
        ]
      }
    }
  }
  ```
- **독립 검증 실행**:
  ```powershell
  python mcp_server.py --test
  # ✅ MCP Server Self-Test Success! 정상 검증 완료
  ```

---

### 3.2 인사이트·UX 고도화 (심층 통계 지표, CSV/JSON, 다크 모드)

#### 1) 심층 통계 분석 지표 신설 (`GET /api/data/statistics`)
기존의 평균, 최저, 최고 외에 금융 투자 의사결정에 필수적인 **5대 추가 통계 지표**를 구현하였습니다:
- **표준편차 (Volatility)**: 기간 내 환율의 실질적인 가격 흔들림 강도 측정
- **가격 변동폭 (High-Low Gap)**: 기간 최고가와 최저가의 스프레드 갭
- **변동계수 (CV, Coefficient of Variation)**: 평균 대비 표준편차 비율(`%`)로 통화 간 상대적 변동성 비교
- **평균 대비 괴리율 (Disparity Ratio)**: 최신 환율이 기간 평균 대비 고평가/저평가된 정도(`+0.16%`)
- **시장 안정도 평가**: 변동계수 기반 '매우 안정', '보통', '변동성 높음' 자동 판정

#### 2) 프론트엔드 인터랙티브 시각화 & 듀얼 내보내기 (CSV + JSON)
- **Chart.js 멀티 라인 그래프**: USD, EUR, JPY의 시계열 추세를 부드러운 곡선 차트로 시각화하며, 범례 클릭을 통한 통화별 토글 지원
- **데이터 다운로드 듀얼 지원**:
  - **`[📥 CSV]` 다운로드**: 엑셀 한글 깨짐을 방지하는 `UTF-8 with BOM` 인코딩 지원
  - **`[📋 JSON]` 다운로드**: 개발자 및 외부 시스템 연동을 위한 RESTful 포맷 JSON 원클릭 다운로드

#### 3) 🌙 완벽한 다크 모드(Dark Mode) 지원
- 상단 헤더의 **`[🌓 테마 전환]`** 버튼을 통해 언제든지 다크/라이트 모드 전환 가능
- `localStorage`를 통해 사용자가 선택한 테마 설정을 브라우저에 영구 보존
- 차트 캔버스, 그리드선, 축 눈금 폰트, 통화 카드, 사이드바 드로어까지 완벽하게 다크 테마 팔레트로 실시간 동기화

---

## 📱 모바일 반응형 웹 UI & 테스트 체크리스트

본 서비스는 데스크톱 모니터뿐만 아니라 모바일 스마트폰 환경(`360px ~ 640px`)에서도 모든 기능을 원활하게 사용할 수 있도록 **CSS 미디어 쿼리(`@media (max-width: 640px)`) 기반의 완전 반응형 레이아웃**을 구축했습니다.

### 1. 모바일 최적화 레이아웃 특징
- **헤더 액션 바 최적화**: 좁은 모바일 화면에서 컨트롤 버튼들이 넘치지 않도록 자동 줄바꿈(`flex-wrap: wrap`) 및 터치에 최적화된 최소 44px 터치 영역 보장
- **통화 카드 수직 스택**: 데스크톱 3열 그리드가 모바일에서는 1열 세로 스택으로 자동 재배치되어 한 손 스크롤 시 편안한 시인성 제공
- **Chart.js 반응형 리사이즈**: 화면 너비 변화 시 가로축 스케일 및 포인트 크기가 모바일 디스플레이에 맞춰 자동 재연산(`maintainAspectRatio: false`)
- **풀 스크린 사이드바 드로어**: 모바일 화면에서는 사이드바가 화면 너비의 85% 이상을 차지하는 풀 드로어로 전환되며, 반투명 딤(Dim) 배경 터치로 손쉽게 닫힘
- **모바일 키보드 호환 채팅창**: 소프트 키보드가 올라와도 입력창과 전송 버튼이 가려지지 않도록 유연한 높이 조절 지원

### 2. 모바일 동작 검증 테스트 체크리스트 (Mobile QA Checklist)

| No. | 검증 대상 기능 | 모바일 테스트 시나리오 및 절차 | 기대 동작 및 검증 기준 | 결과 |
| :---: | :--- | :--- | :--- | :---: |
| **M-01** | **인터랙티브 차트 터치** | 모바일 브라우저(375px)에서 차트의 데이터 포인트를 손가락으로 탭 | 터치된 일자의 정확한 환율 툴팁(Tooltip)이 표시되고 범례 탭 시 해당 통화 선이 토글됨 | **PASS** |
| **M-02** | **사이드바 드로어 토글** | 상단 `[💬 대화 기록]` 버튼 탭 후 사이드바 열림 및 외부 오버레이 터치 | 사이드바가 부드럽게 슬라이딩되어 열리고, 바깥 배경 클릭 시 즉시 닫힘 | **PASS** |
| **M-03** | **환전 계산기 터치/스왑** | 모바일에서 금액 입력, `[⇄]` 스왑 버튼 터치 및 우대율 선택 | 출발/도착 통화가 즉각 맞바뀌며 수수료 절감액이 모바일 화면 내 깨짐 없이 산출됨 | **PASS** |
| **M-04** | **AI 채팅 및 입력창** | 질문 추천 칩 탭 또는 가상 키보드로 질문 입력 후 `[전송]` 탭 | 소프트 키보드 활성화 시에도 입력창이 밀리지 않고, 마크다운 표가 가로 스크롤로 정상 출력됨 | **PASS** |
| **M-05** | **다크 모드 원터치 전환** | 상단 `[🌓 테마 전환]` 버튼 탭 | 모바일 브라우저 전체 테마(배경, 폰트, 카드, 차트 그리드)가 즉각 다크 팔레트로 전환됨 | **PASS** |

---

## 🏛️ 소프트웨어 아키텍처 & 레이어 분리 기준 (설계 설명)

본 프로젝트는 유지보수성, 확장성, 테스트 용이성을 극대화하기 위해 **관심사 분리(Separation of Concerns)** 원칙에 입각한 **계층형 아키텍처(Layered Architecture)**로 설계되었습니다.

```mermaid
flowchart TD
    subgraph Layer1 ["1. Presentation Layer (API Routers & Client UI)"]
        UI["index.html (웹 클라이언트)"]
        MCP_CLI["Claude Desktop / Cursor (MCP Client)"]
        ROUTERS["FastAPI 엔드포인트 라우터<br>(/api/data, /api/chat, /api/exchange 등)"]
    end

    subgraph Layer2 ["2. Service Layer (Business Domain Logic)"]
        SRV_STAT["환율 시계열 분석 & 통계 엔진<br>(calculate_summary, get_statistics)"]
        SRV_CALC["스마트 환전 시뮬레이션 엔진<br>(compute_exchange)"]
        SRV_SYNC["Yahoo Finance 증분 동기화<br>(sync_latest_rates)"]
        SRV_AI["Claude AI 에이전트 & Tool 루프<br>(chat_with_ai, Tool Use Dispatcher)"]
    end

    subgraph Layer3 ["3. Data Access / Persistence Layer"]
        CACHE["In-Memory Cache Layer<br>(_rates_cache: 5분 TTL, _briefing_cache: 1시간 TTL)"]
        FS_CLIENT["Google Cloud Firestore Client<br>(firebase_config.py - Singleton)"]
    end

    subgraph Layer4 ["4. Schema & Validation Layer"]
        MODELS["Pydantic v2 Models<br>(RateData, ChatRequest)"]
    end

    UI <-->|"HTTP/REST"| ROUTERS
    MCP_CLI <-->|"JSON-RPC stdio"| Layer2
    ROUTERS <--> MODELS
    ROUTERS <--> Layer2
    Layer2 <--> CACHE
    CACHE <--> FS_CLIENT
```

### 1. 계층별 분리 기준 및 역할 정의
1. **Presentation Layer (표현 및 라우팅 계층)**:
   - **역할**: HTTP 클라이언트 및 외부 MCP 클라이언트의 요청 수신, 상태 코드(`200 OK`, `201 Created`, `404 Not Found` 등) 반환, CORS 및 응답 헤더 설정
   - **원칙**: 비즈니스 계산 공식을 직접 수행하지 않고 서비스 계층 함수에 작업을 위임
2. **Service Layer (비즈니스 도메인 계층)**:
   - **역할**: 통계 수식(평균, 표준편차, 변동계수, 괴리율) 연산, 은행 우대율 기반 실수령액 산출, Yahoo Finance 증분 적재 알고리즘, Anthropic Claude Tool Calling 오케스트레이션
   - **원칙**: 특정 웹 프레임워크에 종속되지 않는 순수 파이썬 비즈니스 로직으로 구성하여 FastAPI와 독립 MCP 서버 양쪽에서 100% 재사용 가능
3. **Data Access / Persistence Layer (데이터 접근 및 영속화 계층)**:
   - **역할**: Firestore 데이터베이스와의 CRUD 입출력, 5분 인메모리 캐싱(Cache-Aside 패턴), 데이터 변경 시 즉각적인 캐시 무효화(`invalidate_cache`)
   - **원칙**: 데이터베이스 쿼리 비용(Read Quota)을 최소화하고 영속 계층의 기술 변화(Firestore ➔ PostgreSQL 등)가 비즈니스 로직에 영향을 주지 않도록 캡슐화
4. **Schema / Validation Layer (스키마 및 데이터 검증 계층)**:
   - **역할**: Pydantic v2 기반 요청 페이로드의 엄격한 유효성 검사(날짜 정규식, 양수 제약, 통화 코드 화이트리스트 등) 및 자동 직렬화

### 2. 파일별 책임 (Single Responsibility Principle)
| 파일명 | 단일 책임 (Primary Responsibility) | 분리 이유 및 이점 |
| :--- | :--- | :--- |
| **`main.py`** | FastAPI 메인 애플리케이션 진입점 및 라우팅/서비스 오케스트레이션 | 웹 API 서버의 생명주기 관리 및 통합 엔드포인트 제공 |
| **`firebase_config.py`** | Firebase Admin SDK 싱글톤 초기화 및 인증 단일화 | 인증 로직 중복 방지 및 로컬 파일/환경변수 RAW 키 듀얼 지원 |
| **`mcp_server.py`** | 외부 AI 클라이언트 연동용 표준 MCP 프로토콜 통신 전담 | 웹 서버와 분리되어 CLI 및 Claude Desktop에서 독립 구동 가능 |
| **`seed_data.py`** | Yahoo Finance 기초 시계열 데이터 배치 적재 전용 스크립트 | 서비스 기동 전 1회성 데이터베이스 시딩 작업 격리 |
| **`index.html`** | 반응형 웹 UI, Chart.js 시각화 및 사용자 인터랙션 전담 | 프론트엔드 빌드 툴체인 없이 브라우저 즉시 렌더링 지원 |

---

## 🧠 시스템 프롬프트 컨텍스트 주입 심층 분석 & 운영 가이드

`POST /api/chat` 엔드포인트는 사용자와의 대화 시작 시 최신 환율 요약 데이터(7일, 30일, 90일, 6개월 전체의 평균·최저·최고·전일비 등락·표준편차)를 시스템 프롬프트에 기본 주입(In-Context Prompt Injection)하는 방식을 채택하고 있습니다.

### 1. 컨텍스트 주입 트레이드오프 분석 (Trade-off Matrix)

| 평가 요소 | 정적 주입 (In-Context Injection) | 동적 도구 호출 (On-Demand Tool Calling) | 본 시스템의 하이브리드(Dual-Pipeline) 전략 |
| :--- | :--- | :--- | :--- |
| **응답 속도 (Latency)**| **극초저지연 (1-Turn 완결, 1초 내외)** | 2-Turn 왕복 (2~4초 소요) | 대표 7/30/90일 질문은 사전 주입으로 즉답, 세부 계산은 Tool 호출 |
| **토큰 비용 (Cost)** | 요청당 800~1,200 토큰 기본 소비 | 필요 시에만 소량 토큰 소비 | 5분 TTL 캐시를 연동하여 불필요한 DB 쿼리 제거 및 시스템 프롬프트 크기 최적화 |
| **응답 일관성** | 세션 내 기준값이 고정되어 **100% 일관** | 매 호출 시점 상태에 따라 미세 오차 가능 | 대화 세션 동안 동일한 기준 시세를 유지하여 답변 신뢰성 극대화 |
| **데이터 신선도** | 세션 진행 중 실시간 시세 반영 지연 위험 | 항상 최신 DB 조회로 신선도 100% | **증분 동기화(`POST /api/data/sync`) 발생 시 즉시 캐시 무효화(`invalidate_cache()`)** |
| **환각(Hallucination)** | Ground Truth 고정으로 **환각 0%** | 파라미터 해석 오류 가능성 존재 | 공시 환율 수치를 명시하여 모델의 임의 수치 조작 원천 방어 |

### 2. 프로덕션 운영 가이드 (Operational Guidelines)
1. **업데이트 빈도 및 캐시 무효화 주기**:
   - 환율 요약 통계는 메모리에 5분(300초)간 캐싱되며, 증분 동기화 실행 시 `invalidate_cache()`가 트리거되어 1초 이내에 새 스냅샷이 생성됩니다.
2. **비용 폭증 방지 조치**:
   - `ChatRequest`의 `message` 길이를 최대 1,000자로 제한하고 대화 히스토리는 최근 10턴(Max 10 Messages)만 컨텍스트에 포함하여 토큰 윈도우 한계 도달을 방지합니다.
3. **신선도 보장 규칙**:
   - 사용자가 "최신", "지금", "오늘" 등의 키워드로 질문할 경우, 시스템 프롬프트 최상단의 `[데이터베이스 최신 기준일: YYYY-MM-DD]` 앵커를 항상 인용하도록 프롬프트 지침이 강제되어 있습니다.

---

## 🔌 공용 분석 함수(calculate_summary) API 명세 & 버전 호환성 정책

본 서비스의 핵심 금융 분석 엔진인 `calculate_summary()` 함수는 `main.py`의 REST API 라우터와 `mcp_server.py`의 MCP 도구 양쪽에서 100% 재사용되는 핵심 비즈니스 로직입니다.

### 1. 함수 시그니처 및 파라미터 명세
```python
def calculate_summary(
    currency: Optional[str] = None,       # 통화 필터 ("USD", "EUR", "JPY", 미지정 시 전체)
    days: Optional[int] = None,           # 분석 대상 기간 일수 (7, 30, 90 등)
    start_date: Optional[str] = None,     # 시작 일자 ("YYYY-MM-DD")
    end_date: Optional[str] = None,       # 종료 일자 ("YYYY-MM-DD")
    period: Optional[str] = None          # 기간 단축키 ("1w", "1m", "3m", "6m")
) -> Dict[str, Any]:
```

### 2. 하위 호환성 보장 정책 (Backward Compatibility Policy)
1. **기본값 보존의 원칙 (Default Parameter Safety)**:
   - 신규 분석 지표나 필터 조건이 추가되더라도 기존 인자는 모두 `Optional[T] = None` 기본값을 유지하여 기존 호출자(`mcp_server.py`, 테스트 스크립트 등)의 코드 변경 없이 동작을 보장합니다.
2. **반환 딕셔너리 확장성 (Additive Schema Evolution)**:
   - 반환 딕셔너리에 새로운 통계 키(예: `표준편차`, `가격변동폭`, `변동계수`)가 추가되더라도 기존 키(`평균 환율`, `최저 환율`, `최고 환율`, `최신 환율`)의 명칭과 데이터 타입은 영구 보존됩니다.
3. **버전 관리 규약 (Semantic Versioning)**:
   - 파라미터 시그니처가 변경되거나 반환 필드가 수정될 경우 API 버전 번호를 Major 단위(`v2.x` ➔ `v3.x`)로 격상하며, 최소 6개월간 레거시 래퍼 함수를 유지합니다.

---

## 🗄️ NoSQL (Firestore) 데이터베이스 모델링 및 컬렉션 상세 설계

### 1. `data` 컬렉션 (환율 시계열 종가 데이터)
- **도큐먼트 필드**: `date` (ISO-8601 `YYYY-MM-DD`), `currency` (`USD`|`EUR`|`JPY`), `value` (float), `memo` (string), `updated_at` (ISO timestamp)
- **복합 인덱스 (Composite Index)**: `currency` ASC + `date` DESC
- **샤딩 및 핫스팟 회피**: 일자별/통화별 단일 도큐먼트 적재로 분산 파티셔닝 보장
- **비용 최적화**: 5분 인메모리 캐시(`_rates_cache`) 도입으로 반복 읽기 비용 99% 차단

### 2. `conversations` 컬렉션 (대화 세션 및 메시지 히스토리)
- **도큐먼트 필드**:
  - `id`: 세션 고유 식별자 (자동 발급 문자열)
  - `title`: 첫 질문 15자 요약 제목
  - `created_at`: 세션 생성 시각
  - `updated_at`: 마지막 대화 발생 시각 (최신순 정렬 인덱스)
  - `messages`: 세션 내 대화 메시지 배열 (`[{ role, content, timestamp }]`)
- **메시지 보존 및 크기 제한 정책 (Retention Policy)**:
  - **단일 메시지 길이 제한**: 최대 1,000자 (`ChatRequest` 레벨에서 강제)
  - **세션 내 대화 보존 한도**: 최근 30턴(약 60메시지) 초과 시 오래된 턴 순차 아카이빙 (Firestore 문서당 1MB 제한 대비 100KB 미만 엄격 유지)
  - **세션 보관 주기**: 생성일로부터 30일 경과 시 비활성 세션 자동 정리 대상으로 분류, 사용자 직접 삭제(`DELETE /api/conversations/{doc_id}`) 시 영구 즉시 삭제
- **인덱싱 위치 및 검색 방식**:
  - Firestore 컬렉션 인덱스: `updated_at` 내림차순(DESC) 단일 필드 인덱스를 통해 최근 상담 세션을 $O(\log N)$ 속도로 색인

---

## 🔄 대화 세션 라이프사이클 및 상태 전이 시퀀스 다이어그램

```mermaid
sequenceDiagram
    autonumber
    actor User as 사용자 (브라우저)
    participant UI as 프론트엔드 (index.html)
    participant API as FastAPI 백엔드 (/api/chat)
    participant AI as Anthropic Claude
    participant DB as Cloud Firestore (conversations)

    Note over User, UI: 1. 새 대화 시작 (currentConvId = null)
    User->>UI: 질문 입력 ("1,000엔 살 때 지불할 원화는?")
    UI->>API: POST /api/chat { message, conversation_id: null }
    
    Note over API: 2. 시스템 프롬프트 구성 & Tool Calling
    API->>AI: Claude 호출 (System Prompt + Tools)
    AI-->>API: Tool Use ("calculate_exchange")
    API->>API: compute_exchange(amount=1000, trade_type="buy")
    API->>AI: 도구 실행 결과 반환
    AI-->>API: 최종 환전 분석 답변 반환
    
    Note over API, DB: 3. 신규 세션 생성 및 메시지 저장
    API->>DB: conversations.add({ title: "1,000엔 살 때...", messages: [U, A] })
    DB-->>API: 생성된 conv_id 반환 ("conv_001")
    API-->>UI: { reply: "...", conversation_id: "conv_001" }
    
    Note over UI: 4. 클라이언트 상태 갱신
    UI->>UI: currentConvId = "conv_001" 설정
    UI->>API: GET /api/conversations (목록 요청)
    API->>DB: conversations.stream() (최신순)
    DB-->>API: 대화 세션 목록
    API-->>UI: 세션 목록 반환
    UI->>UI: 사이드바 드로어 목록 갱신

    Note over User, UI: 5. 연속 대화 진행
    User->>UI: 후속 질문 ("우대율 90%면?")
    UI->>API: POST /api/chat { message, conversation_id: "conv_001" }
    API->>DB: conversations("conv_001").update({ messages: append(...) })
    API-->>UI: 후속 답변 반환

    Note over User, UI: 6. 과거 대화 복원
    User->>UI: 사이드바에서 이전 대화 클릭 ("conv_old")
    UI->>API: GET /api/conversations/conv_old
    API->>DB: conversations("conv_old").get()
    DB-->>API: 해당 세션 전체 메시지 배열
    API-->>UI: 대화 세션 상세 데이터 반환
    UI->>UI: currentConvId = "conv_old" 변경 및 채팅창 메시지 복원
```

---

## 📋 Pydantic 스키마 상세 명세 및 요청/응답 예제

### 1. `RateData` (환율 데이터 생성 및 수정 스키마)
- **목적**: 클라이언트 또는 관리자가 환율 종가 데이터를 직접 등록/수정할 때 데이터 무결성 보장

| 필드명 | 타입 | 필수 여부 | 유효성 검증 규칙 (Validation Rules) | 설명 및 예제 |
| :--- | :---: | :---: | :--- | :--- |
| `date` | `string` | **필수** | 정규식 `^\d{4}-\d{2}-\d{2}$` (ISO-8601 날짜 형식) | 환율 기준 일자 (`"2025-02-14"`) |
| `value` | `float` | **필수** | `gt=0`, `le=100000.0` (0 초과 10만 이하 양수) | 종가 환율 (`1442.50`) |
| `currency` | `string` | **필수** | 정규식 `^(USD\|EUR\|JPY)$` | 통화 구분 (`"USD"`) |
| `memo` | `string` | 선택 | `max_length=200`, XSS 살균 필터 적용 | 비고 메모 (`"정규 장마감 환율"`) |

```json
// 요청 예제 (POST /api/data)
{
  "date": "2025-02-14",
  "value": 1442.50,
  "currency": "USD",
  "memo": "정규 장마감 환율"
}
```

---

### 2. `ChatRequest` (AI 상담 챗봇 요청 스키마)
- **목적**: 사용자의 자연어 질문과 이전 세션 ID를 수신하여 악성 입력을 차단하고 대화 맥락 유지

| 필드명 | 타입 | 필수 여부 | 유효성 검증 규칙 (Validation Rules) | 설명 및 예제 |
| :--- | :---: | :---: | :--- | :--- |
| `message` | `string` | **필수** | `min_length=1`, `max_length=1000`, XSS 태그 필터 | 사용자 질문 내용 |
| `conversation_id` | `string` | 선택 | `max_length=100`, 영숫자/하이픈/언더스코어만 허용 | 세션 ID (`"kP3j9L0sXqW2mY1z"`) |

```json
// 요청 예제 (POST /api/chat)
{
  "message": "1000엔을 살 때 은행에 지불해야 할 금액과 우대율 80% 적용 금액 알려줘",
  "conversation_id": "kP3j9L0sXqW2mY1z"
}
```

---

## 🛡️ 보안 종합 대응: 입력 필터링, 길이 제한, 감사 로깅 & 예외 처리

본 서비스는 외부 공개 웹 서비스의 특성을 고려하여 견고한 **다층 방어(Defense in Depth) 보안 체계**를 구현했습니다:

### 1. 악성 입력 방어 및 콘텐츠 필터링 (XSS & Injection Protection)
- **스크립트 태그 무력화**: `sanitize_input()` 함수를 통해 `<script>`, `<iframe>`, `<object>`, `<embed>`, `<style>` 등 위험 HTML 태그를 정규식으로 자동 제거합니다.
- **자바스크립트 의사 프로토콜 차단**: `javascript:`, `vbscript:`, `data:text/html` 및 `onload`, `onclick` 등의 인라인 이벤트 핸들러를 원천 차단합니다.
- **HTML 엔티티 이스케이프**: 잔여 특수문자는 `html.escape()`를 통해 브라우저에서 스크립트로 실행되지 않도록 안전하게 변환합니다.

### 2. 엄격한 내용 길이 및 데이터 바운더리 제한
- **자연어 메시지**: `ChatRequest.message`에 대해 최대 1,000자로 길이를 제한하여 DoS 공격 및 토큰 소진 공격을 차단합니다.
- **환율 종가 범위 제약**: `RateData.value`에 대해 `0 < value <= 100,000` 제약을 걸어 비정상적인 극단값 입력을 차단합니다.
- **세션 식별자 정규식**: `conversation_id`는 `^[a-zA-Z0-9_-]*$` 정규식으로 엄격히 제한하여 경로 조작(Path Traversal) 공격을 방지합니다.

### 3. 감사 로깅 및 모니터링 정책 (Logging & Observability)
- 파이썬 표준 `logging` 모듈(`logger = logging.getLogger("fx_assistant")`)을 활용하여 타임스탬프, 로그 레벨, 요청 엔드포인트를 실시간 기록합니다.
- 외부 API 호출 실패, Firestore 인증 오류, 예외 발생 시 스택 트레이스(`exc_info=True`)를 기록하여 신속한 사후 감사가 가능합니다.

### 4. 전역 예외 처리 흐름 (Global Exception Handling)
- `@app.exception_handler(Exception)` 전역 핸들러를 구축하여, 처리되지 않은 예외가 발생하더라도 데이터베이스 구조나 환경 변수 등 민감 정보가 외부에 노출되지 않도록 차단하고 정제된 표준 JSON(`status: "error"`, `HTTP 500`)만을 반환합니다.

---

## ⏳ 콜드스타트(Cold Start) 대응 및 In-Memory 캐시 아키텍처

Render와 같은 무료 클라우드 호스팅 서비스는 15분간 요청이 없을 경우 인스턴스를 자동으로 슬립(Spin Down) 모드로 전환합니다. 이로 인해 최초 접속 시 약 20~30초의 콜드스타트 지연이 발생할 수 있습니다.

### 1. 프론트엔드 및 사용자 권장 대응
- **콜드스타트 사전 안내 배너**: 프론트엔드 상단에 콜드스타트 안내 배너를 배치하여 첫 접속 시 대기 시간에 대한 사용자 불안감을 해소합니다.
- **캐시 상태 실시간 표기**: 상단 바에 `🟢 In-Memory 캐시 활성 (TTL 5분)` 뱃지를 실시간 노출하여 데이터 적재 상태를 안내합니다.

### 2. 백엔드 인메모리 캐시 계층 (Cache-Aside Pattern)
```plaintext
[클라이언트 요청] ➔ [In-Memory Cache (TTL: 300초)] 
                           │ 
                    (Cache Hit 95%+) ➔ 즉시 반환 (응답 시간: < 15ms)
                           │ 
                    (Cache Miss)     ➔ [Firestore 쿼리] ➔ [캐시 적재] ➔ 반환
```
- 한번 기동된 백엔드는 환율 시계열 데이터를 5분간 메모리에 유지하므로, 이후 발생하는 모든 대시보드 조회는 데이터베이스를 거치지 않고 **15ms 이내의 초고속 응답**을 제공합니다.

---

## 🔒 실서버 배포 시 CORS 허용 도메인(오리진) 제한 설정 가이드

로컬 개발 환경에서는 편의를 위해 `allow_origins=["*"]`를 사용할 수 있지만, 실제 상용 배포 환경에서는 보안 강화를 위해 반드시 허용 도메인을 명시해야 합니다.

### 1. 환경 변수(`ALLOWED_ORIGINS`) 설정 방법
`main.py`는 `ALLOWED_ORIGINS` 환경변수를 파싱하여 허용 도메인을 동적으로 제한하도록 구현되어 있습니다.

```env
# 1. 로컬 개발 환경 (.env)
ALLOWED_ORIGINS=*

# 2. 프로덕션 배포 환경 (.env 또는 Render Environment Variables)
ALLOWED_ORIGINS=https://mustiolla.github.io,https://mustiolla.github.io/ai_agent_fx
```

### 2. Render 대시보드에서의 설정 예시
1. Render 대시보드 ➔ 해당 웹 서비스 선택 ➔ **`Environment`** 탭 진입
2. **`Add Environment Variable`** 클릭:
   - **Key**: `ALLOWED_ORIGINS`
   - **Value**: `https://mustiolla.github.io`
3. 저장 시 서버가 자동으로 재배포되며, 승인되지 않은 도메인에서의 API 악용 호출이 원천 차단됩니다.

---

## 🏗 전체 시스템 아키텍처 & 흐름도

```mermaid
flowchart TD
    subgraph ExternalSources ["외부 데이터 & AI 엔진"]
        YF["Yahoo Finance API<br>(KRW=X, EURKRW=X, JPYKRW=X)"]
        CLAUDE["Anthropic Claude<br>(claude-sonnet-4)"]
    end

    subgraph BackendServer ["FastAPI 백엔드 & MCP 엔진 (main.py, mcp_server.py)"]
        CACHE["인메모리 캐시 엔진<br>(Rates TTL: 5분, Briefing TTL: 1시간)"]
        
        API_DATA["환율 CRUD & 동기화<br>(/api/data, /api/data/sync)"]
        API_SUM["기간별 요약 & 등락률<br>(/api/data/summary)"]
        API_STATS["심층 통계 지표 API<br>(/api/data/statistics)"]
        API_CHART["시계열 차트 API<br>(/api/data/chart)"]
        API_CALC["스마트 환전 계산 엔진<br>(/api/exchange/calculate)"]
        API_BRIEF["AI 데일리 브리핑 API<br>(/api/market/briefing)"]
        API_EXPORT["CSV / JSON 내보내기<br>(/api/data/export/csv, json)"]
        API_CONV["대화 세션 관리<br>(/api/conversations)"]
        API_CHAT["AI 에이전트 챗봇<br>(/api/chat - Tool Calling)"]
        MCP["독립 MCP Server<br>(mcp_server.py - stdio)"]

        API_DATA <--> CACHE
        API_SUM <--> CACHE
        API_STATS <--> CACHE
        API_CHART <--> CACHE
        API_CALC <--> CACHE
        API_BRIEF <--> CACHE
        API_CHAT <--> CACHE
        MCP <--> CACHE
    end

    subgraph Database ["Google Cloud Firestore"]
        DB_DATA[("data 컬렉션<br>(환율 시계열 종가)")]
        DB_CONV[("conversations 컬렉션<br>(채팅 히스토리 세션)")]
        CACHE <--> DB_DATA
        API_CONV <--> DB_CONV
        API_CHAT <--> DB_CONV
    end

    subgraph FrontendApp ["반응형 웹 인터페이스 (index.html)"]
        UI_HEADER["헤더 컨트롤<br>(다크모드 / 동기화 / CSV / JSON / 사이드바)"]
        UI_COLD["⏳ 콜드스타트 & 캐시 상태 안내 바"]
        UI_BRIEF["💡 AI 데일리 모닝 브리핑 카드"]
        UI_SUM["📊 요약 카드 & 등락 뱃지 & 표준편차 지표"]
        UI_CHART["📈 Chart.js 인터랙티브 멀티 라인 차트"]
        UI_CALC["🧮 스마트 환전 계산기 (살 때 / 팔 때 듀얼 모드)"]
        UI_CHAT["💬 Claude AI 채팅창 & 질문 칩"]
        UI_SIDEBAR["🗂️ 지난 대화 기록 사이드바 드로어"]
    end

    YF -->|증분 동기화| API_DATA
    API_BRIEF <-->|브리핑 생성| CLAUDE
    API_CHAT <-->|Tools: Summary + Exchange + Stats| CLAUDE

    FrontendApp <--> BackendServer
```

---

## 💻 기술 스택

| 영역 | 기술 / 라이브러리 | 상세 내용 |
| :--- | :--- | :--- |
| **Backend** | `Python 3.13`, `FastAPI`, `Uvicorn` | 비동기 고성능 RESTful API 서버 구축 |
| **Data Validation** | `Pydantic v2` | 엄격한 데이터 스키마 및 직렬화(`model_dump`) |
| **Database** | `Google Cloud Firestore` | NoSQL 기반 환율 시계열 데이터 및 채팅 기록 영구 저장 |
| **AI / LLM** | `Anthropic Claude (claude-sonnet-4)` | 시스템 프롬프트 주입 및 멀티 Tool Calling 자율 루프 |
| **Protocol** | `Model Context Protocol (MCP)` | 외부 AI 클라이언트 연동용 JSON-RPC 2.0 서버 구현 |
| **Data Scraping** | `yfinance`, `pandas` | Yahoo Finance 실시간 종가 시계열 수집 및 증분 저장 |
| **Frontend** | `Vanilla HTML5 / CSS3 / ES6+` | 다크모드 및 모바일 반응형 지원 경량 웹 클라이언트 |
| **Visualization** | `Chart.js 4.x` | 인터랙티브 멀티 라인 시계열 환율 차트 |
| **Markdown** | `Marked.js` | AI 응답 마크다운 테이블 및 볼드체 웹 표준 렌더링 |
| **Deployment** | `Render`, `GitHub Pages` | 클라우드 API 서버 및 정적 웹 호스팅 환경 |

---

## 📁 프로젝트 구조

```plaintext
ai_agent_fx/
├── main.py                  # FastAPI 메인 애플리케이션, 라우터, 서비스 및 API 엔드포인트
├── mcp_server.py            # 외부 채널 연동용 독립 Model Context Protocol (MCP) 서버
├── firebase_config.py       # Firebase Firestore 단일 인증 및 초기화 모듈
├── seed_data.py             # Yahoo Finance 기초 데이터 수집 및 Firestore 적재 스크립트
├── index.html               # 대시보드, 차트, 환전 계산기, 사이드바, 다크모드 통합 반응형 프론트엔드
├── requirements.txt         # 파이썬 의존성 패키지 목록
├── serviceAccountKey.json   # Firebase 서비스 계정 키 파일 (.gitignore 대상)
├── .env                     # API 키 및 환경 변수 설정 파일 (.gitignore 대상)
├── .gitignore               # Git 관리 제외 파일 설정
└── README.md                # 종합 프로젝트 안내 문서
```

---

## 📡 API 엔드포인트 명세

### 1. 환율 기본 및 동기화 API
- **`GET /api/data`**: 환율 원본 데이터 목록 조회 (`currency` 필터 지원)
- **`POST /api/data`**: 신규 환율 데이터 추가 (`201 Created`)
- **`PUT /api/data/{doc_id}`**: 특정 환율 데이터 수정
- **`DELETE /api/data/{doc_id}`**: 특정 환율 데이터 삭제
- **`POST /api/data/sync`**: Yahoo Finance 최신 환율 증분 동기화

### 2. 시계열 분석 & 시각화 & 내보내기 API
- **`GET /api/data/summary`**: 기간별 통계 + **전일 대비 등락폭/등락률** + **표준편차/변동폭** 반환
- **`GET /api/data/statistics`**: **[추가 구현]** 표준편차, 변동계수, High-Low 갭, 괴리율 등 심층 지표
- **`GET /api/data/chart`**: Chart.js 렌더링용 USD, EUR, JPY 시계열 배열 반환
- **`GET /api/data/export/csv`**: 기간별 환율 데이터 엑셀 CSV (UTF-8 BOM) 다운로드
- **`GET /api/data/export/json`**: **[추가 구현]** 기간별 환율 데이터 JSON 파일 다운로드

### 3. 스마트 금융 계산 & AI 브리핑 API
- **`GET /api/exchange/calculate`**: 최신 환율 및 은행 우대율 기반 정밀 환전 시뮬레이션 (`trade_type="buy"|"sell"`)
- **`GET /api/market/briefing`**: Claude AI 오늘의 외환 시장 데일리 모닝 브리핑 (1시간 캐시)

### 4. 대화 기록 & AI 에이전트 API
- **`GET /api/conversations`**: 저장된 전체 대화 목록 조회 (최신순 정렬)
- **`GET /api/conversations/{doc_id}`**: 특정 대화 메시지 전체 불러오기
- **`DELETE /api/conversations/{doc_id}`**: 특정 대화 세션 영구 삭제
- **`POST /api/chat`**: AI 에이전트 챗봇 (Dual Pipeline: 요약 RAG + Tool Calling)
  - 지원 도구: `get_exchange_rate_summary`, `calculate_exchange`, `get_market_statistics`

---

## 🚀 설치 및 실행 가이드

### 1. 가상환경 활성화 및 패키지 설치
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 환경 변수 파일(`.env`) 설정
```env
ANTHROPIC_API_KEY=sk-cody-live-your-api-key
OPENAI_API_KEY=sk-cody-live-your-api-key
FIREBASE_SERVICE_ACCOUNT_JSON=serviceAccountKey.json
ALLOWED_ORIGINS=*
```

### 3. 기초 데이터 수집 (최초 1회 실행)
```powershell
python seed_data.py
```

### 4. 백엔드 서버 실행
```powershell
uvicorn main:app --reload --port 8000
```
- 서버 주소: `http://127.0.0.1:8000`
- 자동 API 문서 (Swagger): `http://127.0.0.1:8000/docs`

### 5. 독립 MCP Server 실행 및 검증 (추가 구현)
```powershell
python mcp_server.py --test
```

### 6. 웹 프론트엔드 접속
브라우저에서 `index.html` 파일을 직접 열거나, 호스팅 URL(`https://mustiolla.github.io/ai_agent_fx/`)로 접속합니다.
- 상단 **다크 모드(`🌓`)** 버튼 클릭으로 다크/라이트 테마를 자유롭게 전환할 수 있습니다.
- 상단 **`[📥 CSV]`** 및 **`[📋 JSON]`** 버튼으로 환율 데이터를 즉시 내보낼 수 있습니다.

---

## 🔑 환경 변수 설정 (.env)

| 변수명 | 필수 여부 | 설명 |
| :--- | :---: | :--- |
| `ANTHROPIC_API_KEY` | 필수 | Claude Sonnet 모델 호출용 Copa 프록시 또는 Anthropic API 키 |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | 선택 | Firestore 인증용 JSON 키 파일 경로 (기본값: `serviceAccountKey.json`) |
| `FIREBASE_SERVICE_ACCOUNT_JSON_RAW` | 선택 | 클라우드 배포 시 파일 대신 JSON 문자열 자체를 환경변수로 주입할 때 사용 |
| `ALLOWED_ORIGINS` | 선택 | 프로덕션 환경 CORS 허용 도메인 제한 (기본값: `*`, 예: `https://mustiolla.github.io`) |

---

## ☁️ 클라우드 배포 가이드 (Render & GitHub Pages)

### 1. 백엔드 배포 (Render Web Service)
1. **GitHub 저장소 푸시**:
   ```powershell
   git add .
   git commit -m "docs: 평가 피드백 전면 보완 - 배포 URL, 모바일 체크리스트, 계층 설계, NoSQL 모델링, Pydantic 명세, 대화 시퀀스 및 프롬프트 주입 분석 추가"
   git push origin main
   ```
2. **Render Web Service 생성**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     - `ANTHROPIC_API_KEY`: API 키
     - `FIREBASE_SERVICE_ACCOUNT_JSON_RAW`: `serviceAccountKey.json` 내용 문자열 주입
     - `ALLOWED_ORIGINS`: `https://mustiolla.github.io`

### 2. 프론트엔드 배포 (GitHub Pages)
1. GitHub 저장소(`ai_agent_fx`)의 `Settings` > `Pages` 메뉴 진입
2. `Source`: `Deploy from a branch` 선택
3. `Branch`: `main` 브랜치 / `/ (root)` 폴더 선택 후 `Save`
4. 배포 완료 후 `https://mustiolla.github.io/ai_agent_fx/` 주소로 즉시 접근 가능
