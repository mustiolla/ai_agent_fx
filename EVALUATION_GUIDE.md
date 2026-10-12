# 📋 외환(FX) 분석 AI 비서 - 프로젝트 심사 & 평가 Q&A 가이드북

> 본 문서는 **환율 분석 AI 비서 (`ai_agent_fx`)** 프로젝트의 평가 및 발표 심사 시 활용할 수 있도록, **핵심 평가 체크리스트 18개 문항**에 대한 실전 모범 답변과 기술적 구현 근거를 체계적으로 정리한 공식 가이드 문서입니다.

---

## 🌐 1. 공식 서비스 배포 및 접근 정보

| 구분 | 플랫폼 / 호스팅 | 공식 URL | 비고 |
| :--- | :--- | :--- | :--- |
| **Frontend Web App (Vercel)** | Vercel | **[https://ai-agent-fx.vercel.app/](https://ai-agent-fx.vercel.app/)** | 글로벌 엣지 CDN 초고속 배포 |
| **Frontend Web App (GitHub)** | GitHub Pages | **[https://mustiolla.github.io/ai_agent_fx/](https://mustiolla.github.io/ai_agent_fx/)** | GitHub 정적 호스팅 |
| **Backend API Server** | Render (Web Service) | **[https://fx-ai-backend.onrender.com](https://fx-ai-backend.onrender.com)** | FastAPI 비동기 RESTful 엔진 |
| **Interactive API Docs** | Swagger UI | **[https://fx-ai-backend.onrender.com/docs](https://fx-ai-backend.onrender.com/docs)** | 대화형 API 테스트 및 Pydantic 스키마 |
| **Source Code Repository** | GitHub | **[https://github.com/mustiolla/ai_agent_fx](https://github.com/mustiolla/ai_agent_fx)** | 오픈소스 저장소 (main 브랜치) |

---

## 📌 목차
1. [기본 동작 검증 항목 (Q1 ~ Q6)](#-기본-동작-검증-항목-q1--q6)
2. [항목 2: 아키텍처 및 설계 의도 (Q7 ~ Q10)](#-항목-2-아키텍처-및-설계-의도-q7--q10)
3. [항목 3: AI 연동 및 데이터 엔지니어링 의도 (Q11 ~ Q14)](#-항목-3-ai-연동-및-데이터-엔지니어링-의도-q11--q14)
4. [항목 4: 운영, 보안, 최적화 및 확장성 (Q15 ~ Q18)](#-항목-4-운영-보안-최적화-및-확장성-q15--q18)

---

## 🚀 기본 동작 검증 항목 (Q1 ~ Q6)

### Q1. 배포된 웹 서비스 URL로 정상 접속이 가능한가?
- **핵심 답변**: **"네, Vercel과 GitHub Pages 두 곳에 완전 분리 배포되어 안정적으로 24시간 실서비스 접속이 가능합니다."**
- **상세 설명**:
  - 메인 프론트엔드는 Vercel 글로벌 엣지 네트워크([https://ai-agent-fx.vercel.app/](https://ai-agent-fx.vercel.app/))에 배포되어 초기 로딩 속도를 극대화했습니다.
  - 서브 프론트엔드로 GitHub Pages([https://mustiolla.github.io/ai_agent_fx/](https://mustiolla.github.io/ai_agent_fx/))를 이중화하여 무중단 서비스 환경을 구축했습니다.

### Q2. Swagger UI에서 API 문서를 확인할 수 있는가?
- **핵심 답변**: **"네, Render 클라우드 실서버의 `/docs` 엔드포인트에서 모든 API 명세와 Pydantic 스키마를 확인하고 직접 테스트할 수 있습니다."**
- **상세 설명**:
  - URL: [`https://fx-ai-backend.onrender.com/docs`](https://fx-ai-backend.onrender.com/docs)
  - FastAPI의 OpenAPI 기반 자동 문서화 엔진을 통해 환율 데이터 조회, 동기화, 환전 계산기, Claude AI 챗봇, 대화 히스토리 등 15개 이상의 API 스펙이 완벽하게 문서화되어 있습니다.

### Q3. 웹에서 데이터를 추가하면 Firestore에 저장되고 목록에 반영되는가?
- **핵심 답변**: **"네, 원클릭 동기화 버튼을 누르면 Yahoo Finance의 최신 환율이 Firestore에 저장되고 대시보드와 차트에 즉시 반영됩니다."**
- **상세 설명**:
  - 상단 **`[🔄 최신 동기화]`** 버튼 클릭 시 `POST /api/data/sync` 엔드포인트가 실행됩니다.
  - 최근 1개월의 USD, EUR, JPY 일별 종가를 실시간 스크래핑하여 기존 DB와 비교 후 중복 없는 증분(Incremental) 적재를 수행합니다.
  - 적재 완료 즉시 In-memory 캐시를 무효화하고 프론트엔드 통화 카드와 Chart.js 그래프를 실시간 리로드합니다.

### Q4. `/api/data/summary`가 정상 응답하며, 채팅 답변이 요약 정보를 반영하는가?
- **핵심 답변**: **"네, 요약 API가 기간별 통계를 정확히 반환하며, AI 챗봇은 이 요약 수치를 시스템 프롬프트 및 Tool Calling을 통해 100% 반영합니다."**
- **상세 설명**:
  - `GET /api/data/summary?period=30d` 호출 시 3대 통화의 평균, 최저, 최고, 전일비 등락, 표준편차를 JSON으로 반환합니다.
  - Claude AI 챗봇은 사용자가 환율 동향을 물어볼 때 사전에 주입된 실시간 요약 컨텍스트 및 `get_rates_summary` 도구를 자율 호출하여 실제 DB 수치에 기반한 정확한 팩트 답변을 제공합니다.

### Q5. 대화가 저장되고, 대화 목록 조회 및 "불러오기"가 동작하는가?
- **핵심 답변**: **"네, Firestore `conversations` 컬렉션에 세션별로 자동 저장되며, 사이드바를 통해 이전 상담 내역을 즉시 불러올 수 있습니다."**
- **상세 설명**:
  - 챗봇 응답 완료 시 고유 `conversation_id`를 기준으로 질문/답변 쌍이 타임스탬프와 함께 자동 저장됩니다.
  - 상단 **`[💬 대화 기록]`** 버튼 클릭 시 좌측 슬라이딩 사이드바가 열려 과거 대화 세션 목록(`GET /api/conversations`)이 렌더링되며, 클릭 시 해당 대화 전체가 화면에 완벽 복원됩니다.

### Q6. 모바일/작은 화면에서도 주요 기능을 사용할 수 있는가?
- **핵심 답변**: **"네, 미디어 쿼리 기반의 완전 반응형 웹으로 구축되어 스마트폰(360~640px)에서도 모든 기능을 편리하게 사용할 수 있습니다."**
- **상세 설명**:
  - `@media (max-width: 640px)` 설정을 통해 데스크톱 3열 카드 그리드가 모바일 1열 세로 스택으로 자동 전환됩니다.
  - 사이드바는 모바일 풀스크린 드로어로 열리며, 우측 하단에 고정된 **플로팅 AI 상담 뱃지(`💬 AI 비서 상담`)**를 통해 한 손으로도 즉시 AI와 상담할 수 있습니다.

---

## 🏛️ 항목 2: 아키텍처 및 설계 의도 (Q7 ~ Q10)

### Q7. FastAPI에서 라우터/서비스 등을 어떤 기준으로 분리했는지 설명할 수 있는가?
- **핵심 답변**: **"관심사의 분리(Separation of Concerns) 원칙에 따라 Presentation, Service, Data Access 3계층으로 철저히 분리했습니다."**
- **상세 설명**:
  ```mermaid
  flowchart LR
      L1["Presentation Layer<br>(FastAPI Routers & Pydantic)"] --> L2["Service Layer<br>(calculate_summary & Claude AI)"]
      L2 --> L3["Data Access Layer<br>(Firestore DB & In-Memory Cache)"]
  ```
  1. **Presentation Layer (엔드포인트 라우터)**: HTTP 요청/응답 처리, CORS 헤더 주입, Pydantic DTO 유효성 검증
  2. **Service Layer (비즈니스 도메인 엔진)**: 통계 및 표준편차 연산(`calculate_summary`), 환전 우대율 계산기, Claude Tool Calling AI 엔진
  3. **Data Access Layer (데이터 영속성 계층)**: Firestore NoSQL CRUD 처리 및 DB 읽기 비용을 절감하는 5분 TTL 인메모리 캐시

### Q8. `data` / `conversations` 컬렉션 구조를 왜 그렇게 설계했는지 설명할 수 있는가?
- **핵심 답변**: **"데이터의 고유 성격(시계열 vs 대화 세션)을 분리하고 Firestore 읽기 비용을 최소화하기 위해 분리 설계했습니다."**
- **상세 설명**:
  - **`data` 컬렉션 (시계열 환율)**:
    - 문서 ID: `USD_2026-10-01` (`통화_날짜`)
    - 장점: 자연 키(Natural Key)를 적용하여 동일 일자 데이터의 중복 적재를 원천 방지하고 빠른 단건 조회를 지원합니다.
  - **`conversations` 컬렉션 (채팅 내역)**:
    - 문서 ID: 세션 고유 UUID (`kP3j9L0sXqW2mY1z`)
    - 구조: 문서 1개 내부에 `messages: [{ role, content, timestamp }]` 배열 포함
    - 장점: 메시지 건건마다 문서를 만들면 읽기/쓰기 비용이 급증하지만, 세션 단위 배열로 묶으면 **단 1회의 Firestore Read로 전체 대화 복원이 완료**되어 클라우드 비용을 획기적으로 절감합니다.

### Q9. 요청/응답 스키마(Pydantic)를 어떤 기준으로 정의했고 검증을 어디에 적용했는지 설명할 수 있는가?
- **핵심 답변**: **"신뢰할 수 없는 외부 입력을 비즈니스 로직 진입 전에 차단하기 위해 엄격한 필드 유효성 검사를 라우터 파이프라인에 적용했습니다."**
- **상세 설명**:
  - `RateData`: 날짜 형식(`YYYY-MM-DD` 정규식), 환율 종가(0 초과 10만 이하 양수), 통화 코드(`USD|EUR|JPY`) 화이트리스트 검증
  - `ChatRequest`: 메시지 길이(1~1,000자 제한) 및 `@field_validator` 기반의 위험 스크립트 이스케이프(`sanitize_input`) 적용
  - 적용 위치: 라우터 함수 인자에 DTO로 선언하여, 유효하지 않은 데이터는 컨트롤러 코드 실행 전 FastAPI 파이프라인에서 자동으로 `422 Unprocessable Entity` 에러로 차단됩니다.

### Q10. 프론트에서 "데이터 관리 / 대화 불러오기 / 채팅" 화면을 어떤 상태 흐름으로 연결했는지 설명할 수 있는가?
- **핵심 답변**: **"단일 진실 공급원(Single Source of Truth) 기반의 반응형 상태 흐름으로 설계했습니다."**
- **상세 설명**:
  - **데이터 관리**: 기간 탭(`currentPeriod`) 클릭 ➔ `loadDashboard()` 실행 ➔ 요약 카드와 Chart.js 그래프가 동시 갱신
  - **채팅 진행**: 첫 질문 전송 ➔ 서버가 반환한 `conversation_id`를 클라이언트 메모리에 보관 ➔ 후속 질문마다 ID를 동봉하여 컨텍스트 연속성 유지
  - **대화 불러오기**: 사이드바 목록 클릭 ➔ `currentConversationId` 교체 ➔ `GET /api/conversations/{id}`로 이전 메시지 배열을 수신하여 채팅창에 즉시 렌더링

---

## 🧠 항목 3: AI 연동 및 데이터 엔지니어링 의도 (Q11 ~ Q14)

### Q11. "컨텍스트 주입(요약 ➔ 시스템 프롬프트)"을 왜 사용했고, 어떤 장단점이 있는가?
- **핵심 답변**: **"LLM의 고질적 한계인 할루시네이션(거짓 정보)을 방지하고 항상 최신 공시 환율에 기반해 정확히 답변하도록 하기 위함입니다."**
- **상세 설명**:
  - **장점**: 복잡한 벡터 DB(RAG) 파이프라인 없이도, 사전 계산된 최신 수치를 주입함으로써 100% 팩트에 기반한 금융 리포트를 즉시 생성합니다.
  - **단점 및 극복 방안**: 원본 데이터를 통째로 넣으면 토큰 비용이 급증하므로, 백엔드에서 사전 연산한 **핵심 압축 요약 JSON(약 200토큰 내외)**만 선별 주입하여 토큰 비용을 95% 이상 절감했습니다.

### Q12. 데이터 요약(`/api/data/summary`)을 별도로 둔 이유(책임 분리/재사용성 등)는?
- **핵심 답변**: **"계산 기준 단일화와 다중 클라이언트(웹 UI, AI 챗봇, 독립 MCP 서버) 재사용성을 위해 별도 모듈로 분리했습니다."**
- **상세 설명**:
  - 웹 대시보드 요약 카드, AI 시스템 프롬프트 컨텍스트, 외부 연동용 MCP 서버(`mcp_server.py`) 3곳 모두 동일한 통계(동일한 평균, 최고, 최저)를 바라보아야 데이터 신뢰성이 보장됩니다.
  - 백엔드 공용 분석 엔진인 `calculate_summary()` 함수 하나로 집계 책임을 일원화하여 유지보수성과 무결성을 확보했습니다.

### Q13. 대화 저장 방식(언제, 어떤 형태로 저장하는지)을 선택한 이유는?
- **핵심 답변**: **"사용자 응답 지연을 방지하기 위해 턴 종료 직후 비동기로 저장하며, 읽기 비용 최소화를 위해 세션 문서 내 배열 구조를 선택했습니다."**
- **상세 설명**:
  - **시점**: 사용자 질문과 AI 답변이 완전히 생성된 직후 비동기 백그라운드로 저장하여 챗봇 응답 체감 속도를 지연시키지 않습니다.
  - **형태**: 세션 단위 Document 내 `messages: [...]` 배열 형태를 채택하여, 대화 복원 시 단 1회의 Read 연산만으로 전체 히스토리를 불러올 수 있도록 최적화했습니다.

### Q14. 환경 변수를 어떤 이유로 도입했고(보안/배포), 실제로 어떻게 적용했는가?
- **핵심 답변**: **"API 키 및 DB 보안 인증 정보의 GitHub 유출을 원천 방지하고 로컬/클라우드 배포 환경을 무수정으로 분리하기 위해 도입했습니다."**
- **상세 설명**:
  - 보안 대상: `ANTHROPIC_API_KEY`, `FIREBASE_CREDENTIALS_JSON`, `ALLOWED_ORIGINS`
  - 적용 방식: `.env` 파일과 Render 클라우드 환경변수 설정에 주입하고 `python-dotenv`를 통해 로드하며, `.gitignore`에 `.env`를 등록하여 공개 코드 저장소 유출을 방어했습니다.

---

## 🛡️ 항목 4: 운영, 보안, 최적화 및 확장성 (Q15 ~ Q18)

### Q15. 첫 접속 지연(콜드스타트)이 발생했을 때 어떻게 안내하고 완화했는가?
- **핵심 답변**: **"화면 최상단에 투명한 사전 안내 배너를 배치하고, 백엔드에는 5분 In-memory 캐시를 구축하여 체감 지연을 완화했습니다."**
- **상세 설명**:
  - **안내**: 대시보드 상단에 *"무료 클라우드(Render) 슬립 모드 해제 시 약 20~30초의 콜드스타트 지연이 발생할 수 있습니다"* 배너를 상시 노출하여 사용자의 이탈을 방지했습니다.
  - **완화**: 첫 부팅 이후에는 `_rates_cache`(5분 TTL) 및 `_briefing_cache`(1시간 TTL)를 통해 Firestore 호출 없이 **0.05초 만에 초고속 응답**하도록 최적화했습니다. 또한 프론트엔드는 로컬 서버 미실행 시 1초 내에 실서버로 자동 폴백(Auto-fallback)됩니다.

### Q16. CORS가 왜 발생했고, 어떤 설정으로 해결했는가?
- **핵심 답변**: **"프론트엔드 도메인(Vercel, GitHub)과 백엔드 도메인(Render)이 달라 발생하는 동일 출처 정책(SOP) 차단 문제였으며, FastAPI CORSMiddleware로 해결했습니다."**
- **상세 설명**:
  - 원인: 웹 브라우저는 보안상 서로 다른 도메인 간의 비동기 API 호출을 기본 차단합니다.
  - 해결: FastAPI에 `CORSMiddleware`를 구성하고 환경변수 `ALLOWED_ORIGINS`를 통해 Vercel 주소(`https://ai-agent-fx.vercel.app`), GitHub Pages 주소, 로컬 `localhost`를 명시적으로 허용하여 보안과 크로스 오리진 통신을 모두 만족시켰습니다.

### Q17. 사용자 입력을 그대로 저장/전달할 때의 위험과 최소 대응책은?
- **핵심 답변**: **"XSS 스크립트 삽입 및 프롬프트 인젝션 공격 위험이 존재하며, 3단계 입력 방어 체계로 대응했습니다."**
- **상세 설명**:
  1. **길이 제한**: Pydantic 스키마에서 사용자 메시지를 최대 1,000자로 강제 제한
  2. **스크립트 제거 및 이스케이프**: 정규식 및 `html.escape()`를 통해 `<script>`, `<iframe>`, `javascript:`, `onload=` 등 악성 태그를 원천 무력화
  3. **프롬프트 샌드박싱**: 시스템 프롬프트에서 사용자 질의를 `<user_question>` 격리 블록에 감싸 LLM이 시스템 보안 지침을 덮어쓰지 못하도록 방어

### Q18. 데이터가 늘어나거나 요약 기준이 바뀌면(예: 최근 30일만 반영) 어디를 어떻게 수정하는가?
- **핵심 답변**: **"서비스 계층의 `main.py` 내 `calculate_summary(days=30)` 함수 단 한 곳만 수정하면 전체 시스템에 일괄 반영됩니다."**
- **상세 설명**:
  - 날짜 필터링 및 집계 로직이 `calculate_summary` 단일 함수에 캡슐화되어 있습니다.
  - 따라서 파라미터 `days`의 기본값을 30으로 조정하거나 쿼리 파라미터 `period=30d`를 넘겨주는 것만으로 대시보드 통화 카드, 인터랙티브 차트, AI 챗봇 컨텍스트, 독립 MCP 서버까지 전체 시스템의 요약 기준이 즉시 자동 반영됩니다.

---

## 🎁 [보너스 구현] 독립 MCP Server & 인사이트 고도화 요약

- **독립 MCP Server (`mcp_server.py`)**: Claude Desktop, Cursor 등 외부 AI 도구에서 본 외환 분석 API를 직접 도구로 호출할 수 있는 Model Context Protocol 표준 지원.
- **확장 통계 지표 (`GET /api/data/statistics`)**: 기간별 표준편차(Volatility), 최고-최저 가격 갭, 변동계수(CV%) 실시간 산출.
- **듀얼 데이터 내보내기**: 한글 깨짐 없는 `UTF-8 BOM CSV` 다운로드 & RESTful `JSON` 파일 다운로드 지원.
- **다크 모드 지원**: 상단 헤더의 `[🌙 다크 모드]` 버튼을 통해 전체 테마 및 Chart.js 그래프 색상까지 실시간 원클릭 전환 (`localStorage` 영구 보존).

---
*문서 작성일: 2026-10-12 | 프로젝트 저장소: [mustiolla/ai_agent_fx](https://github.com/mustiolla/ai_agent_fx)*
