import streamlit as st
from datetime import datetime
from decimal import Decimal

from src.flow.payment_flow import OffshoreKRWPaymentFlow
from src.flow.exchange_processor import ExchangeRateProcessor
from src.cutoff.manager import CutOffTimeManager
from src.bok_simulator.scenarios import ScenarioEngine
from src.parser.block_parser import SWIFTBlockParser
from src.parser.tag_parser import TagParser

st.set_page_config(page_title="역외원화결제 SWIFT 모니터링 대시보드", layout="wide")

if "payment_flow" not in st.session_state:
    st.session_state.payment_flow = OffshoreKRWPaymentFlow()
if "simulated_messages" not in st.session_state:
    st.session_state.simulated_messages = []
if "bok_status" not in st.session_state:
    st.session_state.bok_status = "정상"


def simulate_mt103(ref: str, amount: str):
    mt103 = f"""{{1:F01WOOBURKRSAXXX0000000000}}
{{2:I103HNBKKRSEXXX}}
{{3:{{108:{ref}}}}}
{{4:
:20:{ref}
:23B:CRED
:32A:240101KRW{amount},
:50K:/123456789
WOORI BANK SEOUL
:57A:HNBKKRSE
:59:/987654321
KOREA BANK COUNTRY PARTY
:70:OFFSHORE KRW PAYMENT TEST
:71A:SHA
-}}"""
    result = st.session_state.payment_flow.process(mt103)
    st.session_state.simulated_messages.append({
        "ref": ref,
        "amount": amount,
        "status": result.status.value,
        "time": datetime.now().strftime("%H:%M:%S"),
        "msg_count": len(result.all_messages),
        "errors": result.errors,
    })


st.title("역외원화결제 SWIFT 모니터링 대시보드")

col1, col2, col3 = st.columns(3)

flow = st.session_state.payment_flow
audit_logs = flow.audit_logger.get_logs()

total_inbound = len([l for l in audit_logs if l.direction == "INBOUND"])
total_outbound = len([l for l in audit_logs if l.direction == "OUTBOUND"])
mt103_count = len([l for l in audit_logs if l.mt_type == "MT103"])
mt202_count = len([l for l in audit_logs if l.mt_type == "MT202"])
completed = len([l for l in audit_logs if l.status in ("SETTLED", "SENT", "RECEIVED")])
errors_count = len([l for l in audit_logs if l.status in ("ERROR", "REJECTED")])

with col1:
    st.subheader("수신 전문")
    st.metric("MT103", mt103_count)
    st.metric("MT202", mt202_count)
    st.metric("기타", total_inbound - mt103_count - mt202_count)

with col2:
    st.subheader("처리 중")
    pending = len([l for l in audit_logs if l.status == "PROCESSING"])
    waiting = len([l for l in audit_logs if l.status == "PENDING_BOK"])
    st.metric("대기", pending + waiting)
    st.metric("오류", errors_count)
    st.metric("중복", len([l for l in audit_logs if l.status == "DUPLICATE"]))

with col3:
    st.subheader("완료 / 오류")
    st.metric("완료", completed)
    st.metric("거부", errors_count)
    total = total_inbound + total_outbound
    st.metric("전체", total)

with st.expander("전문 송수신 입력", expanded=True):
    sim_col1, sim_col2, sim_col3 = st.columns([3, 3, 1])
    with sim_col1:
        ref = st.text_input("참조번호", "TEST-REF-" + datetime.now().strftime("%H%M%S"))
    with sim_col2:
        amount = st.text_input("금액 (KRW)", "50000000")
    with sim_col3:
        if st.button("전송", type="primary"):
            simulate_mt103(ref, amount)
            st.rerun()

st.subheader("실시간 전문 플로우")
flow_col1, flow_col2 = st.columns([2, 1])

with flow_col1:
    st.markdown(
        f"""
    ```
    [MT103] ──> [VALIDATE] ──> [BOK_SEND] ──> [SETTLE]
                 └──> [ERROR] ──> [REPAIR_Q]
    현재 상태: {flow.status.current_status.value}
    ```
    """
    )

    if st.session_state.simulated_messages:
        st.dataframe(
            st.session_state.simulated_messages,
            column_config={
                "time": "시간",
                "ref": "참조번호",
                "amount": "금액",
                "status": "상태",
                "msg_count": "생성 메시지",
                "errors": "오류",
            },
            use_container_width=True,
            hide_index=True,
        )

with flow_col2:
    st.subheader("BOK 연동 상태")
    status_color = "🟢" if st.session_state.bok_status == "정상" else "🔴"
    st.markdown(f"### {status_color} {st.session_state.bok_status}")

    cutoff = CutOffTimeManager()
    for ptype in ["BOK_KRW_OFFSHORE", "BOK_KRW_DOMESTIC", "SWIFT_DAILY"]:
        try:
            c = cutoff.check_cutoff(ptype)
            label = {"BOK_KRW_DOMESTIC": "BOK 원화 국내", "BOK_KRW_OFFSHORE": "BOK 역외원화", "SWIFT_DAILY": "SWIFT 일일 마감"}
            st.markdown(f"**{label[ptype]}**: {'🟢' if c.is_within else '🔴'} 잔여 {c.remaining_minutes}분")
        except Exception:
            pass

    if st.button("연동 재시작"):
        st.session_state.bok_status = "정상"
        st.rerun()

with st.expander("예외 전문 Repair Queue", expanded=False):
    engine = ScenarioEngine()
    repair = engine.get_repair_queue()
    if repair:
        st.dataframe(repair, use_container_width=True)
    else:
        st.info("Repair Queue가 비어 있습니다.")

    if st.button("Repair Queue 초기화"):
        engine.clear_repair_queue()
        st.rerun()

with st.expander("감사 로그", expanded=False):
    logs = audit_logs
    if logs:
        log_data = [
            {
                "시간": l.timestamp[-12:-7] if len(l.timestamp) > 12 else l.timestamp,
                "방향": l.direction,
                "유형": l.mt_type,
                "참조번호": l.reference,
                "상태": l.status,
            }
            for l in logs[-20:]
        ]
        st.dataframe(log_data, use_container_width=True, hide_index=True)
    else:
        st.info("로그가 없습니다.")

st.caption(f"OWP-Simulator v1.0.0 | 마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
