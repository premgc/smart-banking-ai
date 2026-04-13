from __future__ import annotations

import logging

from llm import check_openai_health, generate_response
from prompts import SMART_BANKING_PROMPT
from retriever import health_check as retriever_health_check
from retriever import search
from tools import TOOLS


# =========================================================
# LOGGER (PRODUCTION READY)
# =========================================================
logger = logging.getLogger("agent")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


# =========================================================
# SYSTEM PROMPT (AGENT BRAIN)
# =========================================================
SYSTEM_PROMPT = """
You are a smart banking assistant.

You can either:
1. Call a tool
2. Use retrieved transaction data (rag)

Available tools:
- total_deposit
- total_withdrawal
- expense_breakdown
- daily_summary
- financial_insights
- filtered_summary

STRICT RULES:
- Return ONLY ONE of these:
  total_deposit
  total_withdrawal
  expense_breakdown
  daily_summary
  financial_insights
  filtered_summary
  rag

- DO NOT explain
- DO NOT add extra words

Routing rules:
- totals → total_deposit / total_withdrawal
- expenses / spending → expense_breakdown
- daily → daily_summary
- insights / losing money / recommendations → financial_insights
- date queries (last 7 days, this month, march, last 30 days) → filtered_summary
- anything else → rag
"""


# =========================================================
# DECISION ENGINE
# =========================================================
def decide_action(query: str) -> str:
    try:
        decision_prompt = f"{SYSTEM_PROMPT}\n\nUser question: {query}\nAnswer:"
        decision = generate_response(decision_prompt).strip().lower()

        # Clean response
        decision = decision.replace("\n", "").replace(".", "").strip()

        logger.info(f"[DECISION] Query: {query} → {decision}")

        return decision

    except Exception as e:
        logger.error(f"[DECISION ERROR] {e}")
        return "rag"


# =========================================================
# TOOL EXECUTION
# =========================================================
def execute_tool(tool_name: str, query: str) -> str:
    try:
        if tool_name not in TOOLS:
            return None

        logger.info(f"[TOOL] Executing: {tool_name}")

        if tool_name == "filtered_summary":
            return TOOLS[tool_name](query)

        return TOOLS[tool_name]()

    except Exception as e:
        logger.error(f"[TOOL ERROR] {tool_name}: {e}")
        return None


# =========================================================
# RAG FALLBACK
# =========================================================
def run_rag(query: str) -> str:
    try:
        is_qdrant_ok, qdrant_msg = retriever_health_check()

        if not is_qdrant_ok:
            logger.warning(f"[RAG WARNING] {qdrant_msg}")
            return f"❌ {qdrant_msg}"

        docs = search(query, limit=8)

        context = "\n\n".join(docs) if docs else "No matching data found."

        prompt = SMART_BANKING_PROMPT.format(
            context=context,
            question=query,
        )

        return generate_response(prompt)

    except Exception as e:
        logger.error(f"[RAG ERROR] {e}")
        return "⚠️ Unable to retrieve data. Please try again."


# =========================================================
# MAIN AGENT FUNCTION
# =========================================================
def run_agent(query: str) -> str:
    try:
        # -----------------------------------------------------
        # 1. Health Check (Azure OpenAI)
        # -----------------------------------------------------
        is_ok, msg = check_openai_health()

        if not is_ok:
            logger.error(f"[OPENAI ERROR] {msg}")
            return f"❌ {msg}"

        # -----------------------------------------------------
        # 2. Decide action
        # -----------------------------------------------------
        decision = decide_action(query)

        if decision not in TOOLS and decision != "rag":
            logger.warning(f"[INVALID DECISION] {decision} → fallback to rag")
            decision = "rag"

        # -----------------------------------------------------
        # 3. Execute tool
        # -----------------------------------------------------
        if decision in TOOLS:
            result = execute_tool(decision, query)

            if result:
                return result

            logger.warning("[TOOL FAILED] Falling back to RAG")
            return run_rag(query)

        # -----------------------------------------------------
        # 4. Default → RAG
        # -----------------------------------------------------
        return run_rag(query)

    except Exception as e:
        logger.error(f"[AGENT ERROR] {e}")
        return "⚠️ Something went wrong. Please try again."