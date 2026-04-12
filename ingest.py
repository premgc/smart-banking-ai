from app.analytics import get_df
from app.retriever import upsert_texts
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)


def row_to_text(row):
    return f"""
    Date: {row.get('date')}
    Description: {row.get('description')}
    Deposit: {row.get('deposit')}
    Withdrawal: {row.get('withdrawal')}
    """


def main():
    df = get_df()
    texts = [row_to_text(row) for _, row in df.iterrows()]

    count = upsert_texts(texts)

    print(f"Indexed {count} rows to Azure AI Search")


if __name__ == "__main__":
    main()