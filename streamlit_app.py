import streamlit as st
import requests

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
    "Accept": "application/json"
}

# 3. Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render past chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 4. Handle new user input
if prompt := st.chat_input("Ask a question about your data..."):
    
    # Display and save the user's message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 5. Call the Snowflake Cortex API
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                
                # --- FIX 1: Format messages exactly how Cortex Agents expects them ---
                api_messages = []
                for msg in st.session_state.messages:
                    api_messages.append({
                        "role": msg["role"],
                        "content": [
                            {
                                "type": "text", 
                                "text": msg["content"]
                            }
                        ]
                    })
                    
                payload = {
                    "messages": api_messages,
                    "stream": False
                }
                
                try:
                    response = requests.post(URL, headers=HEADERS, json=payload)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    # --- FIX 2: Parse the Cortex Agent's response structure ---
                    # The API returns: {"role": "assistant", "content": [{"type": "text", "text": "..."}]}
                    assistant_reply = ""
                    for block in data.get("content", []):
                        if block.get("type") == "text":
                            assistant_reply += block.get("text", "") + "\n"
                            
                    # Display and save the extracted text
                    st.markdown(assistant_reply)
                    st.session_state.messages.append({"role": "assistant", "content": assistant_reply.strip()})
                    
                except requests.exceptions.RequestException as e:
                    st.error(f"API Error: {e}")
                    if response.content:
                        st.error(response.json())