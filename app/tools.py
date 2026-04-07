from app.analytics import (
    get_daily_summary,
    get_expense_breakdown,
    total_deposit,
    total_withdrawal,
)
from app.insights import generate_financial_insights


def tool_total_deposit() -> str:
    return f"Total deposit is ₹ {total_deposit():,.2f}"


def tool_total_withdrawal() -> str:
    return f"Total withdrawal is ₹ {total_withdrawal():,.2f}"


def tool_expense_breakdown() -> str:
    df = get_expense_breakdown()
    if df.empty:
        return "No expense data available."

    lines = ["### Expense Breakdown", ""]
    for _, row in df.iterrows():
        lines.append(f"- {row['Category']}: ₹ {row['Withdrawal']:,.2f}")
    return "\n".join(lines)


def tool_daily_summary() -> str:
    df = get_daily_summary()
    if df.empty:
        return "No daily summary available."

    lines = ["### Daily Summary", ""]
    for _, row in df.head(10).iterrows():
        lines.append(
            f"- {row['Tran Date'].strftime('%d-%b-%Y')}: "
            f"Deposit ₹ {row['Deposit']:,.2f}, "
            f"Withdrawal ₹ {row['Withdrawal']:,.2f}, "
            f"Profit ₹ {row['Profit']:,.2f}"
        )
    return "\n".join(lines)


def tool_financial_insights() -> str:
    return generate_financial_insights()


TOOLS = {
    "total_deposit": tool_total_deposit,
    "total_withdrawal": tool_total_withdrawal,
    "expense_breakdown": tool_expense_breakdown,
    "daily_summary": tool_daily_summary,
    "financial_insights": tool_financial_insights,
}