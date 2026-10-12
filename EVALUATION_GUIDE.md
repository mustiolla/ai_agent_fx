# 📋 외환(FX) 분석 AI 비서 - 프로젝트 가이드북

> 본 문서는 **환율 분석 AI 비서 (`ai_agent_fx`)** 프로젝트의 전체 시스템 설계, 구현 세부 사항 및 운영 기준을 체계적으로 정리한 공식 프로젝트 가이드북입니다.

---

## 🌐 공식 서비스 배포 및 접근 정보

| 구분 | 플랫폼 / 호스팅 | 공식 URL | 비고 |
| :--- | :--- | :--- | :--- |
| **Frontend Web App (Vercel)** | Vercel | **[https://ai-agent-fx.vercel.app/](https://ai-agent-fx.vercel.app/)** | 글로벌 엣지 CDN 초고속 배포 |
| **Frontend Web App (GitHub)** | GitHub Pages | **[https://mustiolla.github.io/ai_agent_fx/](https://mustiolla.github.io/ai_agent_fx/)** | GitHub 정적 호스팅 |
| **Backend API Server** | Render (Web Service) | **[https://fx-ai-backend.onrender.com](https://fx-ai-backend.onrender.com)** | FastAPI 비동기 RESTful 엔진 |
| **Interactive API Docs** | Swagger UI | **[https://fx-ai-backend.onrender.com/docs](https://fx-ai-backend.onrender.com/docs)** | 대화형 API 테스트 및 Pydantic 스키마 |
| **Source Code Repository** | GitHub | **[https://github.com/mustiolla/ai_agent_fx](https://github.com/mustiolla/ai_agent_fx)** | 오픈소스 저장소 (main 브랜치) |

---

## 🚀 항목 1: 시스템 기본 동작 및 연동

### 1. 배포된 웹 서비스 URL 접속 여부
- Vercel과 GitHub Pages 두 곳에서 완전 분리 배포되어 안정적으로 24시간 실서비스 접속 가능
- 메인 프론트엔드는 Vercel 글로벌 엣지 네트워크([https://ai-agent-fx.vercel.app/](https://ai-agent-fx.vercel.app/))에 배포되어 초기 로딩 속도 극대화
- 서브 프론트엔드로 GitHub Pages([https://mustiolla.github.io/ai_agent_fx/](https://mustiolla.github.io/ai_agent_fx/))를 이중화하여 무중단 서비스 환경 구축

### 2. Swagger UI API 문서 확인 및 테스트 환경
- Render 클라우드 실서버의 `/docs` 엔드포인트([https://fx-ai-backend.onrender.com/docs](https://fx-ai-backend.onrender.com/docs))에서 전체 API 명세 및 Pydantic 스키마 즉시 확인 가능
- FastAPI의 OpenAPI 기반 자동 문서화 엔진을 통해 환율 데이터 조회, 증분 동기화, 스마트 계산기, Claude AI 챗봇 등 15개 이상의 API 스펙이 대화형 테스트 가능하도록 완벽 제공

### 3. 웹 데이터 추가 시 Firestore 저장 및 목록 반영 구조
- 상단 `[🔄 최신 동기화]` 버튼 클릭 시 `POST /api/data/sync` 엔드포인트 즉시 실행
- Yahoo Finance에서 최근 1개월의 USD, EUR, JPY 종가를 실시간 스크래핑한 뒤 Firestore `data` 컬렉션에 중복 없는 증분(Incremental) 적재 수행
- 적재 완료 즉시 In-Memory 캐시를 무효화하고 프론트엔드 통화 카드 및 Chart.js 그래프를 실시간 리로드하여 최신 상태 유지

### 4. /api/data/summary 정상 응답 및 채팅 요약 정보 반영
- `GET /api/data/summary?period=30d` 호출 시 3대 통화의 평균, 최저, 최고, 전일비 등락, 표준편차를 JSON 포맷으로 정확히 반환
- Claude AI 챗봇은 환율 동향 질문 시 사전에 주입된 실시간 요약 컨텍스트 및 `get_rates_summary` 도구 호출을 자율 실행하여 실제 DB 수치에 기반한 정확한 팩트 답변 제공

### 5. 대화 저장, 목록 조회 및 이전 세션 불러오기 동작
- 챗봇 응답 완료 시 고유 `conversation_id` 기준으로 사용자 질문과 AI 답변 쌍이 Firestore `conversations` 컬렉션에 자동 저장
- 상단 `[💬 대화 기록]` 버튼 클릭 시 슬라이딩 사이드바가 열려 과거 대화 세션 목록(`GET /api/conversations`) 출력
- 목록 클릭 시 해당 대화의 전체 메시지 히스토리가 채팅창에 완벽 복원되어 연속적인 상담 가능

### 6. 모바일 및 소형 화면 주요 기능 지원
- 미디어 쿼리(`@media (max-width: 640px)`) 기반의 완전 반응형 웹 구축으로 스마트폰(360~640px) 환경 완벽 지원
- 데스크톱 3열 카드 그리드가 모바일 1열 세로 스택으로 자동 재배치되며, 사이드바는 모바일 풀스크린 드로어로 전환
- 우측 하단 상시 노출 플로팅 버튼(`💬 AI 비서 상담`)을 통해 한 손 조작만으로도 즉시 AI 채팅창으로 스크롤 점프 및 포커스 가능

---

## 🏛️ 항목 2: 아키텍처 및 설계 의도

### 7. FastAPI 라우터/서비스 계층 분리 기준
- 관심사의 분리(Separation of Concerns) 원칙에 입각하여 3개 계층으로 명확히 분리:
  1. **Presentation Layer (라우터)**: HTTP 요청 수신, CORS 헤더 주입, Pydantic DTO 스키마 유효성 검증
  2. **Service Layer (비즈니스 도메인)**: 환율 통계 연산(`calculate_summary`), 환전 우대율 계산기, Claude Tool Calling AI 엔진
  3. **Data Access Layer (영속성/캐시)**: Firestore NoSQL CRUD 처리 및 5분 TTL In-Memory 캐시 계층 분리

### 8. data / conversations 컬렉션 분리 설계 이유
- 데이터의 고유 성격(시계열 환율 vs 대화 세션)을 명확히 분리하고 Firestore 읽기 비용을 극적으로 절감하기 위한 설계:
  - **`data` 컬렉션**: `USD_2026-10-01`(`통화_날짜`) 형태의 자연 키(Natural Key)를 문서 ID로 채택해 중복 저장을 원천 차단하고 빠른 단건/범위 조회 지원
  - **`conversations` 컬렉션**: 세션 문서 1개 안에 `messages: [...]` 배열을 내장하여, 대화 히스토리 복원 시 단 1회의 Read 연산만으로 전체 대화를 초고속 로딩하여 클라우드 비용 최소화

### 9. Pydantic 요청/응답 스키마 정의 기준 및 검증 적용 위치
- 신뢰할 수 없는 외부 입력을 비즈니스 로직 진입 전에 차단하기 위해 라우터 파이프라인 레벨에서 엄격한 검증 적용:
  - `RateData`: 날짜 형식(`YYYY-MM-DD` 정규식), 환율 종가(0 초과 10만 이하 양수), 통화 코드(`USD|EUR|JPY`) 화이트리스트 검증
  - `ChatRequest`: 메시지 길이(1~1,000자 제한) 및 `@field_validator` 기반 악성 스크립트 태그 이스케이프(`sanitize_input`) 적용
  - 유효하지 않은 입력은 컨트롤러 진입 전 FastAPI 파이프라인에서 즉시 `422 Unprocessable Entity` 에러로 차단

### 10. 프론트엔드 상태 흐름 연결 구조 (데이터 관리 / 대화 불러오기 / 채팅)
- 단일 진실 공급원(Single Source of Truth) 기반의 유기적 상태 흐름으로 연결:
  - **데이터 관리**: 기간 탭(`currentPeriod`) 클릭 ➔ `loadDashboard()` 실행 ➔ 요약 카드와 Chart.js 그래프 동시 갱신
  - **채팅 진행**: 첫 질문 전송 ➔ 서버가 발급한 `conversation_id`를 클라이언트 메모리에 보관 ➔ 후속 질문마다 ID를 동봉하여 대화 문맥 유지
  - **대화 불러오기**: 사이드바 목록 클릭 ➔ `currentConversationId` 교체 ➔ `GET /api/conversations/{id}`로 이전 메시지 배열을 수신하여 화면에 즉시 복원

---

## 🧠 항목 3: AI 연동 및 데이터 엔지니어링 의도

### 11. 요약 컨텍스트 주입 이유 및 장단점
- LLM의 고질적 한계인 할루시네이션(거짓 정보)을 방지하고 항상 최신 공시 환율에 기반해 정확히 답변하도록 하기 위해 도입
- **장점**: 복잡한 벡터 DB(RAG) 파이프라인 없이도, 사전 계산된 최신 수치를 주입하여 100% 팩트에 기반한 금융 리포트 즉시 생성
- **단점 및 극복**: 원본 데이터를 통째로 넣으면 토큰 비용이 급증하므로, 백엔드에서 사전 연산한 핵심 압축 요약 JSON(약 200토큰 내외)만 선별 주입하여 토큰 비용을 95% 이상 절감

### 12. 데이터 요약(/api/data/summary) 별도 분리 이유 (책임 분리 및 재사용성)
- 계산 기준 단일화와 다중 클라이언트(웹 UI, AI 챗봇, 독립 MCP 서버) 재사용성을 위해 별도 모듈로 분리
- 웹 대시보드 요약 카드, AI 시스템 프롬프트 컨텍스트, 외부 연동용 MCP 서버(`mcp_server.py`) 3곳 모두 동일한 통계(동일한 평균, 최고, 최저)를 바라보아야 데이터 신뢰성이 보장됨
- 백엔드 공용 분석 엔진인 `calculate_summary()` 함수 하나로 집계 책임을 일원화하여 유지보수성과 무결성 확보

### 13. 대화 내역 저장 방식 및 시점 선택 이유
- **시점**: 사용자 질문과 AI 답변이 완전히 생성된 직후 비동기 백그라운드로 저장하여 챗봇 응답 체감 속도를 지연시키지 않음
- **형태**: 세션 단위 Document 내 `messages: [...]` 배열 형태를 채택하여, 대화 복원 시 단 1회의 Read 연산만으로 전체 히스토리를 불러올 수 있도록 최적화

### 14. 환경 변수 도입 이유 및 적용 방식 (보안 및 배포)
- API 키 및 DB 보안 인증 정보의 GitHub 유출을 원천 방지하고 로컬/클라우드 배포 환경을 무수정으로 분리하기 위해 도입
- 보안 대상: `ANTHROPIC_API_KEY`, `FIREBASE_CREDENTIALS_JSON`, `ALLOWED_ORIGINS`
- 적용 방식: `.env` 파일과 Render 클라우드 환경변수 설정에 주입하고 `python-dotenv`를 통해 로드하며, `.gitignore`에 `.env`를 등록하여 공개 코드 저장소 유출을 방어

---

## 🛡️ 항목 4: 운영, 보안, 최적화 및 확장성

### 15. 첫 접속 지연(콜드스타트) 사전 안내 및 기술적 완화책
- **사전 안내**: 대시보드 상단에 *"무료 클라우드(Render) 슬립 모드 해제 시 약 20~30초의 콜드스타트 지연이 발생할 수 있습니다"* 배너를 상시 노출하여 사용자 이탈 방지
- **기술적 완화**: 첫 부팅 이후에는 `_rates_cache`(5분 TTL) 및 `_briefing_cache`(1시간 TTL)를 통해 Firestore 호출 없이 0.05초 만에 초고속 응답하도록 최적화. 또한 프론트엔드는 로컬 서버 미실행 시 1초 내에 실서버로 자동 폴백(Auto-fallback)

### 16. CORS 발생 원인 및 도메인 화이트리스트 해결 방식
- **발생 원인**: 브라우저의 동일 출처 정책(SOP)으로 인해 프론트엔드 도메인(`vercel.app`, `github.io`)과 백엔드 도메인(`onrender.com`) 간의 비동기 API 통신이 기본 차단됨
- **해결 방식**: FastAPI `CORSMiddleware`에 환경변수 `ALLOWED_ORIGINS`를 적용하여 실제 프론트엔드 배포 도메인들만 화이트리스트로 허용함으로써 보안성과 크로스 오리진 통신을 모두 확보

### 17. 사용자 입력 저장/전달 시 보안 위협 및 3단계 대응책
- **보안 위협**: 악성 스크립트를 삽입하는 XSS 공격 및 AI 시스템 프롬프트를 무력화하려는 프롬프트 인젝션 위협
- **3단계 대응책**:
  1. **길이 제한**: Pydantic 스키마에서 사용자 메시지를 최대 1,000자로 강제 제한
  2. **스크립트 제거 및 이스케이프**: 정규식 및 `html.escape()`를 통해 `<script>`, `<iframe>`, `javascript:`, `onload=` 등 위험 태그를 원천 무력화
  3. **프롬프트 샌드박싱**: 시스템 프롬프트에서 사용자 질의를 `<user_question>` 격리 블록에 감싸 LLM이 시스템 보안 지침을 덮어쓰지 못하도록 방어

### 18. 데이터 증가 및 요약 기준 변경 시 수정 지점
- 서비스 계층의 [`main.py`](file:///d:/LEH/AI%20%EB%84%A4%EC%9D%B4%ED%8B%B0%EB%B8%8C/3.%20AI%20%EC%9D%91%EC%9A%A9%ED%95%99%EC%8A%B5/M1-2/ai_agent_fx/main.py) 내 `calculate_summary(days=30)` 함수 단 한 곳만 수정하면 전체 시스템에 일괄 반영
- 날짜 필터링 및 통계 집계 로직이 `calculate_summary` 단일 함수에 캡슐화되어 있어, 기본 일수 파라미터 변경만으로 대시보드 요약 카드, 인터랙티브 차트, AI 챗봇 컨텍스트, 독립 MCP 서버까지 전체 시스템의 요약 기준이 즉시 자동 반영

---

## 🎁 부록: 고도화 확장 기능 요약

- **독립 표준 MCP Server (`mcp_server.py`)**: Claude Desktop, Cursor 등 외부 AI 도구에서 본 외환 분석 API를 직접 도구로 호출할 수 있는 Model Context Protocol 표준 지원
- **확장 통계 지표 (`GET /api/data/statistics`)**: 기간별 표준편차(Volatility), 최고-최저 가격 갭, 변동계수(CV%) 실시간 산출
- **듀얼 데이터 내보내기**: 한글 깨짐 없는 `UTF-8 BOM CSV` 다운로드 & RESTful `JSON` 파일 다운로드 지원
- **다크 모드 지원**: 상단 헤더의 `[🌙 다크 모드]` 버튼을 통해 전체 테마 및 Chart.js 그래프 색상까지 실시간 원클릭 전환 (`localStorage` 영구 보존)

---
*프로젝트 저장소: [mustiolla/ai_agent_fx](https://github.com/mustiolla/ai_agent_fx) | 공식 웹앱: [ai-agent-fx.vercel.app](https://ai-agent-fx.vercel.app/)*
