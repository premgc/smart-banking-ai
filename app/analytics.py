from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path
from typing import Optional

import pandas as pd
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from pathlib import Path



# =========================================================
# LOAD ENV (ROBUST)
# =========================================================
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER", "smart-banking-aid")
AZURE_BLOB_NAME = os.getenv("AZURE_BLOB_NAME", "statement.csv")

# =========================================================
# VALIDATION
# =========================================================
if not AZURE_STORAGE_CONNECTION_STRING:
    raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING not set")

# =========================================================
# LOAD CSV FROM AZURE BLOB
# =========================================================
def load_csv_from_blob() -> pd.DataFrame:
    try:
        blob_service = BlobServiceClient.from_connection_string(
            AZURE_STORAGE_CONNECTION_STRING
        )
        container_client = blob_service.get_container_client(AZURE_STORAGE_CONTAINER)
        blob_client = container_client.get_blob_client(AZURE_BLOB_NAME)

        blob_data = blob_client.download_blob().readall()

        df = pd.read_csv(BytesIO(blob_data), encoding="utf-8", low_memory=False)

        return df

    except Exception as e:
        raise RuntimeError(f"❌ Failed to load CSV from Azure Blob: {e}")

# =========================================================
# CLEAN DATAFRAME
# =========================================================
def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip() for c in df.columns]

    # Normalize columns (adapt if needed)
    column_map = {
        "Tran Date": "date",
        "Value Date": "value_date",
        "Particulars": "description",
        "Withdrawal": "withdrawal",
        "Deposit": "deposit",
    }

    df = df.rename(columns=column_map)

    # Convert numbers
    for col in ["withdrawal", "deposit"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Convert date
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df

# =========================================================
# MAIN DATA ACCESS
# =========================================================
_df_cache: Optional[pd.DataFrame] = None

def get_df(force_reload: bool = False) -> pd.DataFrame:
    global _df_cache

    if _df_cache is not None and not force_reload:
        return _df_cache

    df = load_csv_from_blob()
    df = clean_dataframe(df)

    _df_cache = df
    return df

# =========================================================
# BUSINESS LOGIC FUNCTIONS
# =========================================================

def total_deposit() -> str:
    df = get_df()
    total = df["deposit"].sum()
    return f"💰 Total deposits: ₹ {total:,.2f}"

def total_withdrawal() -> str:
    df = get_df()
    total = df["withdrawal"].sum()
    return f"💸 Total withdrawals: ₹ {total:,.2f}"

def expense_breakdown() -> str:
    df = get_df()

    top = (
        df.groupby("description")["withdrawal"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )

    result = "📊 Top Expenses:\n\n"
    for k, v in top.items():
        result += f"- {k}: ₹ {v:,.2f}\n"

    return result

def daily_summary() -> str:
    df = get_df()

    summary = (
        df.groupby(df["date"].dt.date)[["deposit", "withdrawal"]]
        .sum()
        .tail(5)
    )

    result = "📅 Last 5 Days Summary:\n\n"
    for idx, row in summary.iterrows():
        result += f"{idx} → Deposit: ₹ {row['deposit']:,.2f}, Withdrawal: ₹ {row['withdrawal']:,.2f}\n"

    return result

def financial_insights() -> str:
    df = get_df()

    total_dep = df["deposit"].sum()
    total_wd = df["withdrawal"].sum()

    if total_dep == 0:
        return "⚠️ No deposits found."

    savings_rate = (total_dep - total_wd) / total_dep * 100

    return (
        f"📈 Financial Insights:\n\n"
        f"- Total Deposit: ₹ {total_dep:,.2f}\n"
        f"- Total Withdrawal: ₹ {total_wd:,.2f}\n"
        f"- Savings Rate: {savings_rate:.2f}%\n"
    )

def filtered_summary(query: str) -> str:
    df = get_df()

    # very basic filter logic
    query_lower = query.lower()

    if "upi" in query_lower:
        filtered = df[df["description"].str.contains("upi", case=False, na=False)]
    elif "atm" in query_lower:
        filtered = df[df["description"].str.contains("atm", case=False, na=False)]
    else:
        filtered = df

    total = filtered["withdrawal"].sum()

    return f"🔍 Filtered Summary:\nTotal withdrawal: ₹ {total:,.2f}"

# =========================================================
# TOOL MAP (USED BY AGENT)
# =========================================================
TOOLS = {
    "total_deposit": total_deposit,
    "total_withdrawal": total_withdrawal,
    "expense_breakdown": expense_breakdown,
    "daily_summary": daily_summary,
    "financial_insights": financial_insights,
    "filtered_summary": filtered_summary,
}

def run_analysis(query: str):
    """
    Simple analysis placeholder for MCP integration
    """

    if not query:
        return {"message": "No query provided"}

    # Dummy response (replace later with real logic)
    return {
        "status": "success",
        "query": query,
        "insight": f"Analysis result for: {query}"
    }