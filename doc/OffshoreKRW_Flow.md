# 역외원화결제 플로우

## 개요

역외원화결제(Offshore KRW Payment)는 해외 거래 은행 간 원화 거래를 정산하는 체계입니다.
본 문서는 실제 업무에서 사용되는 역외원화 결제 프로세스를 설명합니다.

---

## 역외원화결제란?

### 정의

역외원화(Offshore KRW)는 한국 국외에서 원화(KRW)를 거래하는 것을 말합니다.
주로 해외 은행 간 원화 예금 거래, 무역 정산 등에 사용됩니다.

### 특징

| 항목 | 내용 |
|------|------|
| **거래 장소** | 해외 (주로 홍콩, Singapore) |
| **거래 통화** | KRW (원화) |
| **결제 방식** | SWIFT MT 메시지 |
| **관리 기관** | 한국은행 |

---

## 결제 플로우 상세

### 전체 흐름도

```
해외거래은행          우리은행(국내)         한국은행
    │                     │                    │
    │──MT103 송금─────────>│                    │
    │                     │                    │
    │                     │──MT103 통보────────>│
    │                     │                    │
    │                     │<─MT900 확인─────────│
    │<─MT910 수신확인──────│                    │
    │                     │                    │
    │                     │──MT202 자금이체────>│
    │                     │                    │
    │                     │<─MT950 잔액보고─────│
```

### 상태 머신

```
RECEIVED ──> VALIDATED ──> PROCESSING ──> PENDING_BOK ──> SETTLED
    │              │             │              │
    v              v             v              v
  ERROR ───> REPAIR ───> (재처리) ──> VALIDATED
```

| 상태 | 설명 |
|------|------|
| `RECEIVED` | 전문 수신 완료 |
| `VALIDATED` | 형식 검증 완료 |
| `PROCESSING` | 처리 중 |
| `PENDING_BOK` | 한국은행 응답 대기 |
| `SETTLED` | 정산 완료 |
| `ERROR` | 처리 오류 |
| `REPAIR` | 수동 복구 대기 |

---

## 단계별 상세

### Step 1: MT103 수신

해외 거래 은행으로부터 MT103 송금 전문을 수신합니다.

**수신 조건:**
- Block 1~4 형식 유효
- 필수 태그 존재 (:20:, :23B:, :32A:, :50K:, :59:)
- BIC 코드 유효

**예시:**
```
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
```

### Step 2: 파싱 및 검증

수신된 MT103를 파싱하고 유효성을 검증합니다.

**검증 항목:**
- Block 구조 (Basic, Application, User, Text)
- 필수 태그 존재 여부
- 태그별 형식 (길이, 패턴)
- BIC 코드 유효성
- 금액 형식 (KRW: 소수점 없음)

### Step 3: 한국은행 통보 (MT103 Forward)

검증 완료 후, 한국은행에 MT103 통보 메시지를 전송합니다.

**전송 조건:**
- 원화 금액 (KRW)
- 역외원화 결제 해당
- Cut-off 시간 이내

### Step 4: MT900 확인 대기

한국은행으로부터 MT900 (차변 확인)을 수신합니다.

**수신 내용:**
- 계좌 차감 금액
- Value Date
- 참조번호

### Step 5: MT910 수신확인

MT900 확인 후, MT910 (수신확인)을 전송합니다.

**응답 시간:** 일반적으로 1~5초

### Step 6: MT202 자금이체

실제 자금이체를 위해 MT202를 전송합니다.

**필드 설정:**
- :21: - 관련 참조번호 (MT103 참조)
- :32A: - 금액 (KRW)
- :58A: - 수령 은행 (한국은행 BIC)

### Step 7: MT950 잔액 보고

한국은행이 nostro 계좌 잔액을 MT950로 보고합니다.

**보고 내용:**
- 일일 시작/종료 잔액
- 거래 내역
- Value Date

---

## 환율 처리

### 환전 플로우

```
외화 금액 (USD/CNH)
    │
    ├── 기준환율 조회
    │     │
    │     ├── 스프레드 적용
    │     │     │
    │     │     └── 원화 금액 산출
    │     │
    │     └── KRWAmount 반환
    │
    └── 재정환율 적용 (대금 정산)
          │
          └── 협정 스프레드
                │
                └── 보고용 원화 금액
```

### 스프레드 계산

```python
def apply_spread(base_rate: Decimal, spread_bp: int) -> Decimal:
    """
    베이시스 포인트(bp) 단위로 스프레드 적용

    Args:
        base_rate: 기준환율 (예: 1330.50)
        spread_bp: 스프레드 (예: 30 = 0.30%)

    Returns:
        조정된 환율
    """
    spread_rate = Decimal(spread_bp) / 10000
    return base_rate * (1 + spread_rate)
```

---

## 금액 처리 규칙

### 원화(KRW) 처리

- 소수점 이하 없음
- 반올림 처리
- 예: 1,234,567.5 KRW → 1,234,568 KRW

### 외화 처리 (USD, CNH 등)

- 소수점 2자리
- 반올림 처리
- 예: 1,000.555 USD → 1,000.56 USD

---

## 노스트로/로스트로 계좌

### 개념

| 구분 | 설명 | 비고 |
|------|------|------|
| **Nostro** | 우리은행이 한국은행에 개설한 원화 계좌 | "우리 것" |
| **Vostro** | 한국은행이 우리은행에 개설한 원화 계좌 | "그대 것" |

### 용도

| 계좌 | 용도 |
|------|------|
| Nostro | 역외원화 결제 시 차감/입금 계좌 |
| Vostro | 고객 지급용 계좌 |

### 잔액 관리

- 일일 MT950로 잔액 보고
- 한도 관리 (Nostro 한도 초과 시 Alert)
- 정산 시간: 16:30 (한국은행 마감)

---

## 예외 처리

### 예외 시나리오 목록

| 시나리오 | 설명 | 처리 |
|----------|------|------|
| `DUPLICATE_REF` | 동일 참조번호 중복 | 첫 건만 처리 |
| `INVALID_BIC` | 잘못된 BIC | NAK + Repair Queue |
| `AMOUNT_MISMATCH` | MT103 vs MT202 불일치 | 정산 부서 협조 |
| `CUTOFF_EXCEEDED` | 마감시간 초과 | 익일 Valor 처리 |
| `INVALID_KRW_FORMAT` | 원화 형식 오류 | Repair 필요 |
| `BOK_TIMEOUT` | BOK 응답 없음 | 재시도 후 대기열 |
| `NOSTRO_INSUFFICIENT` | Nostro 잔액 부족 | 한도 알림 |

### Repair Queue

오류가 발생한 전문은 Repair Queue에 등록됩니다.

**수동 처리 항목:**
1. 형식 오류 수정
2. BIC 코드 교정
3. 금액 조정
4. 참조번호 재할당

---

## 감사 추적

### 로그 항목

모든 전문 처리에 대해 다음 정보를 기록합니다:

```python
audit_record = {
    "timestamp": "2024-01-01T10:30:00+09:00",
    "direction": "INBOUND",  # INBOUND / OUTBOUND
    "mt_type": "MT103",
    "reference": "SENDER-REF-001",
    "message_hash": "sha256:abc123...",
    "raw_message": "{1:F01...}",
    "status": "PROCESSED",
    "processing_time_ms": 150
}
```

### 해시 처리

메시지 위변조 방지를 위해 SHA-256 해시를 생성합니다:

```python
def _sha256(raw_message: str) -> str:
    import hashlib
    return hashlib.sha256(raw_message.encode()).hexdigest()
```

---

## Cut-off 관리

### 시간표

| 구분 | Cut-off 시간 | 비고 |
|------|--------------|------|
| BOK 원화 국내 | 16:30 | 당일 Valor |
| BOK 역외원화 | 15:00 | 당일 Valor |
| SWIFT 일일 | 17:00 | 익일 Valor |

### 처리 로직

```python
def check_cutoff(payment_type: str) -> CutOffResult:
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    cutoff = CUTOFF_TIMES[payment_type]

    return CutOffResult(
        is_within=now.time() < cutoff,
        remaining_minutes=calc_remaining(now, cutoff),
        next_value_date=calc_next_value_date(now)
    )
```

---

## 테스트 시나리오

### TC-001: 정상 역외원화 결제

```
 precondition: Cut-off 시간 이전, Nostro 잔액 충분

 step:
   1. MT103 수신
   2. 파싱/검증
   3. BOK MT103 통보
   4. MT900 수신
   5. MT910 전송
   6. MT202 전송
   7. MT950 수신

 expected: SETTLED 상태
```

### TC-002: 중복 참조 처리

```
 precondition: 동일 참조번호 재전송

 step:
   1. MT103 수신 (Ref: DUP-001)
   2. 중복 참조 감지
   3. ACK299 응답

 expected: 중복 건 무시, 로그 기록
```

### TC-003: 마감시간 초과

```
 precondition: Cut-off 이후 전송

 step:
   1. MT103 수신
   2. Cut-off 체크
   3. 익일 Valor 설정

 expected: NEXT_VALUE_DATE 상태
```

---

## 관련 문서

- [프로젝트 README](./README.md)
- [SWIFT MT 가이드](./SWIFT_MT_Guide.md)
- [BOK 연동 규격](./BOK_Interface_Spec.md)
- [API 참조](./API_Reference.md)