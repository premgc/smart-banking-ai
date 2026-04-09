from __future__ import annotations

from typing import Callable, Dict, Optional

from app.analytics import (
    get_daily_summary,
    get_expense_breakdown,
    total_deposit,
    total_withdrawal,
    filter_df_by_date,
)
from app.date_utils import parse_date_range
from app.insights import generate_financial_insights


# =========================================================
# HELPERS
# =========================================================
def _fmt_rupee(value: float) -> str:
    return f"₹ {value:,.2f}"


def _safe_df(df):
    return df if df is not None else None


# =========================================================
# CORE TOOLS
# =========================================================
def tool_total_deposit() -> str:
    try:
        value = total_deposit()
        return f"### 💰 Total Deposit\n\n{_fmt_rupee(value)}"
    except Exception as e:
        return f"❌ Error calculating total deposit: {e}"


def tool_total_withdrawal() -> str:
    try:
        value = total_withdrawal()
        return f"### 💸 Total Withdrawal\n\n{_fmt_rupee(value)}"
    except Exception as e:
        return f"❌ Error calculating total withdrawal: {e}"


def tool_expense_breakdown() -> str:
    try:
        df = _safe_df(get_expense_breakdown())

        if df is None or df.empty:
            return "No expense data available."

        lines = ["### 💸 Expense Breakdown", ""]

        for _, row in df.iterrows():
            lines.append(
                f"- **{row['Category']}**: {_fmt_rupee(float(row['Withdrawal']))}"
            )

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Error generating expense breakdown: {e}"


def tool_daily_summary() -> str:
    try:
        df = _safe_df(get_daily_summary())

        if df is None or df.empty:
            return "No daily summary available."

        lines = ["### 📊 Daily Summary", ""]

        for _, row in df.head(20).iterrows():
            lines.append(
                f"- {row['Tran Date'].strftime('%d-%b-%Y')} → "
                f"Deposit {_fmt_rupee(float(row['Deposit']))}, "
                f"Withdrawal {_fmt_rupee(float(row['Withdrawal']))}, "
                f"Profit {_fmt_rupee(float(row['Profit']))}"
            )

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Error generating daily summary: {e}"


# =========================================================
# FINANCIAL INSIGHTS TOOL
# =========================================================
def tool_financial_insights() -> str:
    try:
        return generate_financial_insights()
    except Exception as e:
        return f"❌ Error generating financial insights: {e}"


# =========================================================
# DATE FILTERING TOOL
# =========================================================
def tool_filtered_summary(query: str) -> str:
    try:
        start, end = parse_date_range(query)

        if not start or not end:
            return (
                "❌ Could not understand date range.\n\n"
                "Try examples:\n"
                "- last 7 days\n"
                "- this month\n"
                "- March\n"
                "- last 30 days"
            )

        df = _safe_df(get_daily_summary())

        if df is None or df.empty:
            return "No transaction data available."

        df = filter_df_by_date(df, start, end)

        if df.empty:
            return f"No data found between {start.date()} and {end.date()}."

        total_dep = float(df["Deposit"].sum())
        total_wd = float(df["Withdrawal"].sum())
        net = total_dep - total_wd

        lines = [
            f"### 📅 Filtered Summary ({start.date()} → {end.date()})",
            "",
            f"**Total Deposit:** {_fmt_rupee(total_dep)}",
            f"**Total Withdrawal:** {_fmt_rupee(total_wd)}",
            f"**Net:** {_fmt_rupee(net)}",
            "",
        ]

        for _, row in df.iterrows():
            lines.append(
                f"- {row['Tran Date'].strftime('%d-%b-%Y')} → "
                f"Deposit {_fmt_rupee(float(row['Deposit']))}, "
                f"Withdrawal {_fmt_rupee(float(row['Withdrawal']))}"
            ) 

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Error in date filtering: {e}"


# =========================================================
# TOOL REGISTRY
# =========================================================
TOOLS: Dict[str, Callable[..., str]] = {
    "total_deposit": tool_total_deposit,
    "total_withdrawal": tool_total_withdrawal,
    "expense_breakdown": tool_expense_breakdown,
    "daily_summary": tool_daily_summary,
    "financial_insights": tool_financial_insights,
    "filtered_summary": tool_filtered_summary,
}