# 역외원화결제시스템 사전 학습용 바이브코딩 프로젝트 개발계획

## 📋 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **프로젝트명** | SWIFT MT 메시지 시뮬레이터 (OWP-Simulator) |
| **목적** | 역외원화결제 + 한국은행 SWIFT 전문 처리 실습 |
| **기간** | 4주 (파트타임 바이브코딩 기준) |
| **기술스택** | Python / Node.js + SWIFT 메시지 파서 + 간이 DB |

---

## 🎯 학습 목표

```
✅ SWIFT MT 전문 구조 이해 (MT103, MT202, MT950, MT900/910)
✅ 한국은행 연동 메시지 플로우 파악
✅ 역외원화(CNH-KRW, USD-KRW) 결제 프로세스 이해
✅ 전문 파싱 / 생성 / 검증 로직 직접 구현
✅ 실무 투입 시 코드 패턴 사전 체득
```

---

## 🗓️ 4주 개발 계획

### **1주차 : SWIFT 전문 기초 구현**

#### Day 1-2 | SWIFT MT 메시지 파서 개발
```python
# 실습 목표: MT103 전문 파싱
# 예시 MT103 전문 구조

raw_mt103 = """
{1:F01WOOBURKRSAXXX0000000000}
{2:I103HNBKKRSEXXX}
{3:{108:REF20240101001}}
{4:
:20:SENDER-REF-001
:23B:CRED
:32A:240101KRW50000000,
:50K:/123456789
WOORI BANK SEOUL
:57A:HNBKKRSE
:59:/987654321
KOREA BANK COUNTERPARTY
:70:OFFSHORE KRW PAYMENT TEST
:71A:SHA
-}
"""

# 구현 Task
# 1. Block 파싱 (Block1~5)
# 2. 태그별 필드 추출
# 3. 필드 유효성 검증
```

**구현 항목:**
- [ ] Block 1~5 파서
- [ ] Tag 추출기 (`:20:`, `:32A:`, `:50K:` 등)
- [ ] BIC 코드 검증기
- [ ] 금액/통화 파서 (KRW 처리)

---

#### Day 3-4 | MT 전문 생성기 개발

```python
class SWIFTMessageBuilder:
    """
    SWIFT MT 전문 생성기
    역외원화결제용 MT103 / MT202 생성
    """
    
    def build_mt103(self, payment_data: dict) -> str:
        """송금 전문 생성"""
        pass
    
    def build_mt202(self, cover_data: dict) -> str:
        """은행간 자금이체 전문 생성"""
        pass
    
    def build_mt950(self, statement_data: dict) -> str:
        """잔액보고 전문 생성"""
        pass

# 한국은행 연동 특화 전문
class BOKMessageBuilder(SWIFTMessageBuilder):
    """
    한국은행(BOK) 전용 전문 빌더
    BOK BIC: HNBKKRSE
    """
    
    def build_bok_mt103(self, amount: Decimal, 
                         currency: str = "KRW") -> str:
        pass
```

**구현 항목:**
- [ ] MT103 생성기
- [ ] MT202 생성기  
- [ ] MT950/940 생성기
- [ ] 한국은행 BIC 기준 헤더 자동 설정

---

#### Day 5 | 유효성 검증 엔진

```python
class SWIFTValidator:
    
    RULES = {
        ":20:": {"max_len": 16, "pattern": r"[A-Z0-9/-]{1,16}"},
        ":32A:": {"format": "YYMMDD + Currency(3) + Amount"},
        ":71A:": {"values": ["BEN", "OUR", "SHA"]},
    }
    
    def validate_mt103(self, message: dict) -> ValidationResult:
        """MT103 필수 필드 및 형식 검증"""
        errors = []
        # :20: 필수
        # :23B: 필수  
        # :32A: 필수 (날짜+통화+금액)
        # :50K 또는 50F 필수
        # :59 필수
        return ValidationResult(errors)
```

---

### **2주차 : 역외원화결제 프로세스 구현**

#### Day 6-7 | 결제 플로우 시뮬레이션

```
[역외원화결제 플로우]

해외거래은행          우리은행(국내)         한국은행
    │                     │                    │
    │──MT103 송금─────────>│                    │
    │                     │──MT103 통보────────>│
    │                     │                    │
    │                     │<─MT900 확인─────────│
    │<─MT910 수신확인──────│                    │
    │                     │──MT202 자금이체────>│
    │                     │                    │
    │                     │<─MT950 잔액보고─────│
```

**구현 항목:**
- [ ] 결제 플로우 오케스트레이터
- [ ] 상태 머신 (RECEIVED → VALIDATED → PROCESSED → SETTLED)
- [ ] 각 단계별 MT 전문 자동 생성/발송 시뮬레이션

```python
class OffshoreKRWPaymentFlow:
    
    def __init__(self):
        self.status = PaymentStatus.INIT
    
    def process(self, incoming_mt103: str):
        
        # Step 1: 수신 전문 파싱
        parsed = self.parser.parse(incoming_mt103)
        
        # Step 2: 검증
        self.validator.validate(parsed)
        
        # Step 3: 한국은행 통보 MT103 생성
        bok_mt103 = self.builder.build_bok_mt103(parsed)
        
        # Step 4: 승인 대기 → MT900 수신 시뮬레이션
        self.simulate_bok_response(bok_mt103)
        
        # Step 5: MT910 수신확인 발송
        mt910 = self.builder.build_mt910(parsed)
        
        # Step 6: MT202 자금이체
        mt202 = self.builder.build_mt202(parsed)
        
        return PaymentResult(all_messages=[bok_mt103, mt910, mt202])
```

---

#### Day 8-9 | 환율 처리 모듈

```python
class ExchangeRateProcessor:
    """
    역외원화 환율 처리
    - USD/KRW
    - CNH/KRW  
    - 기준환율 vs 재정환율
    """
    
    def convert_to_krw(self, 
                        amount: Decimal,
                        from_currency: str,
                        rate_type: str = "BASE") -> KRWAmount:
        pass
    
    def apply_spread(self, base_rate: Decimal, 
                     spread_bp: int) -> Decimal:
        """스프레드 적용 (베이시스 포인트)"""
        pass
    
    def calculate_bok_reporting_amount(self, 
                                        amount: Decimal) -> Decimal:
        """한국은행 보고 기준 금액 산출"""
        pass
```

---

#### Day 10 | 전문 로깅 / 감사추적 시스템

```python
class SWIFTAuditLogger:
    """
    금융 규제 요구사항 기반 감사 로그
    - 전문 송수신 이력 전체 보관
    - 위변조 방지 해시 처리
    """
    
    def log_message(self, 
                    direction: str,  # INBOUND / OUTBOUND
                    mt_type: str,    # MT103, MT202...
                    raw_message: str,
                    status: str):
        
        audit_record = {
            "timestamp": datetime.now(timezone.utc),
            "direction": direction,
            "mt_type": mt_type,
            "message_hash": self._sha256(raw_message),
            "raw": raw_message,
            "status": status
        }
        # DB 저장
```

---

### **3주차 : 한국은행 연동 시뮬레이터**

#### Day 11-12 | BOK 모의 서버 구축

```python
# FastAPI 기반 한국은행 SWIFT 게이트웨이 모의 서버

from fastapi import FastAPI

app = FastAPI(title="BOK SWIFT Gateway Simulator")

@app.post("/swift/inbound/mt103")
async def receive_mt103(raw_message: str):
    """
    한국은행이 우리은행으로부터 MT103 수신 시뮬레이션
    → MT900 자동 응답
    """
    parsed = parser.parse(raw_message)
    
    # 처리 지연 시뮬레이션 (실제 BOK 응답시간)
    await asyncio.sleep(random.uniform(0.5, 2.0))
    
    # MT900 응답 생성
    mt900 = build_mt900_response(parsed)
    
    return {"status": "ACCEPTED", "response": mt900}

@app.post("/swift/inbound/mt202")
async def receive_mt202(raw_message: str):
    """자금이체 수신 → MT950 잔액보고"""
    pass

# 오류 시나리오 테스트용
@app.post("/swift/simulate/reject")
async def simulate_rejection(reason: str):
    """MT195 조회 / MT196 응신 오류 시뮬레이션"""
    pass
```

---

#### Day 13-14 | 이상 케이스 처리

```python
class ExceptionHandler:
    """
    실무 발생 예외 케이스 시뮬레이션
    """
    
    scenarios = {
        "DUPLICATE_REF": "동일 Reference 중복 전송",
        "INVALID_BIC": "잘못된 BIC 코드",
        "AMOUNT_MISMATCH": "MT103 vs MT202 금액 불일치",
        "CUTOFF_EXCEEDED": "마감시간 초과 전문",
        "INVALID_KRW_FORMAT": "원화 금액 형식 오류",
        "BOK_TIMEOUT": "한국은행 응답 타임아웃",
        "NOSTRO_INSUFFICIENT": "노스트로 계좌 잔액 부족",
    }
    
    def test_scenario(self, scenario_key: str):
        """시나리오별 예외 처리 테스트"""
        pass
```

**구현 항목:**
- [ ] 7가지 예외 시나리오 처리
- [ ] MT195/MT199 조회전문 처리
- [ ] Repair Queue 구현 (수동 수정 플로우)

---

#### Day 15 | 마감시간 / Cut-off 관리

```python
class CutOffTimeManager:
    """
    역외원화결제 마감시간 관리
    """
    
    CUTOFF_TIMES = {
        "BOK_KRW_DOMESTIC": time(16, 30),   # 한국은행 원화 마감
        "BOK_KRW_OFFSHORE": time(15, 00),   # 역외원화 마감
        "SWIFT_DAILY": time(17, 00),         # SWIFT 일일 마감
    }
    
    def check_cutoff(self, payment_type: str) -> CutOffResult:
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        cutoff = self.CUTOFF_TIMES[payment_type]
        
        return CutOffResult(
            is_within=now.time() < cutoff,
            remaining_minutes=self._calc_remaining(now, cutoff),
            next_value_date=self._calc_next_value_date(now)
        )
```

---

### **4주차 : 통합 테스트 & 대시보드**

#### Day 16-17 | 전체 통합 테스트

```python
class IntegrationTestSuite:
    """
    실제 업무 시나리오 기반 E2E 테스트
    """
    
    def test_normal_offshore_krw_payment(self):
        """정상 역외원화 송금 전체 플로우"""
        # 1. 해외은행 MT103 수신
        # 2. 파싱 & 검증
        # 3. BOK MT103 통보
        # 4. BOK MT900 수신
        # 5. MT910 수신확인
        # 6. MT202 자금이체
        # 7. MT950 잔액확인
        pass
    
    def test_high_value_payment(self):
        """고액 결제 (1억원 이상) 추가 검증 플로우"""
        pass
    
    def test_end_of_day_settlement(self):
        """일일 마감 정산 플로우"""
        pass
    
    def test_giro_payment(self):
        """지로 연계 결제"""
        pass
```

---

#### Day 18-19 | 모니터링 대시보드

```
┌─────────────────────────────────────────────┐
│     역외원화결제 SWIFT 모니터링 대시보드        │
├──────────────┬──────────────┬───────────────┤
│  수신 전문    │  처리 중     │  완료/오류     │
│  MT103: 24건 │  대기: 3건   │  완료: 21건   │
│  MT202: 18건 │  오류: 1건   │  거부: 2건    │
├──────────────┴──────────────┴───────────────┤
│  실시간 전문 플로우                            │
│  [MT103] ──> [VALIDATE] ──> [BOK_SEND]      │
│           └──> [ERROR] ──> [REPAIR_Q]       │
├─────────────────────────────────────────────┤
│  BOK 연동 상태: 🟢 정상   마감까지: 2h 30m   │
└─────────────────────────────────────────────┘
```

**구현 항목:**
- [ ] Streamlit 기반 대시보드
- [ ] 실시간 전문 처리 현황
- [ ] BOK 연동 상태 모니터링
- [ ] 예외 전문 Repair Queue 화면

---

#### Day 20 | 최종 점검 & 문서화

```
📁 프로젝트 산출물

OWP-Simulator/
├── src/
│   ├── parser/          # SWIFT 전문 파서
│   ├── builder/         # 전문 생성기
│   ├── validator/       # 유효성 검증
│   ├── flow/            # 결제 플로우
│   ├── bok_simulator/   # BOK 모의 서버
│   └── dashboard/       # 모니터링 UI
├── tests/
│   ├── unit/
│   ├── integration/
│   └── scenarios/       # 실무 시나리오 테스트
├── docs/
│   ├── SWIFT_MT_Guide.md
│   ├── BOK_Interface_Spec.md
│   └── OffshoreKRW_Flow.md
└── sample_messages/     # 실습용 샘플 전문
```

---

## 🛠️ 기술 스택 상세

| 영역 | 기술 |
|------|------|
| **언어** | Python 3.11+ |
| **웹 프레임워크** | FastAPI (BOK 모의 서버) |
| **대시보드** | Streamlit |
| **DB** | SQLite (로컬 실습용) |
| **SWIFT 파싱** | 직접 구현 + `swift-parser` 참고 |
| **테스트** | pytest + pytest-asyncio |
| **AI 코딩** | Cursor IDE + Claude |

---

## 📚 사전 학습 체크리스트

```
SWIFT 기초
□ SWIFT BIC 체계 이해 (WOOBURKR / HNBKKRSE)
□ MT vs MX(ISO20022) 차이 이해
□ Block 1~5 구조 암기
□ MT103 / MT202 / MT950 필드 학습

역외원화 도메인
□ 역외원화(Offshore KRW) 개념
□ 노스트로/로스트로 계좌 개념
□ Value Date / Settlement Date 개념
□ 한국은행 외환결제 규정 기초

실무 패턴
□ 금융 시스템 멱등성 처리
□ 전문 재처리 (Reprocessing) 패턴
□ 마감시간 처리 로직
□ 감사 로그 설계 원칙
```

