from __future__ import annotations

from app.analytics import (
    get_daily_summary,
    get_expense_breakdown,
    get_loss_days,
    total_deposit,
    total_withdrawal,
)


def _fmt_rupee(value: float) -> str:
    return f"₹ {value:,.2f}"


def generate_financial_insights() -> str:
    daily_df = get_daily_summary()
    expense_df = get_expense_breakdown()
    loss_df = get_loss_days()

    if daily_df.empty:
        return "No transaction data available to generate insights."

    total_dep = float(total_deposit())
    total_wd = float(total_withdrawal())
    net_profit = total_dep - total_wd

    total_days = len(daily_df)
    loss_days_count = len(loss_df)
    avg_daily_profit = net_profit / total_days if total_days else 0.0

    highest_spend_day = None
    highest_deposit_day = None

    if "Withdrawal" in daily_df.columns and not daily_df.empty:
        highest_spend_row = daily_df.loc[daily_df["Withdrawal"].idxmax()]
        highest_spend_day = (
            highest_spend_row["Tran Date"].strftime("%d-%b-%Y"),
            float(highest_spend_row["Withdrawal"]),
        )

    if "Deposit" in daily_df.columns and not daily_df.empty:
        highest_deposit_row = daily_df.loc[daily_df["Deposit"].idxmax()]
        highest_deposit_day = (
            highest_deposit_row["Tran Date"].strftime("%d-%b-%Y"),
            float(highest_deposit_row["Deposit"]),
        )

    top_expenses = []
    if not expense_df.empty:
        for _, row in expense_df.head(3).iterrows():
            top_expenses.append((str(row["Category"]), float(row["Withdrawal"])))

    lines: list[str] = []
    lines.append("## Financial Insights")
    lines.append("")
    lines.append(f"- **Total Deposit:** {_fmt_rupee(total_dep)}")
    lines.append(f"- **Total Withdrawal:** {_fmt_rupee(total_wd)}")
    lines.append(f"- **Net Position:** {_fmt_rupee(net_profit)}")
    lines.append(f"- **Average Daily Profit/Loss:** {_fmt_rupee(avg_daily_profit)}")
    lines.append(f"- **Loss Days:** {loss_days_count} out of {total_days} day(s)")
    lines.append("")

    if highest_spend_day:
        lines.append(
            f"- **Highest Spending Day:** {highest_spend_day[0]} "
            f"({_fmt_rupee(highest_spend_day[1])})"
        )

    if highest_deposit_day:
        lines.append(
            f"- **Highest Deposit Day:** {highest_deposit_day[0]} "
            f"({_fmt_rupee(highest_deposit_day[1])})"
        )

    if top_expenses:
        lines.append("")
        lines.append("### Top Expense Categories")
        lines.append("")
        for category, amount in top_expenses:
            lines.append(f"- **{category}:** {_fmt_rupee(amount)}")

    lines.append("")
    lines.append("### Where You May Be Losing Money")
    lines.append("")

    if top_expenses:
        for category, amount in top_expenses:
            lines.append(
                f"- High outflow in **{category}** is contributing to overall cash reduction."
            )
    else:
        lines.append("- No strong expense categories were detected from the available data.")

    if loss_days_count > 0:
        lines.append(
            f"- You had **{loss_days_count} loss day(s)** where withdrawals exceeded deposits."
        )
    else:
        lines.append("- Good sign: no loss days were detected.")

    if net_profit < 0:
        lines.append("- Overall, your account is running at a **net loss** in this dataset.")
    else:
        lines.append("- Overall, your account is still in **net positive** position.")

    lines.append("")
    lines.append("### Recommendations")
    lines.append("")

    if any(cat.lower() == "bank charges" for cat, _ in top_expenses):
        lines.append("- Reduce frequent chargeable transfers to cut bank fees.")

    if any("cash" in cat.lower() for cat, _ in top_expenses):
        lines.append("- Review cash withdrawals and see if digital payments can reduce leakage.")

    if loss_days_count > max(3, total_days * 0.3):
        lines.append(
            "- Too many loss days detected. Review daily spending discipline and recurring outflows."
        )

    if avg_daily_profit < 0:
        lines.append("- Daily average is negative. You may need to reduce fixed and recurring expenses.")
    else:
        lines.append("- Daily average is positive, but trimming high-expense categories can improve savings.")

    return "\n".join(lines)
