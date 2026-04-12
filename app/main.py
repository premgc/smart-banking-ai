from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.agent import run_agent
from app.analytics import (
    get_daily_summary,
    get_expense_breakdown,
    get_loss_days,
    get_transaction_daily_summary,
    get_unique_transaction_types,
    get_upi_deposit_daily,
    get_upi_deposit_total,
    get_upi_withdrawal_daily,
    get_upi_withdrawal_total,
    total_deposit,
    total_withdrawal,
)
from app.llm import check_openai_health
from app.retriever import health_check as retriever_health_check


# =========================================================
# LOGGING
# =========================================================
logger = logging.getLogger("main")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


# =========================================================
# PAGE SETUP
# =========================================================
st.set_page_config(
    page_title="Smart Banking Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("🏦 Smart Banking Assistant")
st.caption("Azure OpenAI powered banking insights assistant")


# =========================================================
# HELPERS
# =========================================================
def detect_txn_type(query: str) -> Optional[str]:
    q = str(query).lower().strip()
    mapping = {
        "upi": "UPI",
        "neft": "NEFT",
        "imps": "IMPS",
        "rtgs": "RTGS",
        "cash": "CASH",
        "atm": "ATM",
        "transfer": "TRANSFER",
        "tfr": "TRANSFER",
        "charge": "CHARGES",
        "charges": "CHARGES",
    }
    for key, value in mapping.items():
        if key in q:
            return value
    return None


def format_daywise_summary(df, title: str) -> str:
    if df is None or df.empty:
        return f"❌ No data found for {title}."

    lines = [f"### {title}", ""]
    for _, row in df.iterrows():
        date_value = row.get("Tran Date")
        date_str = (
            date_value.strftime("%d-%b-%Y")
            if hasattr(date_value, "strftime")
            else str(date_value)
        )
        deposit = float(row.get("Deposit", 0) or 0)
        withdrawal = float(row.get("Withdrawal", 0) or 0)

        lines.append(
            f"- **{date_str}** → Deposit ₹ {deposit:,.2f} | Withdrawal ₹ {withdrawal:,.2f}"
        )

    return "\n".join(lines)


def format_single_column_daywise(df, title: str, value_col: str, emoji: str) -> str:
    if df is None or df.empty:
        return f"❌ No data found for {title}."

    lines = [f"### {title}", ""]
    for _, row in df.iterrows():
        date_value = row.get("Tran Date")
        date_str = (
            date_value.strftime("%d-%b-%Y")
            if hasattr(date_value, "strftime")
            else str(date_value)
        )
        value = float(row.get(value_col, 0) or 0)
        lines.append(f"- **{date_str}** → {emoji} ₹ {value:,.2f}")

    return "\n".join(lines)


def safe_agent_response(user_query: str) -> str:
    try:
        answer = run_agent(user_query)
        if not answer or not str(answer).strip():
            return "⚠️ No response generated. Try a more specific query."
        return str(answer)
    except Exception as e:
        logger.exception("Agent execution failed")
        return f"❌ Error while processing your request: {e}"


# =========================================================
# SIDEBAR HEALTH CHECK
# =========================================================
with st.sidebar:
    st.subheader("System Health")

    try:
        openai_ok, openai_msg = check_openai_health()
    except Exception as e:
        openai_ok, openai_msg = False, f"Health check failed: {e}"
        logger.exception("Azure OpenAI health check failed")

    try:
        vector_ok, vector_msg = retriever_health_check()
    except Exception as e:
        vector_ok, vector_msg = False, f"Vector DB health check failed: {e}"
        logger.exception("Retriever health check failed")

    st.write(f"**Azure OpenAI:** {'✅' if openai_ok else '❌'} {openai_msg}")
    st.write(f"**Vector DB:** {'✅' if vector_ok else '❌'} {vector_msg}")
    st.caption("For Azure deployment, configure app settings and vector store correctly.")


# =========================================================
# DASHBOARD
# =========================================================
st.subheader("📊 Dashboard")

try:
    daily = get_daily_summary().copy()

    deposit_total = float(total_deposit())
    withdrawal_total = float(total_withdrawal())
    profit_total = deposit_total - withdrawal_total

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Deposit", f"₹ {deposit_total:,.2f}")
    c2.metric("💸 Withdrawal", f"₹ {withdrawal_total:,.2f}")
    c3.metric("📈 Profit", f"₹ {profit_total:,.2f}")

    if not daily.empty:
        chart_df = daily.copy()
        chart_df["Tran Date"] = chart_df["Tran Date"].astype(str)

        st.line_chart(
            chart_df.set_index("Tran Date")[["Deposit", "Withdrawal", "Profit"]]
        )

    with st.expander("📅 Daily Breakdown"):
        if not daily.empty:
            display_daily = daily.copy()
            display_daily["Tran Date"] = display_daily["Tran Date"].astype(str)
            st.dataframe(display_daily, use_container_width=True)
        else:
            st.info("No daily transaction data available.")

    with st.expander("💸 Expense Breakdown"):
        expense_df = get_expense_breakdown().copy()
        if not expense_df.empty:
            st.dataframe(expense_df, use_container_width=True)
        else:
            st.info("No expense breakdown available.")

    with st.expander("⚠️ Loss Days"):
        loss_df = get_loss_days().copy()
        if not loss_df.empty:
            loss_df["Tran Date"] = loss_df["Tran Date"].astype(str)
            st.dataframe(loss_df, use_container_width=True)
        else:
            st.success("No loss days found.")

except Exception as e:
    logger.exception("Dashboard rendering failed")
    st.warning(f"Dashboard error: {e}")


# =========================================================
# CHAT SECTION
# =========================================================
st.subheader("💬 Ask your data")

if "chat" not in st.session_state:
    st.session_state.chat = []

for role, msg in st.session_state.chat:
    with st.chat_message(role):
        st.markdown(msg)

query = st.chat_input("Ask about your transactions...")

if query:
    st.session_state.chat.append(("user", query))

    with st.chat_message("user"):
        st.markdown(query)

    q = str(query).lower().strip()

    try:
        if "day" in q and "upi" in q and "deposit" in q:
            answer = format_single_column_daywise(
                get_upi_deposit_daily(),
                "📅 Day-wise UPI Deposit",
                "Deposit",
                "💰",
            )

        elif "day" in q and "upi" in q and ("withdraw" in q or "debit" in q):
            answer = format_single_column_daywise(
                get_upi_withdrawal_daily(),
                "📅 Day-wise UPI Withdrawal",
                "Withdrawal",
                "💸",
            )

        elif "day" in q:
            txn_type = detect_txn_type(q)

            if txn_type:
                answer = format_daywise_summary(
                    get_transaction_daily_summary(txn_type),
                    f"📅 Day-wise {txn_type} Summary",
                )
            else:
                available = ", ".join(get_unique_transaction_types())
                answer = (
                    "❌ Please specify a transaction type.\n\n"
                    f"Available types: {available}"
                )

        elif "upi deposit" in q:
            answer = f"### 💰 Total UPI Deposit\n\n₹ {get_upi_deposit_total():,.2f}"

        elif "upi withdrawal" in q or "upi debit" in q:
            answer = (
                f"### 💸 Total UPI Withdrawal\n\n₹ {get_upi_withdrawal_total():,.2f}"
            )

        elif "total deposit" in q:
            answer = f"### 💰 Total Deposit\n\n₹ {total_deposit():,.2f}"

        elif "total withdrawal" in q or "total debit" in q:
            answer = f"### 💸 Total Withdrawal\n\n₹ {total_withdrawal():,.2f}"

        elif (
            "transaction types" in q
            or "transaction codes" in q
            or "unique transaction types" in q
        ):
            txn_types = get_unique_transaction_types()
            answer = "### 📋 Available Transaction Types\n\n" + "\n".join(
                [f"- {t}" for t in txn_types]
            )

        elif (
            "financial insights" in q
            or "where am i losing money" in q
            or "money leak" in q
            or "money leaks" in q
            or "financial health" in q
            or "recommendation" in q
            or "recommendations" in q
            or "last 7 days" in q
            or "last 30 days" in q
            or "this month" in q
            or "january" in q
            or "february" in q
            or "march" in q
            or "april" in q
            or "may" in q
            or "june" in q
            or "july" in q
            or "august" in q
            or "september" in q
            or "october" in q
            or "november" in q
            or "december" in q
        ):
            answer = safe_agent_response(query)

        else:
            answer = safe_agent_response(query)

        if not answer or not str(answer).strip():
            answer = "⚠️ No response generated. Try a more specific query."

    except Exception as e:
        logger.exception("Chat processing failed")
        answer = f"❌ {e}"

    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.chat.append(("assistant", answer))