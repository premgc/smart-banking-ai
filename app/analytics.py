from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from config.settings import CSV_SKIPROWS, DATA_DIR


REQUIRED_LIKE_COLUMNS = ['Tran Date', 'Particulars']


def _find_csv_file() -> Path:
    csv_files = sorted(DATA_DIR.glob('*.csv'))
    if not csv_files:
        raise FileNotFoundError(
            f'No CSV file found in data folder: {DATA_DIR}'
        )
    return csv_files[0]


def load_csv(path: Optional[Path] = None) -> pd.DataFrame:
    csv_path = path or _find_csv_file()
    try:
        return pd.read_csv(csv_path, skiprows=CSV_SKIPROWS)
    except Exception:
        return pd.read_csv(csv_path)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]

    for col in REQUIRED_LIKE_COLUMNS:
        if col not in df.columns:
            raise ValueError(
                f"Expected column '{col}' not found. Available columns: {list(df.columns)}"
            )

    if 'Tran Date' in df.columns:
        df = df[df['Tran Date'].notna()].copy()
        df['Tran Date'] = pd.to_datetime(df['Tran Date'], dayfirst=True, errors='coerce')
        df = df[df['Tran Date'].notna()].copy()

    for col in ['Deposit', 'Withdrawal']:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(',', '', regex=False)
            .str.strip()
            .replace({'': '0', 'nan': '0', 'None': '0', 'NaN': '0'})
        )
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    if 'Particulars' in df.columns:
        df['Particulars'] = df['Particulars'].fillna('').astype(str)

    if 'Tran Type' not in df.columns:
        df['Tran Type'] = ''
    df['Tran Type'] = df['Tran Type'].fillna('').astype(str)

    return df


def extract_transaction_type(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def get_type(row) -> str:
        particulars = str(row.get('Particulars', '')).upper()
        tran_type = str(row.get('Tran Type', '')).upper()

        if 'UPI IN' in particulars:
            return 'UPI_IN'
        if 'UPIOUT' in particulars or 'UPI OUT' in particulars:
            return 'UPI_OUT'
        if 'NEFT' in particulars or tran_type == 'NEFT':
            return 'NEFT'
        if 'IMPS' in particulars or tran_type == 'IMPS':
            return 'IMPS'
        if 'RTGS' in particulars or tran_type == 'RTGS':
            return 'RTGS'
        if 'ATM' in particulars or tran_type == 'ATM':
            return 'ATM'
        if 'CASH' in particulars or tran_type == 'CASH':
            return 'CASH'
        if 'CHRG' in particulars or 'CHARGE' in particulars:
            return 'CHARGES'
        if 'TFR' in particulars or tran_type == 'TFR' or 'TRANSFER' in particulars:
            return 'TRANSFER'
        return 'OTHER'

    df['TxnType'] = df.apply(get_type, axis=1)
    return df


def get_df() -> pd.DataFrame:
    df = load_csv()
    df = clean_dataframe(df)
    df = extract_transaction_type(df)
    return df


def get_daily_summary() -> pd.DataFrame:
    df = get_df()
    summary = (
        df.groupby('Tran Date')[['Deposit', 'Withdrawal']]
        .sum()
        .reset_index()
        .sort_values('Tran Date')
    )
    summary['Profit'] = summary['Deposit'] - summary['Withdrawal']
    return summary


def get_monthly_summary() -> pd.DataFrame:
    df = get_df().copy()
    df['Month'] = df['Tran Date'].dt.to_period('M').astype(str)
    summary = df.groupby('Month')[['Deposit', 'Withdrawal']].sum().reset_index()
    summary['Profit'] = summary['Deposit'] - summary['Withdrawal']
    return summary


def filter_by_date(start_date, end_date) -> pd.DataFrame:
    df = get_df()
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    return df[(df['Tran Date'] >= start) & (df['Tran Date'] <= end)].copy()


def total_deposit() -> float:
    return float(get_df()['Deposit'].sum())


def total_withdrawal() -> float:
    return float(get_df()['Withdrawal'].sum())


def get_upi_deposit_total() -> float:
    df = get_df()
    return float(df[df['TxnType'] == 'UPI_IN']['Deposit'].sum())


def get_upi_withdrawal_total() -> float:
    df = get_df()
    return float(df[df['TxnType'] == 'UPI_OUT']['Withdrawal'].sum())


def get_upi_deposit_daily() -> pd.DataFrame:
    df = get_df()
    df = df[df['TxnType'] == 'UPI_IN']
    return df.groupby('Tran Date')['Deposit'].sum().reset_index().sort_values('Tran Date')


def get_upi_withdrawal_daily() -> pd.DataFrame:
    df = get_df()
    df = df[df['TxnType'] == 'UPI_OUT']
    return df.groupby('Tran Date')['Withdrawal'].sum().reset_index().sort_values('Tran Date')


def get_transaction_daily_summary(txn_type: str) -> pd.DataFrame:
    df = get_df()
    txn_type = str(txn_type).upper().strip()
    if txn_type == 'UPI':
        filtered_df = df[df['TxnType'].isin(['UPI_IN', 'UPI_OUT'])]
    else:
        filtered_df = df[df['TxnType'] == txn_type]

    if filtered_df.empty:
        return pd.DataFrame()

    return (
        filtered_df.groupby('Tran Date')[['Deposit', 'Withdrawal']]
        .sum()
        .reset_index()
        .sort_values('Tran Date')
    )


def get_unique_transaction_types():
    df = get_df()
    return sorted(df['TxnType'].dropna().unique().tolist())


def get_expense_breakdown() -> pd.DataFrame:
    df = get_df()
    out_df = df[df['Withdrawal'] > 0].copy()

    def classify(text: str) -> str:
        value = str(text).lower()
        if 'chicken' in value:
            return 'Chicken'
        if 'fuel' in value:
            return 'Fuel'
        if 'salary' in value or 'labour' in value:
            return 'Salary / Labour'
        if 'atm' in value:
            return 'Cash Withdraw'
        if 'rent' in value:
            return 'Rent'
        if 'rice' in value:
            return 'Raw Material'
        if 'advert' in value:
            return 'Advertising'
        if 'charge' in value or 'chrg' in value:
            return 'Bank Charges'
        return 'Other'

    out_df['Category'] = out_df['Particulars'].apply(classify)
    return (
        out_df.groupby('Category')['Withdrawal']
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )


def get_loss_days() -> pd.DataFrame:
    summary = get_daily_summary()
    return summary[summary['Profit'] < 0].copy()


def export_csv(df: pd.DataFrame) -> bytes:
    export_df = df.copy()
    if 'Tran Date' in export_df.columns:
        export_df['Tran Date'] = export_df['Tran Date'].astype(str)
    return export_df.to_csv(index=False).encode('utf-8')
