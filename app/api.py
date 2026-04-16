from fastapi import FastAPI
from app.analytics import run_analysis

app = FastAPI()

@app.post("/analyze")
def analyze_api(payload: dict):
    query = payload.get("query")
    return run_analysis(query)