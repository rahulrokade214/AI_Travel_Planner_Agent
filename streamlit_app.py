import streamlit as st
import requests
import datetime

BASE_URL = "http://localhost:8000"  # Backend endpoint

st.set_page_config(
    page_title="Travel Planner",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ----------------------------------------------------------------
# Custom CSS — Claude.ai-style: warm cream bg, serif greeting,
# terracotta accent, borderless messages, pill composer
# Content is vertically + horizontally centered in the viewport
# until a conversation starts.
# ----------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Inter:wght@400;500;600&display=swap');

    :root {
        --bg: #F4F1EA;
        --surface: #FFFFFF;
        --text: #3D3929;
        --text-muted: #83786B;
        --accent: #D97757;
        --accent-hover: #C15F3C;
        --border: #E8E4D9;
    }

    .stApp { background-color: var(--bg); }
    #MainMenu, footer, header {visibility: hidden;}

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Center everything vertically in the viewport */
    .block-container {
        max-width: 720px;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Greeting — serif, Claude-style */
    .greeting {
        font-family: 'Source Serif 4', serif;
        font-size: 2.1rem;
        font-weight: 400;
        color: var(--accent);
        margin-bottom: 0.3rem;
        letter-spacing: -0.01em;
    }
    .greeting-sub {
        font-size: 1rem;
        color: var(--text-muted);
        margin-bottom: 2.5rem;
    }

    /* Messages — minimal, borderless like Claude.ai */
    .msg-row {
        display: flex;
        margin: 1.4rem 0;
    }
    .msg-row.user { justify-content: flex-end; }
    .msg-row.assistant { justify-content: flex-start; }

    .msg-user {
        background-color: var(--surface);
        border: 1px solid var(--border);
        color: var(--text);
        padding: 0.75rem 1.1rem;
        border-radius: 18px;
        max-width: 75%;
        font-size: 0.98rem;
        line-height: 1.55;
    }

    .msg-assistant {
        color: var(--text);
        padding: 0 0.2rem;
        max-width: 100%;
        font-size: 0.98rem;
        line-height: 1.7;
    }
    .msg-assistant h1, .msg-assistant h2, .msg-assistant h3 {
        font-family: 'Source Serif 4', serif;
        color: var(--text);
        font-weight: 600;
    }
    .assistant-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--accent);
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.5rem;
    }

    /* Composer — pill bar like Claude.ai */
    div[data-testid="stForm"] {
        background-color: var(--surface);
        border: 1.5px solid var(--border);
        border-radius: 26px;
        padding: 0.5rem 0.6rem;
        box-shadow: 0 4px 18px rgba(61, 57, 41, 0.06);
    }
    div[data-testid="stForm"] input {
        border: none !important;
        background: transparent !important;
        font-size: 1rem;
        color: var(--text);
        padding: 0.7rem 0.6rem;
    }
    div[data-testid="stForm"] input:focus {
        box-shadow: none !important;
        outline: none !important;
    }
    div[data-testid="stForm"] input::placeholder {
        color: var(--text-muted);
    }

    div[data-testid="stFormSubmitButton"] button {
        background-color: var(--accent);
        color: #FFFFFF;
        border-radius: 999px;
        border: none;
        padding: 0.55rem 1.4rem;
        font-weight: 500;
        font-size: 0.92rem;
        transition: background-color 0.15s ease;
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        background-color: var(--accent-hover);
        color: #FFFFFF;
    }

    .empty-hint {
        color: var(--text-muted);
        font-size: 0.92rem;
        margin-top: 0.5rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------
# State
# ----------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ----------------------------------------------------------------
# Greeting header
# ----------------------------------------------------------------
st.markdown('<div class="greeting">Where would you like to go?</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="greeting-sub">Tell me your destination and I\'ll put together a full plan — stays, spots, and budget.</div>',
    unsafe_allow_html=True,
)



for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f'<div class="msg-row user"><div class="msg-user">{msg["content"]}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="msg-row assistant"><div class="msg-assistant">'
            f'<div class="assistant-label">Travel Planner · {msg["time"]}</div>'
            f'{msg["content"]}'
            f'</div></div>',
            unsafe_allow_html=True,
        )

# ----------------------------------------------------------------
# Composer
# ----------------------------------------------------------------
with st.form(key="query_form", clear_on_submit=True):
    col1, col2 = st.columns([6, 1])
    with col1:
        user_input = st.text_input(
            "User Input",
            placeholder="Plan a trip to Goa for 5 days",
            label_visibility="collapsed",
        )
    with col2:
        submit_button = st.form_submit_button("Send")

if submit_button and user_input.strip():
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("Planning your trip..."):
        try:
            payload = {"question": user_input}
            response = requests.post(f"{BASE_URL}/query", json=payload, timeout=120)

            if response.status_code == 200:
                answer = response.json().get("answer", "No answer returned.")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "time": datetime.datetime.now().strftime("%b %d, %H:%M"),
                })
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Something went wrong on the backend.\n\n```\n{response.text}\n```",
                    "time": datetime.datetime.now().strftime("%b %d, %H:%M"),
                })
        except Exception as e:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Couldn't reach the planner backend.\n\n`{e}`\n\nMake sure your FastAPI server is running:\n```\nuvicorn main:app --reload --port 8000\n```",
                "time": datetime.datetime.now().strftime("%b %d, %H:%M"),
            })

    st.rerun()