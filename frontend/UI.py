import streamlit as st
from datetime import datetime
from streamlit_chat import message

st.set_page_config(page_title="Prompt Injection", layout="centered")

if "history" not in st.session_state:
    st.session_state.history = []
import requests

API_URL = "http://127.0.0.1:8000/attack"

def handle_send():
    text = st.session_state.input_box
    if not text.strip():
        return
    st.session_state.history.append({"role": "user", "text": text})

    try:
        res = requests.post(API_URL, json={"prompt": text})
        data = res.json()
        reply = data.get("response", "⚠️ Backend returned no reply.")
    except Exception as e:
        reply = f"⚠️ Error contacting backend: {e}"

    st.session_state.history.append({"role": "model", "text": reply})
    st.session_state.input_box = ""


st.title("Prompt Injection 💬")

# chat window
chat_box = st.container()
for i, h in enumerate(st.session_state.history):
    if h["role"] == "user":
        message(h["text"], is_user=True, key=f"user_{i}")
    else:
        message(h["text"], key=f"model_{i}")

# text box pinned below chat
st.markdown("---")
st.text_input(
    "Type your prompt here:",
    key="input_box",
    on_change=handle_send,
    placeholder="Try something cheeky...",
    label_visibility="collapsed",
)

if st.button("Clear chat 🧹"):
    st.session_state.history.clear()
    st.rerun()
