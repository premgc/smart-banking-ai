# Smart Banking Assistant

## Folder structure

```text
AI/
├── app/
│   ├── __init__.py
│   ├── analytics.py
│   ├── llm.py
│   ├── main.py
│   ├── prompts.py
│   ├── retriever.py
│   └── utils.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── data/
├── vector_store/
├── .env
├── .env.example
├── ingest.py
├── requirements.txt
└── README.md
```

## Setup

1. Create a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env`.
4. Put your CSV into `data/`.
5. Start Ollama:
   ```bash
   ollama serve
   ollama pull llama3
   ```
6. Ingest data:
   ```bash
   python ingest.py
   ```
7. Run Streamlit:
   ```bash
   streamlit run app/main.py
   ```

## Notes

- `app/main.py` is the Streamlit app.
- `ingest.py` loads the CSV and writes vectors into Qdrant.
- Local Qdrant storage goes into `vector_store/`.
