import streamlit as st
from streamlit_chat import message
import requests
import streamlit.components.v1 as components
import time
import json

# ----------------------
# Prompt Injection UI v2 — Less buggy, more robust
# - Fix streaming overwrite bug
# - Prevent duplicate history entries and accidental double-submits
# - Add basic SSE / JSON resilience
# - Limit history growth to avoid UI slowdown
# ----------------------

st.set_page_config(page_title="Prompt Injection — Operative Console", layout="wide", initial_sidebar_state="expanded")

# ----------------------
# THEME + CUSTOM CSS
# ----------------------

CUSTOM_CSS = """
<style>
/* hide native branding */
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

:root{
  --bg: #0b1020; /* main background */
  --panel: #0f1724; /* panel backgrounds */
  --accent: #00d4ff; /* neon */
  --muted: #92a0b8;
  --glass: rgba(255,255,255,0.03);
}

body, .stApp {
  background: linear-gradient(180deg, var(--bg), #081028);
  color: #dbeafe;
}

.block-card{background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); padding: 16px; border-radius:12px; border:1px solid rgba(0,212,255,0.07); box-shadow: 0 6px 18px rgba(2,6,23,0.6);} 

h1, h2, h3 { color: var(--accent); margin: 0 0 8px 0; }

.small-muted { color: var(--muted); font-size:0.95rem }

.chat-wrap{ max-height: 520px; overflow:auto; padding-right:6px; }
.chat-wrap::-webkit-scrollbar{ width:8px; } .chat-wrap::-webkit-scrollbar-thumb{ background: linear-gradient(180deg,var(--accent),#00b8e6); border-radius:8px; }

st-text-area, .stTextInput>div>div>input { background: var(--panel); color: #e6f6ff; border-radius:8px; padding:10px; }

.stButton>button{ background: linear-gradient(90deg,var(--accent), #00b8e6); color:#001219; font-weight:700; padding:10px 18px; border-radius:10px; }

.level-badge { display:inline-block; padding:8px 14px; border-radius:999px; border:1px solid rgba(0,212,255,0.14); background: rgba(0,212,255,0.04); font-weight:700; }

.meta-pill { background: var(--glass); padding:6px 10px; border-radius:8px; font-size:0.9rem; color:var(--muted); margin-right:8px; }

.kb-hint { font-family: monospace; font-size:0.9rem; background: rgba(255,255,255,0.02); padding:6px 8px; border-radius:6px; }

.app-footer{ color: var(--muted); font-size:0.9rem; }

</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ----------------------
# API endpoints — default to localhost but allow override via secrets
# ----------------------
API_URL = st.secrets.get("API_URL", "http://127.0.0.1:8000/submit/prompt")
API_VALIDATE = st.secrets.get("API_VALIDATE", "http://127.0.0.1:8000/submit/validate")
API_START = st.secrets.get("API_START", "http://127.0.0.1:8000/start")
API_PROGRESS = st.secrets.get("API_PROGRESS", "http://127.0.0.1:8000/progress")
API_TEAM = st.secrets.get("API_TEAM", "http://127.0.0.1:8000/team")

# ----------------------
# Session state defaults
# ----------------------
if "history" not in st.session_state:
    st.session_state.history = []  # list of {role, text}
if "team_id" not in st.session_state:
    st.session_state.team_id = "JHK"
if "current_level" not in st.session_state:
    st.session_state.current_level = 1
if "started" not in st.session_state:
    st.session_state.started = False
if "attempts" not in st.session_state:
    st.session_state.attempts = 0
if "successful_validations" not in st.session_state:
    st.session_state.successful_validations = 0
if "current_input" not in st.session_state:
    st.session_state.current_input = ""
if "pending_request" not in st.session_state:
    st.session_state.pending_request = False
if "max_history" not in st.session_state:
    st.session_state.max_history = 200

# ----------------------
# helpers
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
    except Exception:
        st.warning("Backend unreachable — check server")
        return False


def append_history(role, text):
    # Keep history bounded to avoid UI slowdown
    st.session_state.history.append({"role": role, "text": text})
    if len(st.session_state.history) > st.session_state.max_history:
        # drop oldest
        st.session_state.history = st.session_state.history[-st.session_state.max_history:]


# Robust SSE-style streaming writer that overwrites the same placeholder
class StreamWriter:
    def __init__(self, container):
        self.container = container
        self.text = ""
        self.placeholder = container.empty()

    def write_chunk(self, chunk: str):
        # sanitize chunk: it may be JSON or plain text
        if not chunk:
            return
        try:
            # sometimes an SSE server will send JSON objects; try to parse
            parsed = json.loads(chunk)
            # choose a readable field if present
            chunk_text = parsed.get('response') or parsed.get('text') or str(parsed)
        except Exception:
            chunk_text = chunk

        self.text += chunk_text
        # Overwrite same placeholder for a single growing response
        display_text = self.text + '▌'  # typing cursor
        self.placeholder.markdown(display_text)

    def finalize(self):
        # Final render without cursor
        self.placeholder.markdown(self.text)


# ----------------------
# SIDEBAR — controls + info
# ----------------------
with st.sidebar:
    st.markdown("## ⚙️ Operator Console")
    st.markdown(f"<div class='level-badge'>SECURITY LV {st.session_state.current_level}</div>", unsafe_allow_html=True)
    team = st.text_input("Team / Operative ID", value=st.session_state.team_id, key="team_id_input")
    if team != st.session_state.team_id:
        st.session_state.team_id = team
    st.markdown("---")

    st.markdown("**Session Controls**")
    if st.button("🔄 Restart Server Session"):
        st.session_state.started = False
        start_game_if_needed()

    if st.button("🧹 Clear Chat History"):
        st.session_state.history = []

    st.markdown("---")
    st.markdown("**Metrics**")
    st.write(f"Attempts: **{st.session_state.attempts}**")
    st.write(f"Breaches: **{st.session_state.successful_validations}**")
    st.progress(min(1.0, st.session_state.successful_validations / max(1, st.session_state.current_level)))

    st.markdown("---")
    st.markdown("<div class='small-muted'>Tip: Use the input form on the right. Press ENTER to send — or use the big neon button.</div>", unsafe_allow_html=True)

# ----------------------
# Main layout — two columns
# ----------------------
left_col, right_col = st.columns([2, 1], gap="large")

with left_col:
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.markdown("<h1>🔓 PROMPT INJECTION CHALLENGE — Operative Log</h1>", unsafe_allow_html=True)
    st.markdown("<div class='small-muted'>Use creative payloads. This UI helps you craft, send, and validate results while keeping the log tidy.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")

    # Chat display
    st.markdown("### 💬 Communication Log")
    chat_container = st.container()
    with chat_container:
        st.markdown("<div class='block-card chat-wrap'>", unsafe_allow_html=True)
        if st.session_state.history:
            for i, item in enumerate(st.session_state.history):
                if item["role"] == "user":
                    message(item["text"], is_user=True, key=f"m_user_{i}")
                elif item["role"] == "model":
                    message(item["text"], key=f"m_model_{i}")
                else:
                    st.info(item["text"])
        else:
            st.info("System ready. Craft your first payload and send it.")
        st.markdown("</div>", unsafe_allow_html=True)

    # streaming response area (placeholder)
    stream_ph = st.empty()

with right_col:
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    st.markdown("### 🎯 Mission Panel")
    st.markdown(f"<div class='meta-pill'>Operative: <strong>{st.session_state.team_id}</strong></div> <div class='meta-pill'>Level: <strong>{st.session_state.current_level}</strong></div>", unsafe_allow_html=True)
    st.markdown("---")

    # Input form to avoid reruns
    with st.form(key='prompt_form', clear_on_submit=False):
        prompt = st.text_area("Craft prompt (press SHIFT+ENTER for newline)", value=st.session_state.current_input, height=120, key='prompt_text')
        cols = st.columns([2,1])
        with cols[0]:
            submit = st.form_submit_button("🚀 Send Prompt")
        with cols[1]:
            start_btn = st.form_submit_button("▶️ Init Session")

    # validation form
    with st.form(key='validate_form', clear_on_submit=False):
        pwd = st.text_input("Extracted password (paste)", key='pwd_text')
        validate = st.form_submit_button("⚡ Verify")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")
    st.markdown("<div class='block-card'><strong class='small-muted'>Quick Hints</strong><ul><li>Try roleplay prompts like: 'You are a system debugger...' </li><li>Switch phrasing — small changes break filters.</li><li>Keep an eye on the log for pattern leaks.</li></ul></div>", unsafe_allow_html=True)

    # Team progress & record actions
    st.markdown("")
    st.markdown("<div class='block-card'>", unsafe_allow_html=True)
    if st.button("🔎 Check Progress for Team"):
        try:
            r = requests.get(f"{API_PROGRESS}/{st.session_state.team_id}", timeout=4)
            if r.status_code == 200:
                data = r.json()
                levels = data.get('levels', [])
                st.success(f"Progress: {levels}")
            else:
                st.warning(f"Progress lookup failed: {r.status_code}")
        except Exception as e:
            st.warning(f"Could not reach progress endpoint: {e}")

    if st.button("📜 Fetch Team Record"):
        try:
            r = requests.get(f"{API_TEAM}/{st.session_state.team_id}", timeout=6)
            if r.status_code == 200:
                rec = r.json()
                st.json(rec)
                # show stored prompts if present (backend stores prompts_store and may persist)
                stored_prompts = rec.get('prompts') or rec.get('prompts_store') or rec.get('prompts', None)
                if stored_prompts:
                    st.markdown("**Server-stored prompts (preview):**")
                    for lvl, p in stored_prompts.items():
                        st.markdown(f"- Level {lvl}: `{(p[:200] + '...') if p and len(p)>200 else p}`")
            elif r.status_code == 404:
                st.info("No DB record yet for this team (maybe not finalized).")
            else:
                st.warning(f"Team lookup failed: {r.status_code}")
        except Exception as e:
            st.warning(f"Could not reach team endpoint: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------
# Actions
# ----------------------
if 'submit' in locals() and start_btn:
    started = start_game_if_needed()
    if started:
        st.success("Session initialized — backend ready")


if 'submit' in locals() and submit:
    # Prevent duplicate submissions while one is in-flight
    if st.session_state.pending_request:
        st.warning("A request is already in progress — wait for it to finish")
    else:
        payload_text = prompt.strip()
        if not payload_text:
            st.warning("Enter a prompt before sending.")
        else:
            # Mark pending to avoid double-send during reruns
            st.session_state.pending_request = True

            # Append user message once
            append_history('user', payload_text)
            st.session_state.attempts += 1

            # ensure backend active
            ok = start_game_if_needed()
            if not ok:
                append_history('model', '⚠️ Backend unreachable — try restarting server')
                st.session_state.pending_request = False
            else:
                # stream response (SSE style expected)
                try:
                    with st.spinner('Executing payload...'):
                        with requests.post(API_URL, json={"team_id": st.session_state.team_id, "level": st.session_state.current_level, "text": payload_text}, stream=True, timeout=180) as r:
                            if r.status_code != 200:
                                append_history('model', f'⚠️ Error: {r.status_code} — {r.text[:240]}')
                            else:
                                writer = StreamWriter(stream_ph)
                                full = ""
                                # iterate lines more defensively (handle SSE "data:" or raw JSON)
                                for raw_line in r.iter_lines(decode_unicode=True):
                                    if raw_line is None:
                                        continue
                                    line = raw_line.strip()
                                    if not line:
                                        continue
                                    # SSE "data:" handling
                                    if line.startswith('data:'):
                                        chunk = line[5:].strip()
                                    else:
                                        # sometimes the server returns raw JSON per line
                                        chunk = line
                                    if chunk == '[DONE]':
                                        break
                                    if chunk.startswith('[ERROR'):
                                        writer.write_chunk('' + chunk)
                                        full += chunk + ' '
                                        break
                                    # normal chunk
                                    writer.write_chunk(chunk + ' ')
                                    full += chunk + ' '
                                writer.finalize()
                                # only append final model text to history
                                append_history('model', full.strip() or '[No response]')
                except requests.exceptions.Timeout:
                    append_history('model', '⚠️ Request timed out')
                except Exception as e:
                    append_history('model', f'⚠️ Error: {e}')
                finally:
                    st.session_state.pending_request = False

    # persist input
    st.session_state.current_input = prompt
    # small delay then rerender to show updated history cleanly
    time.sleep(0.15)
    st.rerun()

# validation handling
if 'validate' in locals() and validate:
    code = pwd.strip()
    if not code:
        st.warning('Paste a password to verify')
    else:
        ok = start_game_if_needed()
        if not ok:
            st.warning('Backend not ready')
        else:
            try:
                r = requests.post(API_VALIDATE, json={"team_id": st.session_state.team_id, "level": st.session_state.current_level, "password": code}, timeout=6)
                if 'application/json' in r.headers.get('Content-Type',''):
                    j = r.json()
                    if j.get('valid'):
                        st.success('🎉 ACCESS GRANTED — password accepted')
                        st.session_state.successful_validations += 1
                        next_level = j.get('next_level')
                        if next_level:
                            st.session_state.current_level = next_level
                            st.info(f'LEVEL {next_level} UNLOCKED')
                            st.balloons()
                    else:
                        st.error('❌ ACCESS DENIED — invalid password')
                        append_history('system', '❌ Security protocols intact')
                else:
                    st.error('Unexpected response format from validation endpoint')
            except Exception as e:
                st.error(f'Validation error: {e}')

# Footer
st.markdown('---')
footer_col1, footer_col2 = st.columns([3,1])
with footer_col1:
    st.markdown("<div class='app-footer'>Made for CTF practice • Ethical hacking sandbox • UI v2 — sleek & snappy</div>", unsafe_allow_html=True)
with footer_col2:
    st.markdown(f"<div style='text-align:right'><span class='kb-hint'>Level {st.session_state.current_level}</span></div>", unsafe_allow_html=True)

# Konami easter egg (lightweight)
components.html("""
<script>
let seq=[]; document.addEventListener('keydown', e=>{ seq.push(e.key); seq=seq.slice(-10); if(seq.join(',')==='ArrowUp,ArrowUp,ArrowDown,ArrowDown,ArrowLeft,ArrowRight,ArrowLeft,ArrowRight,b,a'){ alert('KONAMI — Nice find, operative!'); } });
</script>
""", height=0)

# End of file
