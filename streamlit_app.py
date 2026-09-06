import json
import requests
import streamlit as st

st.title("❄️ Cortex Agent Chat")

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
    with st.chat_message(msg["role"]):
        if isinstance(msg["content"], list):
            for item in msg["content"]:
                if item.get("type") == "text":
                    st.markdown(item.get("data", ""))
                elif item.get("type") == "chart":
                    st.vega_lite_chart(item.get("data"), use_container_width=True)
        else:
            st.markdown(msg["content"])

# 4. Handle new user input
if prompt := st.chat_input("Ask a question about your data..."):
    # Display and record user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 5. Call the Snowflake Cortex API
    with st.chat_message("assistant"):
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
                            st.vega_lite_chart(
                                parsed_spec, use_container_width=True
                            )
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