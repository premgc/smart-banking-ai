from __future__ import annotations

import os
from io import StringIO
from typing import List
from pathlib import Path

import pandas as pd
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv


# =========================================================
# LOAD ENV (🔥 FIX)
# =========================================================
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


# =========================================================
# CONFIG (ENV VARIABLES)
# =========================================================
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER", "smart-banking-aid")
AZURE_BLOB_NAME = os.getenv("AZURE_BLOB_NAME", "statement.csv")


# =========================================================
# LOAD CSV FROM AZURE BLOB
# =========================================================
def load_csv_from_blob() -> pd.DataFrame:
    try:
        if not AZURE_STORAGE_CONNECTION_STRING:
            raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING not set")

        blob_service = BlobServiceClient.from_connection_string(
            AZURE_STORAGE_CONNECTION_STRING
        )

        container_client = blob_service.get_container_client(AZURE_STORAGE_CONTAINER)

        # 🔍 DEBUG (safe)
        blobs = [b.name for b in container_client.list_blobs()]
        print(f"Available blobs: {blobs}")

        if AZURE_BLOB_NAME not in blobs:
            raise RuntimeError(f"Blob '{AZURE_BLOB_NAME}' not found in container")

        blob_client = blob_service.get_blob_client(
            container=AZURE_STORAGE_CONTAINER,
            blob=AZURE_BLOB_NAME,
        )

        data = blob_client.download_blob().readall().decode("utf-8")

        # 🔥 AUTO-DETECT HEADER ROW
        for i in range(0, 30):
            df = pd.read_csv(StringIO(data), skiprows=i)

            if "Tran Date" in df.columns:
                print(f"✅ Header detected at row: {i}")
                return df

        raise RuntimeError("❌ Could not detect header row (Tran Date not found)")

    except Exception as e:
        raise RuntimeError(f"❌ Failed to load CSV from Azure Blob: {e}")


# =========================================================
# CLEANING LOGIC
# =========================================================
REQUIRED_LIKE_COLUMNS = ["Tran Date", "Particulars"]


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]

    for col in REQUIRED_LIKE_COLUMNS:
        if col not in df.columns:
            raise ValueError(
                f"Expected column '{col}' not found. Available columns: {list(df.columns)}"
            )

    # Date cleaning
    df["Tran Date"] = pd.to_datetime(
        df["Tran Date"], dayfirst=True, errors="coerce"
    )
    df = df[df["Tran Date"].notna()].copy()

    # Numeric columns
    for col in ["Deposit", "Withdrawal"]:
        if col not in df.columns:
            df[col] = 0.0

        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
            .replace({"": "0", "nan": "0", "None": "0", "NaN": "0"})
        )

        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["Particulars"] = df["Particulars"].fillna("").astype(str)

    if "Tran Type" not in df.columns:
        df["Tran Type"] = ""

    df["Tran Type"] = df["Tran Type"].fillna("").astype(str)

    return df


# =========================================================
# TRANSACTION TYPE EXTRACTION
# =========================================================
def extract_transaction_type(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def get_type(row) -> str:
        particulars = str(row.get("Particulars", "")).upper()
        tran_type = str(row.get("Tran Type", "")).upper()

        if "UPI IN" in particulars:
            return "UPI_IN"
        if "UPI OUT" in particulars or "UPIOUT" in particulars:
            return "UPI_OUT"
        if "NEFT" in particulars or tran_type == "NEFT":
            return "NEFT"
        if "IMPS" in particulars or tran_type == "IMPS":
            return "IMPS"
        if "RTGS" in particulars or tran_type == "RTGS":
            return "RTGS"
        if "ATM" in particulars:
            return "ATM"
        if "CASH" in particulars:
            return "CASH"
        if "CHRG" in particulars or "CHARGE" in particulars:
            return "CHARGES"
        if "TFR" in particulars or "TRANSFER" in particulars:
            return "TRANSFER"
        return "OTHER"

    df["TxnType"] = df.apply(get_type, axis=1)
    return df


# =========================================================
# MAIN DATAFRAME ENTRY POINT
# =========================================================
def get_df() -> pd.DataFrame:
    df = load_csv_from_blob()
    df = clean_dataframe(df)
    df = extract_transaction_type(df)
    return df


# =========================================================
# ANALYTICS FUNCTIONS
# =========================================================
def get_daily_summary() -> pd.DataFrame:
    df = get_df()
    summary = (
        df.groupby("Tran Date")[["Deposit", "Withdrawal"]]
        .sum()
        .reset_index()
        .sort_values("Tran Date")
    )
    summary["Profit"] = summary["Deposit"] - summary["Withdrawal"]
    return summary


def total_deposit() -> float:
    return float(get_df()["Deposit"].sum())


def total_withdrawal() -> float:
    return float(get_df()["Withdrawal"].sum())