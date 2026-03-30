import streamlit as st
from agents import run_research
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
MAX_MESSAGES = 8  # Keep last 8 messages for bounded token usage

# Set up page configuration
st.set_page_config(page_title="🔍 Agentic Deep Researcher", layout="wide")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

def reset_chat():
    st.session_state.messages = []

# Sidebar: API Status
with st.sidebar:
    st.header("🔧 API Status")

    openai_key = os.getenv("OPENAI_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

    if openai_key and openai_key.startswith("sk-"):
        st.success("✓ OpenAI API key loaded from .env")
    else:
        st.error("✗ OpenAI API key not found in .env")

    if tavily_key and tavily_key.startswith("tvly-"):
        st.success("✓ Tavily API key loaded from .env")
    else:
        st.error("✗ Tavily API key not found in .env")


# Main Chat Interface Header
col1, col2 = st.columns([6, 1])
with col1:
    st.markdown("<h2>🔍 Agentic Deep Researcher</h2>",
                unsafe_allow_html=True)
    st.markdown("*Powered by OpenAI + Tavily + LangGraph*")
with col2:
    st.button("Clear ↺", on_click=reset_chat)

# Add spacing between header and chat history
st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input and process the research query
if prompt := st.chat_input("Enter your research query..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    openai_key = os.getenv("OPENAI_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

    if not openai_key or not tavily_key:
        response = "⚠️ API keys not found in `.env` file. Please add OPENAI_API_KEY and TAVILY_API_KEY to your `.env` file."
    else:
        with st.spinner("Researching... This may take a moment..."):
            try:
                # Build conversation context from previous messages (excluding current prompt)
                previous_messages = st.session_state.messages[:-1]  # Exclude current user message
                conversation_context = ""

                if previous_messages:
                    context_parts = []
                    for msg in previous_messages:
                        role = "Q" if msg["role"] == "user" else "A"
                        context_parts.append(f"{role}: {msg['content'][:500]}")  # Limit each message to 500 chars
                    conversation_context = "\n".join(context_parts)

                # Run research with conversation context
                result = run_research(prompt, conversation_context=conversation_context)
                response = result
            except Exception as e:
                response = f"An error occurred: {str(e)}"

    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append(
        {"role": "assistant", "content": response})

    # Enforce message limit: keep only last MAX_MESSAGES
    if len(st.session_state.messages) > MAX_MESSAGES:
        st.session_state.messages = st.session_state.messages[-MAX_MESSAGES:]
        st.info(f"💾 Chat history limited to last {MAX_MESSAGES} messages for token efficiency")
