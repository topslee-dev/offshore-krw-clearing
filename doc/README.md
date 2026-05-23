# SWIFT MT 메시지 시뮬레이터 (OWP-Simulator)

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **프로젝트명** | OWP-Simulator (Offshore Payment SWIFT Simulator) |
| **목적** | 역외원화결제 + 한국은행 SWIFT 전문 처리 실습 |
| **개발 기간** | 4주 (파트타임 바이브코딩) |
| **버전** | 1.0.0 |

---

## 학습 목표

- SWIFT MT 전문 구조 이해 (MT103, MT202, MT950, MT900/910)
- 한국은행 연동 메시지 플로우 파악
- 역외원화(CNH-KRW, USD-KRW) 결제 프로세스 이해
- 전문 파싱 / 생성 / 검증 로직 직접 구현
- 실무 투입 시 코드 패턴 사전 체득

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| **언어** | Python 3.11+ |
| **웹 프레임워크** | FastAPI (BOK 모의 서버) |
| **대시보드** | Streamlit |
| **DB** | SQLite (로컬 실습용) |
| **테스트** | pytest + pytest-asyncio |

---

## 프로젝트 구조

```
OWP-Simulator/
├── src/
│   ├── __init__.py
│   ├── parser/              # SWIFT 전문 파서
│   │   ├── __init__.py
│   │   ├── block_parser.py # Block 1~5 파서
│   │   ├── tag_parser.py    # 태그 추출기
│   │   ├── field_validator.py
│   │   └── bic_validator.py
    │   ├── builder/             # 전문 생성기
    │   │   ├── __init__.py
    │   │   ├── mt103_builder.py
    │   │   ├── mt202_builder.py
    │   │   └── mt9xx_builder.py
    │   ├── validator/           # 유효성 검증
    │   │   ├── __init__.py
    │   │   └── swift_validator.py
│   ├── flow/               # 결제 플로우
│   │   ├── __init__.py
│   │   ├── payment_flow.py
│   │   ├── status_machine.py
│   │   └── exchange_processor.py
│   ├── bok_simulator/       # BOK 모의 서버
│   │   ├── __init__.py
│   │   ├── app.py          # FastAPI 앱
│   │   ├── handlers.py     # 메시지 핸들러
│   │   └── scenarios.py    # 예외 시나리오
│   ├── audit/              # 감사 로깅
│   │   ├── __init__.py
│   │   └── logger.py
│   └── cutoff/             # 마감시간 관리
│       ├── __init__.py
│       └── manager.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── scenarios/
├── docs/                   # 문서
│   ├── README.md           # 본 문서
│   ├── SWIFT_MT_Guide.md
│   ├── BOK_Interface_Spec.md
│   ├── OffshoreKRW_Flow.md
│   └── API_Reference.md
├── sample_messages/        # 실습용 샘플 전문
├── requirements.txt
└── README.md
```

---

## 모듈 설명

### parser (SWIFT 전문 파서)

SWIFT MT 메시지를 파싱하는 핵심 모듈입니다.

| 모듈 | 설명 |
|------|------|
| `block_parser.py` | Block 1~5 구조 파싱 (Basic Header, Application Header, User Header, Text, Trailer) |
| `tag_parser.py` | 태그(:20:, :32A: 등) 추출 및 필드 파싱 |
| `field_validator.py` | 필드별 형식 및 길이 검증 |
| `bic_validator.py` | BIC 코드 체계 검증 (8+3 형식) |

### builder (전문 생성기)

SWIFT MT 메시지를 생성하는 모듈입니다.

| 모듈 | 설명 |
|------|------|
| `mt103_builder.py` | 송금 전문 (Customer Credit Transfer) 생성 |
| `mt202_builder.py` | 은행간 자금이체 전문 (Cover Payment) 생성 |
| `mt950_builder.py` | 잔액보고 전문 (Statement) 생성 |
| `mt9xx_builder.py` | MT900/910/940 등 확인/응답 전문 생성 |

### validator (유효성 검증)

메시지 검증 로직을 담당합니다.

| 모듈 | 설명 |
|------|------|
| `swift_validator.py` | MT103, MT202 등 메시지 유형별 검증 |
| `field_rules.py` | 필드별 검증 규칙 정의 |

### flow (결제 플로우)

역외원화결제 비즈니스 프로세스를 구현합니다.

| 모듈 | 설명 |
|------|------|
| `payment_flow.py` | 결제 플로우 오케스트레이터 |
| `status_machine.py` | 상태 머신 (RECEIVED → VALIDATED → PROCESSED → SETTLED) |
| `exchange_processor.py` | 환율 처리 (USD/KRW, CNH/KRW) |

### bok_simulator (BOK 모의 서버)

한국은행 SWIFT 게이트웨이 시뮬레이터입니다.

| 모듈 | 설명 |
|------|------|
| `app.py` | FastAPI 기반 REST API 서버 |
| `handlers.py` | MT 수신/응답 핸들러 |
| `scenarios.py` | 예외 시나리오 (DUPLICATE_REF, INVALID_BIC 등) |

### audit (감사 로깅)

금융 규제 요건에 따른 감사 로그 시스템입니다.

| 모듈 | 설명 |
|------|------|
| `logger.py` | 전문 송수신 이력 기록, 해시 기반 위변조 방지 |

### cutoff (마감시간 관리)

마감시간 관리 및 컷오프 로직입니다.

| 모듈 | 설명 |
|------|------|
| `manager.py` | BOK_KRW_DOMESTIC, BOK_KRW_OFFSHORE, SWIFT_DAILY 마감시간 관리 |

---

## 개발 진행 계획 (4주)

### 1주차: SWIFT 전문 기초 구현

| Day | 내용 |
|-----|------|
| Day 1-2 | SWIFT MT 메시지 파서 개발 (Block 파서, Tag 추출, BIC 검증, 금액/통화 파서) |
| Day 3-4 | MT 전문 생성기 개발 (MT103, MT202, MT950, MT940) |
| Day 5 | 유효성 검증 엔진 구현 |

### 2주차: 역외원화결제 프로세스 구현

| Day | 내용 |
|-----|------|
| Day 6-7 | 결제 플로우 시뮬레이션 (오케스트레이터, 상태 머신) |
| Day 8-9 | 환율 처리 모듈 (USD/KRW, CNH/KRW, 스프레드 적용) |
| Day 10 | 전문 로깅 / 감사추적 시스템 |

### 3주차: 한국은행 연동 시뮬레이터

| Day | 내용 |
|-----|------|
| Day 11-12 | BOK 모의 서버 구축 (FastAPI 기반) |
| Day 13-14 | 이상 케이스 처리 (7가지 예외 시나리오, Repair Queue) |
| Day 15 | 마감시간 / Cut-off 관리 |

### 4주차: 통합 테스트 & 대시보드

| Day | 내용 |
|-----|------|
| Day 16-17 | 전체 통합 테스트 (E2E 시나리오) |
| Day 18-19 | 모니터링 대시보드 (Streamlit) |
| Day 20 | 최종 점검 & 문서화 |

---

## 시작하기

### 설치

```bash
pip install -r requirements.txt
```

### 실행

```bash
# BOK 모의 서버 실행
python -m src.bok_simulator.app

# 대시보드 실행
streamlit run src/dashboard/app.py
```

### 테스트

```bash
pytest tests/ -v
```

---

## 관련 문서

- [SWIFT MT 가이드](./SWIFT_MT_Guide.md) - MT 메시지 구조 및 필드 설명
- [BOK 연동 규격](./BOK_Interface_Spec.md) - 한국은행 연동 메시지 규격
- [역외원화결제 플로우](./OffshoreKRW_Flow.md) - 결제 비즈니스 프로세스 상세
- [API 참조](./API_Reference.md) - 모듈별 API 상세 참조