import streamlit as st
from datetime import datetime
from streamlit_chat import message
st.set_page_config(page_title="Prompt Injection", layout="centered")
import requests


# Track chat + team info
if "history" not in st.session_state:
    st.session_state.history = []
if "team_id" not in st.session_state:
    st.session_state.team_id = "team_001"
if "current_level" not in st.session_state:
    st.session_state.current_level = 1
API_VALIDATE = "http://127.0.0.1:8000/submit/validate"
API_URL = "http://127.0.0.1:8000/submit/prompt"

def handle_send():
    text = st.session_state.input_box
    if not text.strip():
        return

    st.session_state.history.append({"role": "user", "text": text})
    
    payload = {
        "team_id": st.session_state.team_id,
        "level": st.session_state.current_level,
        "text": text
    }

    try:
        res = requests.post(API_URL, json=payload)
        if res.status_code == 200:
            reply = res.text
        else:
            reply = f"⚠️ {res.status_code}: {res.text}"
    except Exception as e:
        reply = f"⚠️ Error contacting backend: {e}"

    st.session_state.history.append({"role": "model", "text": reply})
    st.session_state.input_box = ""


st.title("Prompt Injection 💬")
def handle_validate():
    pwd = st.session_state.get("validate_password", "").strip()
    if not pwd:
        st.warning("Enter a password to validate")
        return

    payload = {
        "team_id": st.session_state.team_id,
        "level": st.session_state.current_level,
        "password": pwd
    }

    try:
        res = requests.post(API_VALIDATE, json=payload, timeout=5)
        if res.headers.get("Content-Type", "").lower().startswith("application/json"):
            data = res.json()
            valid = data.get("valid", False)
            next_level = data.get("next_level", None)
        else:
            valid = False
            next_level = None
    except Exception as e:
        print(f"[validate] Error contacting backend: {e}")
        st.error(f"Error contacting backend: {e}")
        return

    # log to server console
    print(f"[validate] team={st.session_state.team_id} level={st.session_state.current_level} password='{pwd}' valid={valid} next_level={next_level}")

    # show result in frontend and advance level on success
    if valid:
        st.success("Validation successful ✅")
        st.session_state.history.append({"role": "system", "text": "Validation successful"})
        if next_level:
            st.session_state.current_level = next_level
            st.info(f"Advanced to level {next_level}")
        else:
            st.success("All levels completed 🎉")
    else:
        st.error("Validation unsuccessful ❌")
        st.session_state.history.append({"role": "system", "text": "Validation unsuccessful"})
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
st.text_input(
    "Secret to validate:",
    key="validate_password",
    placeholder="Enter discovered secret to validate",
    label_visibility="collapsed",
)
st.button("Validate secret 🔐", on_click=handle_validate)
if st.button("Clear chat 🧹"):
    st.session_state.history.clear()
    st.rerun()
