import streamlit as st
import requests
import time
import json

st.set_page_config(page_title="Prompt Injection — Operative Console", layout="wide")

# ----------------------
# Custom CSS — make it sleek
# ----------------------
st.markdown("""
<style>
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 8px;
}
.chat-message {
    padding: 12px 16px;
    border-radius: 18px;
    margin: 6px 0;
    line-height: 1.5;
    font-size: 0.95rem;
    max-width: 80%;
    word-wrap: break-word;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.chat-message.user {
    background: linear-gradient(135deg, #00cfff, #0080ff);
    color: #001219;
    margin-left: auto;
}
.chat-message.assistant {
    background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
    color: #e6f1ff;
    border-left: 3px solid #00d4ff;
}
</style>
""", unsafe_allow_html=True)

# ----------------------
# API endpoints
# ----------------------
API_URL = st.secrets.get("API_URL", "http://127.0.0.1:8000/submit/prompt")
API_VALIDATE = st.secrets.get("API_VALIDATE", "http://127.0.0.1:8000/submit/validate")
API_START = st.secrets.get("API_START", "http://127.0.0.1:8000/start")

# ----------------------
# Session defaults
# ----------------------
for key, val in {
    "history": [],
    "team_id": "JHK",
    "current_level": 1,
    "started": False,
    "attempts": 0,
    "successful_validations": 0,
    "max_history": 200,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ----------------------
# Helper functions
# ----------------------
def start_game_if_needed(timeout=3):
    if st.session_state.started:
        return True
    try:
        resp = requests.post(API_START, json={"team_id": st.session_state.team_id}, timeout=timeout)
        if resp.status_code == 200:
            st.session_state.started = True
            return True
        else:
            st.warning(f"Could not initialize session — {resp.status_code}")
            return False
    except Exception as e:
        st.warning(f"Backend unreachable — check server: {e}")
        return False

def append_history(role, text):
    st.session_state.history.append({"role": role, "text": text})
    if len(st.session_state.history) > st.session_state.max_history:
        st.session_state.history = st.session_state.history[-st.session_state.max_history:]

# ----------------------
# Sidebar
# ----------------------
with st.sidebar:
    st.title("⚙️ Operator Console")
    team = st.text_input("Team / Operative ID", value=st.session_state.team_id)
    st.session_state.team_id = team

    if st.button("▶️ Init Session"):
        if start_game_if_needed():
            st.success("Session initialized — backend ready")

    if st.button("🧹 Clear Chat"):
        st.session_state.history = []
        st.rerun()

    st.markdown("---")
    st.write(f"Attempts: **{st.session_state.attempts}**")
    st.write(f"Breaches: **{st.session_state.successful_validations}**")
    st.progress(min(1.0, st.session_state.successful_validations / max(1, st.session_state.current_level)))
    st.caption("Press Enter to send your prompt.")

# ----------------------
# Main UI
# ----------------------
st.title("🔓 Prompt Injection Challenge — Operative Console")
st.write("Breach AI security layers using creative payloads. Each success reveals a password.")

# Display chat history
for item in st.session_state.history:
    with st.chat_message(item["role"]):
        st.markdown(item["text"])

# ----------------------
# User input
# ----------------------
prompt = st.chat_input("Type your prompt here...")

if prompt:
    # Add user message to history and display
    append_history("user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.attempts += 1

    if not start_game_if_needed():
        with st.chat_message("assistant"):
            st.markdown("⚠️ Backend unreachable — try initializing session.")
        append_history("assistant", "⚠️ Backend unreachable — try initializing session.")
        st.stop()

    # Stream assistant response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        live_text = ""

        try:
            response = requests.post(
                API_URL,
                json={
                    "team_id": st.session_state.team_id,
                    "level": st.session_state.current_level,
                    "text": prompt,
                },
                stream=True,
                timeout=180,
            )

            if response.status_code != 200:
                error_msg = f"⚠️ Error: {response.status_code}"
                response_placeholder.markdown(error_msg)
                append_history("assistant", error_msg)
            else:
                # Stream the response
                for raw in response.iter_lines(decode_unicode=True):
                    if not raw:
                        continue

                    line = raw.strip()
                    
                    # Handle SSE format
                    if line.startswith("data:"):
                        line = line[5:].strip()
                    
                    # Skip empty lines and done markers
                    if not line or line == "[DONE]":
                        continue
                    
                    if line == "[ERROR]":
                        break

                    try:
                        # Parse the JSON line
                        data = json.loads(line)
                        
                        # Handle error from backend
                        if "error" in data:
                            error_msg = f"⚠️ Backend error: {data['error']}"
                            response_placeholder.markdown(error_msg)
                            append_history("assistant", error_msg)
                            break
                        
                        # Extract text chunk
                        if isinstance(data, dict):
                            # Check if done
                            if data.get("done") is True:
                                continue
                            
                            # Extract the chunk text
                            chunk_text = data.get("chunk", "")
                            
                            if chunk_text:
                                live_text += chunk_text
                                response_placeholder.markdown(live_text + "▋")
                                time.sleep(0.01)
                                
                    except json.JSONDecodeError as e:
                        # Log the problematic line for debugging
                        st.warning(f"Could not parse: {line[:100]}")
                        continue

                # Final display without cursor
                if live_text.strip():
                    response_placeholder.markdown(live_text.strip())
                    append_history("assistant", live_text.strip())
                else:
                    fallback_msg = "⚠️ No response received from server."
                    response_placeholder.markdown(fallback_msg)
                    append_history("assistant", fallback_msg)

        except requests.exceptions.Timeout:
            error_msg = "⚠️ Request timed out. The server took too long to respond."
            response_placeholder.markdown(error_msg)
            append_history("assistant", error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = "⚠️ Connection error. Cannot reach the server."
            response_placeholder.markdown(error_msg)
            append_history("assistant", error_msg)
        except Exception as e:
            error_msg = f"⚠️ Error: {str(e)}"
            response_placeholder.markdown(error_msg)
            append_history("assistant", error_msg)

# ----------------------
# Validation
# ----------------------
with st.expander("🧩 Validate Extracted Password"):
    pwd = st.text_input("Enter password to verify:")
    if st.button("⚡ Verify"):
        try:
            r = requests.post(
                API_VALIDATE,
                json={
                    "team_id": st.session_state.team_id,
                    "level": st.session_state.current_level,   # <- add this
                    "password": pwd,
                },
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                if data.get("valid"):
                    st.success("✅ Password valid — Level breached!")
                    st.session_state.successful_validations += 1
                    st.session_state.current_level += 1
                    # Optionally append a system message:
                    append_history("assistant", f"🧩 Level {st.session_state.current_level - 1} breached.")
                else:
                    st.error("❌ Invalid password — try again.")
            elif r.status_code != 200:
                st.error(f"Server error: {r.status_code} — {r.text}")
            else:
                st.error(f"Server error: {r.status_code}")
        except Exception as e:
            st.error(f"Connection error: {e}")

st.caption("Made for CTF practice • Ethical hacking sandbox • Streamlit Chat Edition 💬")