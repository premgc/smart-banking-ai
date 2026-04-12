import streamlit as st

from app.llm import generate_response
from app.retriever import search

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="💳 Smart Banking AI", layout="wide")

st.title("💳 Smart Banking Assistant")


# =========================================================
# SESSION MEMORY (Chat History)
# =========================================================
if "messages" not in st.session_state:
    st.session_state.messages = []


# =========================================================
# DISPLAY CHAT HISTORY
# =========================================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# =========================================================
# USER INPUT
# =========================================================
prompt = st.chat_input("Ask about your transactions...")

if prompt:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # =====================================================
    # 🔥 RAG STEP (IMPORTANT)
    # =====================================================
    try:
        context_docs = search(prompt, limit=5)
        context = "\n\n".join(context_docs)

        full_prompt = f"""
You are a banking assistant.

Use the following transaction data to answer the question.

DATA:
{context}

QUESTION:
{prompt}
"""

        answer = generate_response(full_prompt)

    except Exception as e:
        answer = f"❌ Error: {e}"

    # Show assistant response
    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )