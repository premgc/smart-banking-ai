from __future__ import annotations

from app.analytics import get_df
from app.retriever import upsert_texts


def row_to_text(row) -> str:
    fields = [
        f"Tran Date: {row.get('Tran Date', '')}",
        f"Particulars: {row.get('Particulars', '')}",
        f"Tran Type: {row.get('Tran Type', '')}",
        f"TxnType: {row.get('TxnType', '')}",
        f"Deposit: {row.get('Deposit', 0)}",
        f"Withdrawal: {row.get('Withdrawal', 0)}",
    ]
    return ' | '.join(fields)


def main() -> None:
    df = get_df()
    texts = [row_to_text(row) for _, row in df.iterrows()]
    count = upsert_texts(texts)
    print(f'Indexed {count} transaction rows into Qdrant.')


if __name__ == '__main__':
    main()
