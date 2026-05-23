# OWP-Simulator — Offshore KRW Clearing SWIFT MT Simulator

**SWIFT MT message simulator for offshore Korean Won (KRW) clearing via Bank of Korea (BOK).** Implements MT103/MT202/MT900/MT910/MT940/MT950 parsing, generation, validation, and end-to-end payment flow simulation.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-219%20passing-brightgreen)]()

---

## 개요

이 프로젝트는 **역외원화결제(Offshore KRW Clearing)** 를 SWIFT MT 메시지 레벨에서 학습하기 위한 시뮬레이터입니다. 한국은행(BOK) 연동을 전제로 한 실제 업무 프로세스를 모사하며, MT 전문의 파싱/생성/검증부터 결제 플로우 orchestration까지 전 과정을 구현합니다.

## 기술 스택

| 영역 | 기술 |
|------|------|
| 언어 | Python 3.11+ |
| 웹 서버 | FastAPI (BOK 모의 게이트웨이) |
| 대시보드 | Streamlit |
| DB | SQLite (로컬 실습) |
| 테스트 | pytest (219 tests) |
| 패키징 | uv + pyproject.toml |

---

## 프로젝트 구조

```
OWP-Simulator/
├── src/
│   ├── parser/              # SWIFT MT 메시지 파서
│   │   ├── block_parser.py  # Block 1~5 구조 파싱
│   │   ├── tag_parser.py    # :20:, :32A: 등 태그 추출
│   │   ├── bic_validator.py # BIC 코드 검증/분해
│   │   └── field_validator.py # 필드 값 검증
│   ├── builder/             # MT 전문 생성기
│   │   ├── mt103_builder.py # 송금 전문 (Customer Credit Transfer)
│   │   ├── mt202_builder.py # 은행간 자금이체 (Cover Payment)
│   │   └── mt9xx_builder.py # MT900/910/940/950 확인/응답
│   ├── validator/           # 메시지 검증 엔진
│   │   └── swift_validator.py
│   ├── flow/                # 결제 플로우
│   │   ├── payment_flow.py  # 오케스트레이터 (수신→통보→정산)
│   │   ├── status_machine.py# 상태 머신 (RECEIVED→...→SETTLED)
│   │   └── exchange_processor.py # 환율 변환
│   ├── bok_simulator/       # 한국은행 모의 서버 (FastAPI)
│   │   ├── app.py           # REST API 엔드포인트
│   │   ├── handlers.py      # MT 수신/응답 핸들러
│   │   └── scenarios.py     # 7가지 예외 시나리오
│   ├── audit/               # 감사 로깅 (SHA-256)
│   │   └── logger.py
│   ├── cutoff/              # 마감시간 관리
│   │   └── manager.py
│   └── dashboard/           # 모니터링 대시보드 (Streamlit)
│       └── app.py
├── tests/
│   ├── unit/                # 단위 테스트 (parser, builder, validator)
│   ├── integration/         # 통합 테스트 (flow, exchange, audit)
│   └── scenarios/           # E2E 시나리오 (TC-001~003)
├── doc/                     # 상세 문서
└── pyproject.toml           # 패키지 설정
```

---

## 주요 기능

### SWIFT MT 메시지 처리

| 메시지 | 설명 | 역할 |
|--------|------|------|
| **MT103** | Customer Credit Transfer | 송금 전문 (파싱/생성/검증) |
| **MT202** | Cover Payment | 은행간 자금이체 |
| **MT900** | Debit Note | 차변 확인 응답 |
| **MT910** | Credit Note | 대변 확인 통보 |
| **MT940/950** | Statement | 잔액 보고 |

### 결제 플로우

```
해외거래은행          우리은행              한국은행(BOK)
    │                    │                    │
    │──MT103 송금────────>│                    │
    │                    │──MT103 통보────────>│
    │                    │                    │
    │                    │<─MT900 확인─────────│
    │<─MT910 수신확인─────│                    │
    │                    │──MT202 자금이체────>│
    │                    │                    │
    │                    │<─MT950 잔액보고──────│
```

### 상태 머신

```
RECEIVED → VALIDATED → PROCESSING → PENDING_BOK → SETTLED
    |          |            |             |
    v          v            v             v
  ERROR → REPAIR → VALIDATED (재처리)
```

### 예외 시나리오 (7종)

| 시나리오 | 설명 | 처리 |
|----------|------|------|
| DUPLICATE_REF | 참조번호 중복 | ACK299 |
| INVALID_BIC | 잘못된 BIC | NAK199 + Repair |
| AMOUNT_MISMATCH | 금액 불일치 | Escalation |
| CUTOFF_EXCEEDED | 마감 초과 | 익일 Valor |
| INVALID_KRW_FORMAT | 원화 형식 오류 | Repair |
| BOK_TIMEOUT | BOK 타임아웃 | 재시도 |
| NOSTRO_INSUFFICIENT | 잔액 부족 | 한도 알림 |

---

## 설치 및 실행

```bash
# 저장소 클론
git clone https://github.com/topslee-dev/offshore-krw-clearing.git
cd offshore-krw-clearing

# 가상환경 생성 및 패키지 설치
uv venv
uv pip install -e .
uv pip install fastapi uvicorn streamlit pytest

# 전체 테스트 실행
uv run pytest tests/ -v

# BOK 모의 서버 실행
uv run uvicorn src.bok_simulator.app:app --reload --port 8000

# 모니터링 대시보드 실행
uv run streamlit run src/dashboard/app.py
```

---

## 문서

| 문서 | 설명 |
|------|------|
| [doc/README.md](doc/README.md) | 프로젝트 개요 및 아키텍처 |
| [doc/SWIFT_MT_Guide.md](doc/SWIFT_MT_Guide.md) | SWIFT MT 메시지 구조 및 필드 가이드 |
| [doc/BOK_Interface_Spec.md](doc/BOK_Interface_Spec.md) | 한국은행 연동 규격 |
| [doc/OffshoreKRW_Flow.md](doc/OffshoreKRW_Flow.md) | 역외원화결제 플로우 상세 |
| [doc/API_Reference.md](doc/API_Reference.md) | 모듈별 API 참조 |

---

## 테스트

```bash
uv run pytest tests/          # 전체 219개 테스트
uv run pytest tests/unit/     # 단위 테스트
uv run pytest tests/scenarios/# E2E 시나리오 테스트
```

---

## 라이선스

MIT
