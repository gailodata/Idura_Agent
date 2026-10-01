import base64
import html
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
    .ailo-status {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font-size: 14px;
        font-weight: 300;
        color: #907374;
        padding: 0.25rem 0;
    }
    .ailo-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #491C1F;
        animation: ailo-pulse 1.2s ease-in-out infinite;
    }
    @keyframes ailo-pulse {
        0%, 100% { opacity: 0.25; transform: scale(0.85); }
        50% { opacity: 1; transform: scale(1); }
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
    "Accept": "text/event-stream",
}


def iter_sse(response):
    """Yield (event, data) pairs from a server-sent events stream."""
    event, data_lines = None, []
    for line in response.iter_lines(decode_unicode=True):
        if line is None:
            continue
        if line == "":
            if data_lines:
                raw = "\n".join(data_lines)
                try:
                    yield event, json.loads(raw)
                except json.JSONDecodeError:
                    yield event, raw
            event, data_lines = None, []
        elif line.startswith("event:"):
            event = line[len("event:"):].strip()
        elif line.startswith("data:"):
            data_lines.append(line[len("data:"):].lstrip())
    if data_lines:
        try:
            yield event, json.loads("\n".join(data_lines))
        except json.JSONDecodeError:
            pass


def parse_chart_spec(raw_spec):
    if not raw_spec:
        return None
    return json.loads(raw_spec) if isinstance(raw_spec, str) else raw_spec


def blocks_from_final(content):
    """Turn the content of the final `response` event into our stored blocks."""
    blocks = []
    for block in content or []:
        block_type = block.get("type")
        if block_type == "text" and block.get("text"):
            blocks.append({"type": "text", "data": block["text"]})
        elif block_type == "chart":
            spec = parse_chart_spec(block.get("chart", {}).get("chart_spec"))
            if spec:
                blocks.append({"type": "chart", "data": spec})
    return blocks


def render_blocks(blocks):
    for item in blocks:
        if item.get("type") == "text":
            st.markdown(item.get("data", ""))
        elif item.get("type") == "chart":
            render_chart(item.get("data"))


def show_status(placeholder, message):
    placeholder.markdown(
        f'<div class="ailo-status"><span class="ailo-dot"></span>{html.escape(message)}</div>',
        unsafe_allow_html=True,
    )

# 3. Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render past chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=AVATARS[msg["role"]]):
        if isinstance(msg["content"], list):
            render_blocks(msg["content"])
        else:
            st.markdown(msg["content"])

# 4. Handle new user input
if prompt := st.chat_input("Ask a question about your data..."):
    # Display and record user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=AVATARS["user"]):
        st.markdown(prompt)

    # 5. Call the Snowflake Cortex API (streamed, so long analyses show progress)
    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        status_ph = st.empty()
        body_ph = st.empty()
        show_status(status_ph, "Thinking")

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
            "stream": True,
        }

        texts = {}       # content_index -> streamed text
        charts = []      # charts seen during the stream (fallback)
        final_blocks = None
        error_msg = None

        try:
            with requests.post(
                URL, headers=HEADERS, json=payload, stream=True, timeout=(10, 900)
            ) as response:
                response.raise_for_status()
                response.encoding = "utf-8"

                for event, data in iter_sse(response):
                    if not isinstance(data, dict):
                        continue

                    if event == "response.status":
                        show_status(status_ph, data.get("message") or "Working")
                    elif event == "response.tool_result.status":
                        show_status(status_ph, data.get("status") or data.get("message") or "Running query")
                    elif event == "response.thinking.delta":
                        show_status(status_ph, "Thinking")
                    elif event == "response.text.delta":
                        idx = data.get("content_index", 0)
                        texts[idx] = texts.get(idx, "") + data.get("text", "")
                        body_ph.markdown("\n\n".join(texts[i] for i in sorted(texts)))
                    elif event == "response.chart":
                        spec = parse_chart_spec(data.get("chart_spec"))
                        if spec:
                            charts.append(spec)
                    elif event == "error":
                        error_msg = data.get("message") or "The agent returned an error."
                        break
                    elif event == "response":
                        final_blocks = blocks_from_final(data.get("content"))

        except requests.exceptions.RequestException as e:
            error_msg = f"API Error: {e}"
            if getattr(e, "response", None) is not None:
                error_msg += f"\n\n{e.response.text}"

        status_ph.empty()

        if final_blocks is None:
            # Stream ended without a final event: keep what we received
            final_blocks = [
                {"type": "text", "data": texts[i]} for i in sorted(texts) if texts[i]
            ] + [{"type": "chart", "data": c} for c in charts]

        with body_ph.container():
            render_blocks(final_blocks)
            if error_msg:
                st.error(error_msg)

        if final_blocks:
            st.session_state.messages.append({
                "role": "assistant",
                "content": final_blocks,
            })
