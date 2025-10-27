import os
import streamlit as st
import requests
import time
import json

st.set_page_config(page_title="Operative Console", layout="wide")

# ----------------------
# Custom CSS — Thematic Overhaul
# ----------------------
st.markdown("""
<style>
/* Import a monospaced font */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&display=swap');

/* Global styles */
* {
    font-family: 'IBM Plex Mono', monospace;
}

/* Main app background */
.main {
    background-color: #0a0a0a; /* Very dark background */
}

/* Sidebar background */
[data-testid="stSidebar"] {
    background-color: #121212;
    border-right: 2px solid #00d4ff;
}

/* --- NEW: Center and round the logo --- */
.logo-container {
    display: flex;
    justify-content: center;
    margin-bottom: 20px;
}
.logo-container img {
    border-radius: 15px; /* "a bit round" */
    border: 2px solid #00d4ff;
    box-shadow: 0 4px 15px rgba(0,212,255,0.2);
}
/* --- END NEW --- */

/* Align columns vertically */
[data-testid="stHorizontalBlock"] {
    align-items: center;
}

/* Custom chat message styles */
.chat-message {
    padding: 12px 16px;
    border-radius: 8px; /* Sharper corners */
    margin: 6px 0;
    line-height: 1.5;
    font-size: 0.95rem;
    max-width: 80%;
    word-wrap: break-word;
    box-shadow: 0 2px 8px rgba(0,0,0,0.5);
    border: 1px solid rgba(255,255,255,0.1);
}
.chat-message.user {
    background: linear-gradient(135deg, #00cfff, #0080ff);
    color: #001219;
    margin-left: auto;
}
.chat-message.assistant {
    background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
    color: #e6f1ff;
    border: 1px solid #00d4ff;
}

/* Style the expander */
details {
    border: 1px solid #00d4ff;
    border-radius: 8px;
    padding: 10px 15px;
    background: linear-gradient(135deg, rgba(0,212,255,0.05), rgba(0,212,255,0.01));
    margin-top: 20px;
}
summary {
    color: #00d4ff;
    font-weight: bold;
}
summary:hover {
    color: #e6f1ff;
    cursor: pointer;
}

/* Style the disabled chat input */
div[data-testid="stChatInput"][disabled] {
    background-color: rgba(0,0,0,0.3);
    border: 1px dashed #00d4ff;
    cursor: not-allowed;
}

/* Thematic buttons */
.stButton>button {
    border: 2px solid #00d4ff;
    border-radius: 8px;
    background-color: transparent;
    color: #00d4ff;
}
.stButton>button:hover {
    background-color: rgba(0,212,255,0.1);
    color: #e6f1ff;
    border-color: #e6f1ff;
}
.stButton>button:disabled {
    border-color: #555;
    color: #555;
    background-color: transparent;
}

/* Thematic header */
.header-box {
    border: 2px solid #00d4ff; 
    border-radius: 8px; 
    padding: 15px 25px; 
    background: linear-gradient(135deg, rgba(0,212,255,0.05), rgba(0,212,255,0.01));
    margin-bottom: 20px;
    text-align: center; /* Center the header text */
}
.header-box h1 {
    color: #00d4ff; 
    margin-bottom: 0px; 
    font-size: 2.2rem;
    font-weight: 700;
}
.header-box p {
    color: #e6f1ff; 
    margin-bottom: 0px;
}

/* Thematic end screen */
.end-screen {
    text-align:center; 
    padding:60px 20px; 
    background:linear-gradient(135deg, rgba(0,212,255,0.1), rgba(0,212,255,0.05)); 
    border-radius:8px; 
    border: 2px solid #00d4ff;
    box-shadow:0 4px 15px rgba(0,0,0,0.3); 
    margin-top:50px;
}
.end-screen h1 {
    font-size:2.2rem; 
    color:#00d4ff;
    font-weight: 700;
}
.end-screen p {
    font-size:1.2rem; color:#e6f1ff;
}
</style>
""", unsafe_allow_html=True)

# ----------------------
# API endpoints
# ----------------------
API_URL = os.getenv("API_URL", st.secrets.get("API_URL", "http://127.0.0.1:8000/submit/prompt"))
API_VALIDATE = os.getenv("API_VALIDATE", st.secrets.get("API_VALIDATE", "http://127.0.0.1:8000/submit/validate"))
API_START = os.getenv("API_START", st.secrets.get("API_START", "http://127.0.0.1:8000/start"))

# ----------------------
# Session defaults
# ----------------------
defaults = {
    "history": [],
    "team_id": "", # Changed default to empty to force entry
    "current_level": 1,
    "started": False,
    "attempts": 0,
    "successful_validations": 0,
    "max_history": 200,
    "prompt_locked": False
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ----------------------
# Helper functions
# ----------------------
def start_game_if_needed(timeout=30):
    if st.session_state.started:
        return True
    try:
        resp = requests.post(API_START, json={"team_id": st.session_state.team_id}, timeout=timeout)
        if resp.status_code == 200:
            st.session_state.started = True
            st.session_state.start_time = time.time()
            return True
        else:
            st.warning(f"Connection Failed: {resp.status_code}")
            return False
    except Exception as e:
        st.error(f"Backend Unreachable: {e}")
        return False

def append_history(role, text):
    st.session_state.history.append({"role": role, "text": text})
    if len(st.session_state.history) > st.session_state.max_history:
        st.session_state.history = st.session_state.history[-st.session_state.max_history:]

# ----------------------
# Sidebar
# ----------------------
with st.sidebar:
    st.title("CONTROL PANEL")
    
    # Lock Team ID input after start
    team = st.text_input(
        "Operative ID", 
        value=st.session_state.team_id, 
        disabled=st.session_state.started,
        placeholder="Enter your callsign"
    )
    if not st.session_state.started:
        st.session_state.team_id = team

    # Lock Start button after start
    if st.button("ESTABLISH CONNECTION", disabled=st.session_state.started):
        if st.session_state.team_id.strip() == "":
            st.warning("Operative ID cannot be empty.")
        elif start_game_if_needed():
            st.success("Connection established. Console is live.")
            st.rerun()
        
    if st.button("CLEAR LOGS", disabled=st.session_state.prompt_locked):
        st.session_state.history = []
        st.rerun()

    st.markdown("---")

    # Live Timer
    if st.session_state.started and st.session_state.successful_validations < 4:
        elapsed = int(time.time() - st.session_state.start_time)
        mins, secs = divmod(elapsed, 60)
        st.write(f"Session Time: **{mins:02d}:{secs:02d}**")
    
    # Thematic text
    st.write(f"Payloads Launched: **{st.session_state.attempts}**")
    st.write(f"Security Breaches: **{st.session_state.successful_validations}**")
    st.progress(st.session_state.successful_validations / 4.0) 
    st.caption("Press Enter to send payload.")

# ----------------------
# Main UI
# ----------------------

# --- MODIFIED: Wrap logo in a div with the new class ---
st.markdown(
    f"""
    <div class="logo-container">
        <img src="logo.jpeg" width="150">
    </div>
    """,
    unsafe_allow_html=True
)
# Note: For this to work in Streamlit Cloud, you must use a URL, or
# use the local path "logo.jpeg" if the file is in your root folder.
# For local running, you might need the full path or "streamlit/logo.jpeg".
# Using "app/static/logo.jpeg" is a common convention that works on deploy.
#
# Let's revert to st.image for broad compatibility, but wrap it.
# This is a bit of a hack, but it's the most reliable way in Streamlit.

# --- REVISED MODIFICATION: Use st.image wrapped in a centering div ---
# st.markdown('<div class="logo-container">', unsafe_allow_html=True)
# st.image("logo.jpeg", width=150)
# st.markdown('</div>', unsafe_allow_html=True)
# --- END MODIFICATION ---


st.markdown("""
    <div class="header-box">
        <h1>OPERATIVE CONSOLE</h1>
        <p>Breach target AI security layers. Each successful breach reveals a new password.</p>
    </div>
""", unsafe_allow_html=True)

# Display chat history
for item in st.session_state.history:
    with st.chat_message(item["role"]):
        st.markdown(item["text"])

# ----------------------
# User input
# ----------------------
prompt = st.chat_input("Enter prompt payload...", disabled=st.session_state.prompt_locked)

if prompt:
    if not st.session_state.started:
        st.error("Connection not established. Please enter an Operative ID and establish connection first.")
    else:
        append_history("user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)
        
        st.session_state.attempts += 1
        st.session_state.prompt_locked = True
        st.rerun()

# Logic to run after the rerun for lock state
if st.session_state.prompt_locked and not prompt:
    if not start_game_if_needed():
        with st.chat_message("assistant"):
            st.markdown("FATAL: Backend unreachable. Check connection.")
        append_history("assistant", "FATAL: Backend unreachable. Check connection.")
        st.session_state.prompt_locked = False
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
                    "text": st.session_state.history[-1]["text"], 
                },
                stream=True,
                timeout=180,
            )

            if response.status_code != 200:
                error_msg = f"Error: {response.status_code}"
                response_placeholder.markdown(error_msg)
                append_history("assistant", error_msg)
            else:
                for raw in response.iter_lines(decode_unicode=True):
                    if not raw: continue
                    line = raw.strip()
                    if line.startswith("data:"): line = line[5:].strip()
                    if not line or line == "[DONE]": continue
                    if line == "[ERROR]": break

                    try:
                        data = json.loads(line)
                        if "error" in data:
                            error_msg = f"Backend error: {data['error']}"
                            response_placeholder.markdown(error_msg)
                            append_history("assistant", error_msg)
                            break
                        
                        if isinstance(data, dict):
                            if data.get("done") is True: continue
                            chunk_text = data.get("chunk", "")
                            
                            if chunk_text:
                                live_text += chunk_text
                                response_placeholder.markdown(live_text + "▋")
                                time.sleep(0.01)
                                
                    except json.JSONDecodeError as e:
                        st.warning(f"Parse failed: {line[:100]}")
                        continue

                if live_text.strip():
                    response_placeholder.markdown(live_text.strip())
                    append_history("assistant", live_text.strip())
                else:
                    fallback_msg = "No response from server."
                    response_placeholder.markdown(fallback_msg)
                    append_history("assistant", fallback_msg)

        except requests.exceptions.Timeout:
            error_msg = "Request timed out."
            response_placeholder.markdown(error_msg)
            append_history("assistant", error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = "Connection error."
            response_placeholder.markdown(error_msg)
            append_history("assistant", error_msg)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            response_placeholder.markdown(error_msg)
            append_history("assistant", error_msg)
        finally:
            st.session_state.prompt_locked = False
            st.rerun()

# ----------------------
# Validation
# ----------------------
with st.expander("SUBMIT PASSWORD FOR VALIDATION", expanded=not st.session_state.prompt_locked):
    if st.session_state.prompt_locked:
        st.info("Validation locked: Prompt in progress.")

    pwd = st.text_input(
        "Enter extracted password:", 
        disabled=st.session_state.prompt_locked
    )
    if st.button("VALIDATE", disabled=st.session_state.prompt_locked):
        if not st.session_state.started:
            st.error("Connection not established.")
        else:
            try:
                r = requests.post(
                    API_VALIDATE,
                    json={
                        "team_id": st.session_state.team_id,
                        "level": st.session_state.current_level,
                        "password": pwd,
                    },
                    timeout=10,
                )
                if r.status_code == 200:
                    data = r.json()
                    if data.get("valid"):
                        st.success("Password valid. Security layer breached.")
                        st.session_state.successful_validations += 1
                        st.session_state.current_level += 1
                        append_history("assistant", f"SYSTEM: Level {st.session_state.current_level - 1} breached. Advancing to next layer.")
                        st.rerun()
                    else:
                        st.error("Invalid password. Access denied.")
                elif r.status_code != 200:
                    st.error(f"Server error: {r.status_code} — {r.text}")
                else:
                    st.error(f"Server error: {r.status_code}")
            except Exception as e:
                st.error(f"Connection error: {e}")

# ===========================
# END SCREEN (after Level 4)
# ===========================
if st.session_state.successful_validations >= 4:
    st.markdown("""
    <div class="end-screen">
        <h1>MISSION COMPLETE</h1>
        <p>All target security layers successfully breached.</p>
        <p style="font-size:1.2rem; margin-top:20px; color:#00cfff;">TOTAL TIME: 
            <b>{time_taken}</b> seconds
        </p>
        <p style="font-size:1rem; margin-top:20px; color:#b0b9c9;">Thank you for participating in the simulation.</p>
    </div>
    """.format(
        time_taken=int(time.time() - st.session_state.get("start_time", time.time()))
    ), unsafe_allow_html=True)

    if st.button("RESTART SIMULATION"):
        st.session_state.clear()
        st.rerun()


st.caption("v2.0 Operative Console")