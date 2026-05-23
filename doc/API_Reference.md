# API 참조 문서

## 모듈별 API 상세

---

## parser 모듈

### SWIFTBlockParser

```python
from src.parser.block_parser import SWIFTBlockParser

parser = SWIFTBlockParser()
```

#### Methods

##### `parse(raw_message: str) -> ParsedMessage`

SWIFT 메시지를 Block별로 파싱합니다.

```python
raw_mt103 = """
{1:F01WOOBURKRSAXXX0000000000}
{2:I103HNBKKRSEXXX}
{3:{108:REF20240101001}}
{4:
:20:SENDER-REF-001
:23B:CRED
-}
"""

result = parser.parse(raw_mt103)
# result.block1  # Basic Header
# result.block2  # Application Header
# result.block3  # User Header
# result.block4  # Text (raw)
# result.block5  # Trailer
```

**Parameters:**
- `raw_message: str` - 원본 SWIFT 메시지

**Returns:**
- `ParsedMessage` - 파싱 결과 객체

---

### TagParser

```python
from src.parser.tag_parser import TagParser

tag_parser = TagParser()
```

#### Methods

##### `extract_tags(text_block: str) -> List[Tag]`

Block 4 텍스트에서 태그를 추출합니다.

```python
tags = tag_parser.extract_tags(raw_text)
# [
#   Tag(name=":20:", value="SENDER-REF-001", line=1),
#   Tag(name=":23B:", value="CRED", line=2),
#   ...
# ]
```

##### `parse_field(tag: Tag) -> Field`

태그를 파싱하여 Field 객체로 반환합니다.

```python
field = tag_parser.parse_field(tags[0])
# field.name   # ":20:"
# field.value  # "SENDER-REF-001"
```

---

### BICValidator

```python
from src.parser.bic_validator import BICValidator

validator = BICValidator()
```

#### Methods

##### `validate(bic: str) -> bool`

BIC 코드 유효성을 검증합니다.

```python
is_valid = validator.validate("HNBKKRSEXXX")
# True

is_valid = validator.validate("INVALID")
# False
```

##### `parse(bic: str) -> Optional[BICInfo]`

BIC 코드를 분석하여 정보를 반환합니다.

```python
info = validator.parse("WOOBURKRSAXXX")
# BICInfo(
#   bank_code="WOOB",
#   country_code="KR",
#   location_code="SE",
#   branch_code="XXX"
# )
```

---

## builder 모듈

### MT103Builder

```python
from src.builder.mt103_builder import MT103Builder

builder = MT103Builder()
```

#### Methods

##### `build(payment_data: dict) -> str`

MT103 메시지를 생성합니다.

```python
payment = {
    "sender_ref": "REF20240101001",
    "value_date": "240101",
    "currency": "KRW",
    "amount": Decimal("50000000"),
    "sender_bic": "WOOBURKRSAXXX",
    "receiver_bic": "HNBKKRSEXXX",
    "ordering_customer": {
        "account": "/123456789",
        "name": "WOORI BANK SEOUL"
    },
    "beneficiary_customer": {
        "account": "/987654321",
        "name": "KOREA BANK COUNTERPARTY"
    },
    "charge_type": "SHA"
}

mt103 = builder.build(payment)
```

**Parameters:**
- `payment_data: dict` - 결제 정보 딕셔너리

**Returns:**
- `str` - 생성된 MT103 원본 메시지

---

### MT202Builder

```python
from src.builder.mt202_builder import MT202Builder

builder = MT202Builder()
```

#### Methods

##### `build(cover_data: dict) -> str`

MT202 메시지를 생성합니다.

```python
cover = {
    "sender_ref": "COVER-001",
    "related_ref": "MT103-REF-001",
    "value_date": "240101",
    "currency": "KRW",
    "amount": Decimal("50000000"),
    "ordering_institution": "WOOBUS33",
    "beneficiary_institution": "HNBKKRSE"
}

mt202 = builder.build(cover)
```

---

### MT9xxBuilder

MT900, MT910, MT940 등 확인/응답 메시지를 생성합니다.

```python
from src.builder.mt9xx_builder import MT9xxBuilder

builder = MT9xxBuilder()
```

#### Methods

##### `build_mt900(debit_data: dict) -> str`

MT900 (차변 통보)을 생성합니다.

```python
debit = {
    "reference": "BOK-900-001",
    "related_ref": "MT202-REF-001",
    "account": "1234567890",
    "value_date": "240101",
    "currency": "KRW",
    "amount": Decimal("50000000")
}

mt900 = builder.build_mt900(debit)
```

##### `build_mt910(credit_data: dict) -> str`

MT910 (대변 통보)을 생성합니다.

```python
credit = {
    "reference": "BOK-910-001",
    "related_ref": "MT202-REF-001",
    "account": "1234567890",
    "value_date": "240101",
    "currency": "KRW",
    "amount": Decimal("50000000")
}

mt910 = builder.build_mt910(credit)
```

---

## validator 모듈

### SWIFTValidator

```python
from src.validator.swift_validator import SWIFTValidator

validator = SWIFTValidator()
```

#### Methods

##### `validate_mt103(message: dict) -> ValidationResult`

MT103 메시지를 검증합니다.

```python
parsed = {
    "block1": "{1:F01WOOBURKRSAXXX0000000000}",
    "block2": "{2:I103HNBKKRSEXXX}",
    "block4": {
        ":20:": "SENDER-REF-001",
        ":23B:": "CRED",
        ":32A:": "240101KRW50000000,"
    }
}

result = validator.validate_mt103(parsed)
# result.is_valid    # True/False
# result.errors     # ["error1", "error2"]
# result.warnings   # ["warning1"]
```

##### `validate_field(tag: str, value: str) -> bool`

개별 필드의 유효성을 검증합니다.

```python
is_valid = validator.validate_field(":20:", "SENDER-REF-001")
```

---

## flow 모듈

### OffshoreKRWPaymentFlow

```python
from src.flow.payment_flow import OffshoreKRWPaymentFlow

flow = OffshoreKRWPaymentFlow()
```

#### Methods

##### `process(incoming_mt103: str) -> PaymentResult`

역외원화결제를 처리합니다.

```python
raw_mt103 = """
{1:F01WOOBURKRSAXXX0000000000}
{2:I103HNBKKRSEXXX}
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

result = flow.process(raw_mt103)
# result.status          # PaymentStatus.SETTLED
# result.all_messages    # [mt103_to_bok, mt900, mt910, mt202, mt950]
```

---

### StatusMachine

```python
from src.flow.status_machine import StatusMachine, PaymentStatus

sm = StatusMachine()
```

#### Properties

##### `current_status: PaymentStatus`

현재 상태를 반환합니다.

```python
current = sm.current_status
# PaymentStatus.PROCESSING
```

#### Methods

##### `transition(event: str) -> PaymentStatus`

상태 전이를 수행합니다.

```python
new_status = sm.transition("VALIDATE")
# PaymentStatus.VALIDATED
```

##### `can_transition(event: str) -> bool`

전이 가능 여부를 확인합니다.

```python
can_proceed = sm.can_transition("PROCESS")
# True/False
```

---

### ExchangeRateProcessor

```python
from src.flow.exchange_processor import ExchangeRateProcessor

processor = ExchangeRateProcessor()
```

#### Methods

##### `convert_to_krw(amount: Decimal, from_currency: str, rate_type: str = "BASE") -> KRWAmount`

외화를 원화로 변환합니다.

```python
krw_amount = processor.convert_to_krw(
    amount=Decimal("1000000"),
    from_currency="USD",
    rate_type="BASE"
)
# KRWAmount(
#   original=Decimal("1000000"),
#   currency="USD",
#   rate=Decimal("1330.50"),
#   krw_amount=Decimal("1330500000"),
#   spread_applied=Decimal("3.99")
# )
```

##### `apply_spread(base_rate: Decimal, spread_bp: int) -> Decimal`

스프레드를 적용합니다.

```python
adjusted_rate = processor.apply_spread(
    base_rate=Decimal("1330.50"),
    spread_bp=30  # 30 basis points = 0.30%
)
# Decimal("1334.4915")
```

---

## bok_simulator 모듈

### BOKSimulator (FastAPI)

```python
from src.bok_simulator.app import app

# FastAPI 앱 인스턴스
```

#### Endpoints

##### `POST /swift/inbound/mt103`

MT103 수신 시뮬레이션.

```bash
curl -X POST http://localhost:8000/swift/inbound/mt103 \
  -H "Content-Type: application/json" \
  -d '{"raw_message": "{1:F01...}"}'
```

**Response:**
```json
{
  "status": "ACCEPTED",
  "response": "{1:F01HNBKKRSEXXX...}",
  "processing_time_ms": 150
}
```

##### `POST /swift/inbound/mt202`

MT202 수신 시뮬레이션.

```bash
curl -X POST http://localhost:8000/swift/inbound/mt202 \
  -H "Content-Type: application/json" \
  -d '{"raw_message": "{1:F01...}"}'
```

##### `POST /swift/simulate/reject`

오류 시나리오 시뮬레이션.

```bash
curl -X POST http://localhost:8000/swift/simulate/reject \
  -H "Content-Type: application/json" \
  -d '{"reason": "INVALID_BIC", "original_message": "{1:F01...}"}'
```

**Response:**
```json
{
  "error_code": "NAK199",
  "reason": "Invalid BIC code",
  "repair_required": true
}
```

##### `GET /health`

서버 상태 확인.

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## audit 모듈

### SWIFTAuditLogger

```python
from src.audit.logger import SWIFTAuditLogger

logger = SWIFTAuditLogger()
```

#### Methods

##### `log_message(direction: str, mt_type: str, raw_message: str, status: str)`

전문 송수신 로그를 기록합니다.

```python
logger.log_message(
    direction="INBOUND",
    mt_type="MT103",
    raw_message="{1:F01WOOBURKRSAXXX...}",
    status="PROCESSED"
)
```

##### `get_logs(filters: dict) -> List[AuditRecord]`

로그를 조회합니다.

```python
logs = logger.get_logs({
    "mt_type": "MT103",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
})
```

##### `verify_hash(message_id: str) -> bool`

메시지 무결성을 검증합니다.

```python
is_valid = logger.verify_hash("msg-001")
# True (위변조 없음)
```

---

## cutoff 모듈

### CutOffTimeManager

```python
from src.cutoff.manager import CutOffTimeManager

manager = CutOffTimeManager()
```

#### Properties

##### `CUTOFF_TIMES`

마감시간 설정.

```python
manager.CUTOFF_TIMES
# {
#   "BOK_KRW_DOMESTIC": time(16, 30),
#   "BOK_KRW_OFFSHORE": time(15, 00),
#   "SWIFT_DAILY": time(17, 00)
# }
```

#### Methods

##### `check_cutoff(payment_type: str) -> CutOffResult`

마감 여부를 확인합니다.

```python
result = manager.check_cutoff("BOK_KRW_OFFSHORE")
# CutOffResult(
#   is_within=True,
#   remaining_minutes=45,
#   next_value_date=date(2024, 1, 2)
# )
```

##### `is_available(payment_type: str) -> bool`

거래 가능 여부를 반환합니다.

```python
is_available = manager.is_available("BOK_KRW_OFFSHORE")
# True (마감 전)
```

---

## 공통 데이터 타입

### PaymentStatus

```python
from enum import Enum

class PaymentStatus(Enum):
    INIT = "INIT"
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    PROCESSING = "PROCESSING"
    PENDING_BOK = "PENDING_BOK"
    SETTLED = "SETTLED"
    ERROR = "ERROR"
    REPAIR = "REPAIR"
```

### ValidationResult

```python
@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
```

### CutOffResult

```python
@dataclass
class CutOffResult:
    is_within: bool
    remaining_minutes: int
    next_value_date: date
```

---

## 관련 문서

- [프로젝트 README](./README.md)
- [SWIFT MT 가이드](./SWIFT_MT_Guide.md)
- [BOK 연동 규격](./BOK_Interface_Spec.md)
- [역외원화결제 플로우](./OffshoreKRW_Flow.md)