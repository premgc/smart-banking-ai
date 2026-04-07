from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

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
from app.llm import check_ollama_health, generate_response
from app.prompts import SMART_BANKING_PROMPT
from app.retriever import health_check as retriever_health_check
from app.retriever import search


st.set_page_config(page_title="Smart Banking Assistant", layout="wide")
st.title("🏦 Smart Banking Assistant")


def detect_txn_type(query: str) -> str | None:
    q = query.lower().strip()
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
        date_str = row["Tran Date"].strftime("%d-%b-%Y")
        deposit = row.get("Deposit", 0)
        withdrawal = row.get("Withdrawal", 0)
        lines.append(
            f"- **{date_str}** → Deposit ₹ {deposit:,.2f} | Withdrawal ₹ {withdrawal:,.2f}"
        )
    return "\n".join(lines)


def format_single_column_daywise(df, title: str, value_col: str, emoji: str) -> str:
    if df is None or df.empty:
        return f"❌ No data found for {title}."

    lines = [f"### {title}", ""]
    for _, row in df.iterrows():
        date_str = row["Tran Date"].strftime("%d-%b-%Y")
        value = row[value_col]
        lines.append(f"- **{date_str}** → {emoji} ₹ {value:,.2f}")
    return "\n".join(lines)


def safe_rag_answer(query: str) -> str:
    is_ollama_ok, ollama_msg = check_ollama_health()
    if not is_ollama_ok:
        return f"❌ {ollama_msg}"

    is_qdrant_ok, qdrant_msg = retriever_health_check()
    if not is_qdrant_ok:
        return f"❌ {qdrant_msg}"

    docs = search(query, limit=8)
    context = "\n\n".join(docs) if docs else "No matching data found."
    prompt = SMART_BANKING_PROMPT.format(context=context, question=query)
    return generate_response(prompt)


with st.sidebar:
    st.subheader("System Health")
    ollama_ok, ollama_msg = check_ollama_health()
    qdrant_ok, qdrant_msg = retriever_health_check()
    st.write(f"**Ollama:** {'✅' if ollama_ok else '❌'} {ollama_msg}")
    st.write(f"**Qdrant:** {'✅' if qdrant_ok else '❌'} {qdrant_msg}")
    st.caption("Run: ollama serve, then python ingest.py")

st.subheader("📊 Dashboard")

try:
    daily = get_daily_summary().copy()

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Deposit", f"₹ {total_deposit():,.2f}")
    c2.metric("💸 Withdrawal", f"₹ {total_withdrawal():,.2f}")
    c3.metric("📈 Profit", f"₹ {(total_deposit() - total_withdrawal()):,.2f}")

    chart_df = daily.copy()
    chart_df["Tran Date"] = chart_df["Tran Date"].astype(str)
    st.line_chart(chart_df.set_index("Tran Date")[["Deposit", "Withdrawal", "Profit"]])

    with st.expander("📅 Daily Breakdown"):
        display_daily = daily.copy()
        display_daily["Tran Date"] = display_daily["Tran Date"].astype(str)
        st.dataframe(display_daily, use_container_width=True)

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
    st.warning(f"Dashboard error: {e}")

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

    try:
        q = query.lower().strip()

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
        ):
            answer = run_agent(query)

        else:
            answer = run_agent(query)

        if not answer or not str(answer).strip():
            answer = "⚠️ No response generated. Please try a more specific query."

    except Exception as e:
        answer = f"❌ {e}"

    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.chat.append(("assistant", answer))