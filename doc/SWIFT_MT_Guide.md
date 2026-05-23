# SWIFT MT 메시지 가이드

## SWIFT 메시지 구조

### Block 구조 (1~5)

SWIFT MT 메시지는 5개의 Block으로 구성됩니다.

```
{1:F01WOOBURKRSAXXX0000000000}   ← Block 1: Basic Header
{2:I103HNBKKRSEXXX}              ← Block 2: Application Header
{3:{108:REF20240101001}}         ← Block 3: User Header (선택)
{4:                             ← Block 4: Text (본문)
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
-}                               ← Block 4 끝
{5:xxx}                          ← Block 5: Trailer (_CHECKSUM)
```

#### Block 1: Basic Header (필수)

```
{F01WOOBURKRSAXXX0000000000}
```

| 영역 | 설명 | 예시 |
|------|------|------|
| F | 전송 프로토콜 식별자 | F (FIN Protocol) |
| 01 | Session Number | 01 |
| WOOBURKRSAXXX | 발신 BIC (8+3) | WOOBURKRSAXXX |
| 0000000000 | Sequence Number | 0000000000 |

#### Block 2: Application Header (필수)

```
{I103HNBKKRSEXXX}
```

| 영역 | 설명 | 예시 |
|------|------|------|
| I | Input (수신) / O (Output, 송신) | I |
| 103 | 메시지 유형 | 103 (MT103) |
| HNBKKRSE | 수신 BIC | HNBKKRSE (한국은행) |
| XXX | 터미널 코드 | XXX |

#### Block 3: User Header (선택)

```
{3:{108:REF20240101001}}
```

- 108:/Reference (참조번호)

#### Block 4: Text (필수)

메시지 본문으로 태그(:XX:)와 내용으로 구성됩니다.

#### Block 5: Trailer (선택)

```
{5:CHK1234567890}
```

- CHK: Checksum (위변조 검증)

---

## 주요 MT 메시지 유형

### MT103: Customer Credit Transfer (송금 전문)

#### 필수 태그

| 태그 | 필드명 | 설명 | 예시 |
|------|--------|------|------|
| :20: | Transaction Reference | 거래 참조번호 | SENDER-REF-001 |
| :23B: | Bank Operation Code | 은행 업무 코드 | CRED |
| :32A: | Value Date/Currency/Amount | 결제일/통화/금액 | 240101KRW50000000 |
| :50K: | Ordering Customer | 송금 고객 | /123456789 |
| :59: | Beneficiary Customer | 수령 고객 | /987654321 |
| :71A: | Detail of Charges | 수수료 방식 | SHA |

#### 선택 태그

| 태그 | 필드명 | 설명 |
|------|--------|------|
| :52A/D: | Ordering Bank | 송금 은행 |
| :53A/D: | Sender's Correspondent | 발신 은행 협력사 |
| :54A/D: | Receiver's Correspondent | 수신 은행 협력사 |
| :55A/D: | Third Reimbursement Institution | 제3 reimbursement 기관 |
| :56A/D: | Intermediary Institution | 중개 은행 |
| :57A/D: | Beneficiary Bank | 수령 은행 |
| :70: | Remittance Information | 송금 정보 |
| :71F: | Sender Charges | 발신 수수료 |
| :71G: | Receiver Charges | 수신 수수료 |

#### MT103 예시

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

---

### MT202: Cover Payment (은행간 자금이체)

은행들이 서로간에 자금을 이체할 때 사용됩니다.

#### 필수 태그

| 태그 | 필드명 | 설명 |
|------|--------|------|
| :20: | Transaction Reference | 거래 참조번호 |
| :21: | Related Reference | 관련 참조번호 |
| :32A: | Value Date/Currency/Amount | 결제일/통화/금액 |
| :52A/D: | Ordering Institution | 명령 은행 |
| :58A/D: | Beneficiary Institution | 수령 은행 |

#### MT202 예시

```
{1:F01WOOBURKRSAXXX0000000000}
{2:O202WOOBURKRSAXXX}
{4:
:20:COVER-REF-001
:21:MT103-REF-001
:32A:240101USD1000000,
:52A:WOOBUS33
:58A:HNBKKRSE
-}
```

---

### MT900: Debit Note (차변 통보)

계좌에서 차감될 때 발생하는 확인 메시지입니다.

#### 필수 태그

| 태그 | 필드명 | 설명 |
|------|--------|------|
| :20: | Transaction Reference | 거래 참조번호 |
| :21: | Related Reference | 관련 참조번호 |
| :25: | Account Identification | 계좌 식별 |
| :32A: | Value Date/Currency/Amount | 결제일/통화/금액 |
| :33B: | Original Amount | 원본 금액 (선택) |

#### MT900 예시

```
{1:F01HNBKKRSEXXX0000000000}
{2:O900HNBKKRSEXXX}
{4:
:20:BOK-900-001
:21:MT202-REF-001
:25:1234567890
:32A:240101KRW50000000,
:}
```

---

### MT910: Credit Note (대변 통보)

계좌에 입금될 때 발생하는 확인 메시지입니다.

#### 필수 태그

| 태그 | 필드명 | 설명 |
|------|--------|------|
| :20: | Transaction Reference | 거래 참조번호 |
| :21: | Related Reference | 관련 참조번호 |
| :25: | Account Identification | 계좌 식별 |
| :32A: | Value Date/Currency/Amount | 결제일/통화/금액 |

---

### MT940: Customer Statement (고객 잔액보고)

고객에게 잔액 내역을 보고하는 메시지입니다.

#### 필수 태그

| 태그 | 필드명 | 설명 |
|------|--------|------|
| :20: | Transaction Reference | 거래 참조번호 |
| :25: | Account Identification | 계좌 식별 |
| :28C: | Statement Number/Sequence Number | 보고 번호 |
| :60F: | Opening Balance | 시작 잔액 |
| :61: | Statement Line | 거래 내역 |
| :62F: | Closing Balance | 종료 잔액 |

#### MT940 예시

```
{1:F01HNBKKRSEXXX0000000000}
{2:I940HNBKKRSEXXX}
{4:
:20:STMT-240101-001
:25:1234567890
:28C:1/1
:60F:C240101KRW1000000000,
:61:2401010103C50000000,NTRFMT103REF001//001
:62F:C240101KRW1500000000,
-}
```

---

### MT950: Statement (은행 잔액보고)

은행 간 잔액 보고에 사용됩니다.

```
{1:F01HNBKKRSEXXX0000000000}
{2:I950HNBKKRSEXXX}
{4:
:20:STMT-950-001
:25:KRW-NOSTRO-001
:28C:1/1
:60F:C240101KRW500000000,
:61:240101C200000000,,NTRFMT202COVER001
:61:240101D50000000,,NTRFMT900DEBIT001
:62F:C240101KRW650000000,
-}
```

---

## BIC 코드 체계

### 구조 (8+3)

```
WOOBURKRSAXXX
│    │     ││ │
│    │     ││ └─ 터미널 (3자리, 선택)
│    │     │└──-location (2자리)
│    │     └──country (2자리, ISO 3166)
│    └─────institution (4자리)
└─────bank (4자리)
```

### 주요 BIC 예시

| 은행 | BIC |
|------|-----|
| 우리은행 | WOOBURKRSAXXX |
| 한국은행 | HNBKKRSEXXX |
| 수출입은행 | EXIKKRSEXXX |
| IMF | IMFKRSEXXX |

---

## 필드 형식 규칙

### 금액 필드 (32A, 33B 등)

```
YYMMDD + Currency(3) + Amount
예: 240101KRW50000000
    │    │   └─ 5천만원
    │    └── KRW (원화)
    └── 2024년 1월 1일
```

### 계좌 번호

- 원화 계좌: 숫자만 (예: /1234567890)
- 외화 계좌: 번호만 (예: /USD123456789)

### 날짜 형식

- YYMMDD (6자리)
- MMDD (4자리, 상대적)
- YYYYMMDD (8자리, 확장)

---

## 검증 규칙

### 필수 필드 체크 (MT103)

- :20: - 필수
- :23B: - 필수
- :32A: - 필수
- :50K: 또는 :50F: - 필수
- :59: - 필수

### 금액 형식 체크

- 통화: ISO 4217 (KRW, USD, CNH, EUR)
- 금액: 정수 (소수점 이하 불가)
- 금액 최대: 금융기관별 상이

### BIC 검증

- 8+3 형식
- 대문자 알파벳과 숫자만 허용
- 국가 코드: ISO 3166

---

## SWIFT 네트워크 품질 기준

| 항목 | 기준 |
|------|------|
| 가용성 | 99.95% |
| 메시지 처리 시간 | 5초 이내 |
| 응답 타임아웃 | 30초 |
| 재시도 횟수 | 3회 |

---

## 관련 문서

- [프로젝트 README](./README.md)
- [BOK 연동 규격](./BOK_Interface_Spec.md)
- [역외원화결제 플로우](./OffshoreKRW_Flow.md)