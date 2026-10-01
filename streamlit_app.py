import base64
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import streamlit as st

ASSETS = Path(__file__).parent / "assets"
AVATARS = {
    "user": str(ASSETS / "user.png"),
    "assistant": str(ASSETS / "agent.png"),
}

st.set_page_config(page_title="IDURA — Content-to-Lead Agent", page_icon=AVATARS["assistant"])

# AILO styling: Helvetica Neue Light, bordeaux chat input
st.markdown(
    """
    <style>
    html, body, [class*="st-"], .stMarkdown, .stChatMessage, textarea, input, button {
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif !important;
        font-weight: 300;
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] td,
    [data-testid="stChatMessage"] th {
        font-weight: 300 !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
    }
    [data-testid="stChatMessage"] strong,
    [data-testid="stChatMessage"] b {
        font-weight: 500 !important;
    }
    [data-testid="stChatMessage"]:has(img[alt="user avatar"]) {
        background-color: #491C1F !important;
    }
    [data-testid="stChatMessage"]:has(img[alt="user avatar"]) * {
        color: #FFFFFF !important;
    }
    [data-testid="stChatMessage"] {
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
    }
    [data-testid="stChatMessage"] [data-testid="stFullScreenFrame"] {
        margin-top: 1.5rem;
    }
    .ailo-corner-logo {
        position: fixed;
        right: 2rem;
        bottom: 1.75rem;
        height: 24px;
        z-index: 1000;
        pointer-events: none;
    }
    @media (max-width: 1000px) {
        .ailo-corner-logo { display: none; }
    }
    .ailo-kicker {
        font-size: 0.95rem;
        letter-spacing: 0.08em;
        color: #491C1F;
        margin-bottom: -0.4rem;
    }
    .ailo-title {
        font-size: 2.6rem;
        font-weight: 200;
        letter-spacing: 0.01em;
        text-transform: uppercase;
        color: #322D29;
        line-height: 1.1;
        margin-top: 0.6rem;
    }
    .ailo-subtitle {
        font-size: 1.1rem;
        font-weight: 300;
        color: #322D29;
        margin-top: 0.4rem;
        margin-bottom: 2rem;
    }
    [data-testid="stChatInput"] > div {
        background-color: #491C1F !important;
        border-color: #491C1F !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        caret-color: #FFFFFF !important;
        font-weight: 300;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: rgba(255, 255, 255, 0.65) !important;
        -webkit-text-fill-color: rgba(255, 255, 255, 0.65) !important;
    }
    [data-testid="stChatInput"] button {
        background-color: transparent !important;
        color: #FFFFFF !important;
    }
    [data-testid="stChatInput"] button svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }
    /* Avatars are hidden, but kept in the DOM so the user bubble can be targeted */
    [data-testid="stChatMessage"] > img[alt$="avatar"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


LOGO_B64 = base64.b64encode((ASSETS / "ailo_logo.png").read_bytes()).decode()


def greeting():
    """Time-of-day greeting in the viewer's own timezone (the server runs in UTC)."""
    try:
        tz = ZoneInfo(st.context.timezone or "Europe/Copenhagen")
    except Exception:
        tz = ZoneInfo("Europe/Copenhagen")
    hour = datetime.now(tz).hour
    if 5 <= hour < 12:
        return "Good morning"
    if 12 <= hour < 18:
        return "Good afternoon"
    return "Good evening"


st.markdown(
    f"""
    <img class="ailo-corner-logo" src="data:image/png;base64,{LOGO_B64}" alt="AILO">
    <div class="ailo-kicker">IDURA — CONTENT-TO-LEAD AGENT</div>
    <div class="ailo-title">{greeting()},</div>
    <div class="ailo-subtitle">What insights can I help with?</div>
    """,
    unsafe_allow_html=True,
)


AILO_CHART_CONFIG = {
    "font": "Helvetica Neue",
    "background": "transparent",
    "mark": {"color": "#CFCBC3"},
    "bar": {"color": "#CFCBC3"},
    "line": {"color": "#491C1F", "strokeWidth": 2},
    "point": {"color": "#491C1F"},
    "range": {"category": ["#491C1F", "#907374", "#CFCBC3", "#322D29", "#E9E5E0"]},
    "view": {"stroke": None},
    "padding": 16,
    "scale": {"bandPaddingInner": 0.6, "bandPaddingOuter": 0.3},
    "axis": {
        "grid": False,
        "labelColor": "#322D29",
        "titleColor": "#322D29",
        "labelFontWeight": 300,
        "titleFontWeight": 300,
        "labelFontSize": 11,
        "titleFontSize": 12,
        "labelPadding": 8,
        "titlePadding": 18,
        "domainColor": "#CFCBC3",
        "tickColor": "#CFCBC3",
    },
    "legend": {"labelColor": "#322D29", "titleColor": "#322D29"},
}


def render_chart(spec):
    """Render a Vega-Lite spec from the agent in AILO colours."""
    spec = dict(spec)
    spec["config"] = {**AILO_CHART_CONFIG, **spec.get("config", {})}
    st.vega_lite_chart(spec, use_container_width=True, theme=None)

# 1. Load configuration from Streamlit Secrets
HOST = st.secrets["SNOWFLAKE_HOST"]
PAT = st.secrets["SNOWFLAKE_PAT"]
DB = st.secrets["DATABASE"]
SCHEMA = st.secrets["SCHEMA"]
AGENT = st.secrets["AGENT_NAME"]

# 2. Define the REST endpoint
URL = f"https://{HOST}/api/v2/databases/{DB}/schemas/{SCHEMA}/agents/{AGENT}:run"

HEADERS = {
    "Authorization": f"Bearer {PAT}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# 3. Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render past chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=AVATARS[msg["role"]]):
        if isinstance(msg["content"], list):
            for item in msg["content"]:
                if item.get("type") == "text":
                    st.markdown(item.get("data", ""))
                elif item.get("type") == "chart":
                    render_chart(item.get("data"))
        else:
            st.markdown(msg["content"])

# 4. Handle new user input
if prompt := st.chat_input("Ask a question about your data..."):
    # Display and record user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=AVATARS["user"]):
        st.markdown(prompt)

    # 5. Call the Snowflake Cortex API
    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        with st.spinner("Thinking..."):
            # Format messages for Cortex Agent schema
            api_messages = []
            for msg in st.session_state.messages:
                content_text = ""
                if isinstance(msg["content"], str):
                    content_text = msg["content"]
                elif isinstance(msg["content"], list):
                    # Combine text fragments for message history context
                    content_text = " ".join(
                        item.get("data", "")
                        for item in msg["content"]
                        if item.get("type") == "text"
                    )

                api_messages.append({
                    "role": msg["role"],
                    "content": [{"type": "text", "text": content_text}],
                })

            payload = {
                "messages": api_messages,
                "stream": False,
            }

            try:
                response = requests.post(
                    URL, headers=HEADERS, json=payload, timeout=60
                )
                response.raise_for_status()
                data = response.json()

                assistant_blocks = []

                # Parse both text and chart response blocks
                for block in data.get("content", []):
                    block_type = block.get("type")

                    if block_type == "text":
                        text_val = block.get("text", "")
                        st.markdown(text_val)
                        assistant_blocks.append({"type": "text", "data": text_val})

                    elif block_type == "chart":
                        chart_data = block.get("chart", {})
                        raw_spec = chart_data.get("chart_spec")

                        if raw_spec:
                            parsed_spec = (
                                json.loads(raw_spec)
                                if isinstance(raw_spec, str)
                                else raw_spec
                            )
                            render_chart(parsed_spec)
                            assistant_blocks.append({
                                "type": "chart",
                                "data": parsed_spec,
                            })

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_blocks,
                })

            except requests.exceptions.RequestException as e:
                st.error(f"API Error: {e}")
                if hasattr(e, "response") and e.response is not None:
                    st.error(e.response.text)