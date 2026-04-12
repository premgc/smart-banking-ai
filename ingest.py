from app.analytics import get_df
from app.retriever import upsert_texts


def row_to_text(row) -> str:
    return f"""
    Date: {row['Tran Date']}
    Description: {row['Particulars']}
    Deposit: {row['Deposit']}
    Withdrawal: {row['Withdrawal']}
    """


def main():
    df = get_df()
    texts = [row_to_text(row) for _, row in df.iterrows()]

    count = upsert_texts(texts)

    print(f"Indexed {count} rows to Azure AI Search")


if __name__ == "__main__":
    main()