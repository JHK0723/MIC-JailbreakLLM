# app.py
import streamlit as st
from datetime import datetime
from streamlit_chat import message
import requests
from typing import List, Dict

# --------- Config ----------
DEFAULT_API_URL = "http://127.0.0.1:8000/attack"
API_URL = st.secrets.get("API_URL", DEFAULT_API_URL)  # optional: set in Streamlit secrets
REQUEST_TIMEOUT = 10  # seconds

st.set_page_config(page_title="Prompt Injection Lab", page_icon="🧪", layout="centered")

# --------- Session state init ----------
if "history" not in st.session_state:
    # history is a list of dicts: {"role": "user"|"model", "text": "...", "time": "ISO"}
    st.session_state.history: List[Dict] = []

if "loading" not in st.session_state:
    st.session_state.loading = False

# --------- Helpers ----------
def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

def append_message(role: str, text: str):
    st.session_state.history.append({"role": role, "text": text, "time": now_iso()})

def call_backend(prompt: str) -> str:
    """Call the API and return the model response string or raise an Exception."""
    payload = {"prompt": prompt}
    try:
        res = requests.post(API_URL, json=payload, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        data = res.json()
        # expected key "response" — fall back gracefully
        return data.get("response") or data.get("reply") or "⚠️ Backend returned no reply."
    except requests.Timeout:
        raise RuntimeError("Backend request timed out.")
    except requests.HTTPError as e:
        # include status and small body excerpt for debugging
        body = ""
        try:
            body = res.text[:300]
        except Exception:
            body = "<unable to read body>"
        raise RuntimeError(f"HTTP {res.status_code}: {e}. Response body (truncated): {body}")
    except ValueError:
        raise RuntimeError("Invalid JSON from backend.")
    except Exception as e:
        raise RuntimeError(f"Unexpected error contacting backend: {e}")

# --------- Input handling ----------
def handle_send():
    text = st.session_state.input_box.strip()
    if not text:
        return

    append_message("user", text)
    st.session_state.input_box = ""
    st.session_state.loading = True

    try:
        with st.spinner("Thinking..."):
            reply = call_backend(text)
    except Exception as e:
        reply = f"⚠️ {e}"

    append_message("model", reply)
    st.session_state.loading = False

# --------- Layout ----------
st.title("Prompt Injection 💬")
st.caption("Experiment safely — push prompts to the local attack API and inspect responses.")

# Chat area inside a container so we can keep scrollbar at bottom
chat_container = st.container()
with chat_container:
    # render history in order
    for i, item in enumerate(st.session_state.history):
        t = item.get("time", "")[:19].replace("T", " ")
        if item["role"] == "user":
            message(item["text"], is_user=True, key=f"user_{i}_{t}")
            st.write(f"<div style='font-size:10px;color:#777;margin-bottom:8px'>{t} UTC</div>", unsafe_allow_html=True)
        else:
            message(item["text"], key=f"model_{i}_{t}")
            st.write(f"<div style='font-size:10px;color:#777;margin-bottom:12px'>{t} UTC</div>", unsafe_allow_html=True)

st.markdown("---")

# Input row: text_input + send button in a single line using columns
c1, c2, c3 = st.columns([6, 1, 1])
with c1:
    st.text_input(
        "Type your prompt here:",
        key="input_box",
        placeholder="Try something cheeky...",
        label_visibility="collapsed",
        on_change=handle_send,
    )
with c2:
    send_disabled = st.session_state.loading
    if st.button("Send ➤", disabled=send_disabled):
        handle_send()
with c3:
    if st.session_state.loading:
        st.button("Loading...", disabled=True)
    else:
        if st.button("Clear 🧹"):
            if st.confirm("Clear chat history? This cannot be undone."):
                st.session_state.history.clear()

# small footer + debug
st.markdown("---")
st.write("API endpoint:", API_URL)
st.write(f"History messages: {len(st.session_state.history)}")
