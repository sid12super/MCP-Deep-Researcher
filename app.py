import streamlit as st
from agents import run_research, stream_research
import os
import json
import datetime
import re
from dotenv import load_dotenv
import markdown2
from fpdf import FPDF

# Load environment variables from .env file
load_dotenv()

# Configuration
MAX_MESSAGES = 8  # Keep last 8 messages for bounded token usage

# Set up page configuration
st.set_page_config(page_title="🔍 Agentic Deep Researcher", layout="wide")


def _markdown_to_pdf_bytes(report: str) -> bytes:
    """
    Convert a markdown report string to PDF bytes using fpdf2.
    Simple approach: render all text preserving structure, minimal formatting.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    pdf.set_margins(10, 10, 10)
    
    # Set default font
    pdf.set_font("Helvetica", size=10)

    for raw_line in report.splitlines():
        line = raw_line.rstrip()
        
        # Empty lines
        if not line:
            pdf.ln(3)
            continue
        
        # Determine formatting and strip markdown
        font_style = ""
        font_size = 10
        text = line
        
        if line.startswith("# "):
            font_style = "B"
            font_size = 14
            text = line[2:]
        elif line.startswith("## "):
            font_style = "B"
            font_size = 12
            text = line[3:]
        elif line.startswith("### "):
            font_style = "B"
            font_size = 11
            text = line[4:]
        elif line.startswith("- "):
            text = "• " + line[2:]
        elif line.startswith("```"):
            continue  # Skip code fence lines
        else:
            # Clean inline markdown from regular text
            text = re.sub(r"\*\*(.+?)\*\*", r"", line)
            text = re.sub(r"\*(.+?)\*", r"", text)
            text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"", text)
            text = re.sub(r"`([^`]+)`", r"", text)
        
        # Encode safely
        try:
            text = text.encode("utf-8", "replace").decode("utf-8")
        except Exception:
            text = text.encode("ascii", "replace").decode("ascii")
        
        # Set font and render
        pdf.set_font("Helvetica", style=font_style, size=font_size)
        
        # Use write instead of multi_cell for more reliable rendering
        # This handles wrapping automatically without layout exceptions
        try:
            pdf.multi_cell(0, 5, text, align="L")
        except Exception:
            # Fallback: if multi_cell fails, skip the line rather than showing placeholder
            pass
    
    return bytes(pdf.output())

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "search_depth" not in st.session_state:
    st.session_state.search_depth = "advanced"
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_query" not in st.session_state:
    st.session_state.last_query = None
if "export_format" not in st.session_state:
    st.session_state.export_format = "None"

def reset_chat():
    st.session_state.messages = []
    st.session_state.search_depth = "advanced"
    st.session_state.last_result = None
    st.session_state.last_query = None
    st.session_state.export_format = "None"

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

    st.header("⚙️ Search Settings")
    st.session_state.search_depth = st.sidebar.selectbox(
        "Search Depth",
        ["basic", "advanced"],
        index=["basic", "advanced"].index(st.session_state.search_depth),
        help="'advanced' is slower but retrieves richer content. 'basic' is faster."
    )

    st.divider()
    if st.button("🔄 New Research Topic", use_container_width=True):
        reset_chat()
        st.rerun()

    # Export current research report
    if st.session_state.last_result:
        st.header("📥 Export Options")
        export_format = st.radio(
            "Select export format:",
            ["HTML", "PDF", "JSON"],
            horizontal=True,
            key="export_format_radio",
        )

        if export_format:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_q = re.sub(r"[^\w\s-]", "_", st.session_state.last_query)[:40]
            base_name = f"research_{safe_q}_{ts}"
            response = st.session_state.last_result["report"]

            if export_format == "HTML":
                html_body = markdown2.markdown(response, extras=["tables", "fenced-code-blocks"])
                html_full = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>{html_body}</body></html>"
                st.download_button(
                    label="⬇ Download as HTML",
                    data=html_full,
                    file_name=f"{base_name}.html",
                    mime="text/html",
                    key=f"html_export_{ts}",
                    use_container_width=True,
                )
            elif export_format == "PDF":
                st.download_button(
                    label="⬇ Download as PDF",
                    data=_markdown_to_pdf_bytes(response),
                    file_name=f"{base_name}.pdf",
                    mime="application/pdf",
                    key=f"pdf_export_{ts}",
                    use_container_width=True,
                )
            elif export_format == "JSON":
                export_data = {
                    "query": st.session_state.last_query,
                    "timestamp": ts,
                    "research_questions": st.session_state.last_result.get("research_questions", []),
                    "report": response,
                }
                st.download_button(
                    label="⬇ Download as JSON",
                    data=json.dumps(export_data, ensure_ascii=False, indent=2),
                    file_name=f"{base_name}.json",
                    mime="application/json",
                    key=f"json_export_{ts}",
                    use_container_width=True,
                )


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
        # Build conversation context
        previous_messages = st.session_state.messages[:-1]
        conversation_context = ""
        if previous_messages:
            context_parts = []
            for msg in previous_messages:
                if msg["role"] == "user":
                    context_parts.append(f"Q: {msg['content'][:300]}")
                else:
                    context_parts.append(f"Research Report: {msg['content'][:300]}")
            conversation_context = "\n".join(context_parts)

        response = ""
        result = {"report": "", "research_questions": []}

        _STEP_LABELS = {
            "planner":     "Planning research questions",
            "searcher":    "Searching the web",
            "synthesizer": "Synthesizing report",
        }

        with st.status("Researching...", expanded=True) as status:
            try:
                for event_type, data in stream_research(
                    prompt,
                    conversation_context=conversation_context,
                    search_depth=st.session_state.search_depth,
                ):
                    if event_type == "cache_hit":
                        status.update(label="Loaded from cache", state="complete", expanded=False)
                        response = data["report"]
                        result = {"report": response, "research_questions": []}
                        break
                    elif event_type == "node_done":
                        node = data["node"]
                        status.update(label=f"✓ {_STEP_LABELS.get(node, node)}", state="running")
                        if node == "planner":
                            questions = data["state"].get("research_questions", [])
                            if questions:
                                st.write(f"Generated {len(questions)} research questions")
                        elif node == "searcher":
                            search_res = data["state"].get("search_results", {})
                            total = sum(len(v) for v in search_res.values())
                            st.write(f"Retrieved {total} search results")
                    elif event_type == "complete":
                        status.update(label="Research complete", state="complete", expanded=False)
                        response = data["report"]
                        result = {"report": response, "research_questions": data.get("research_questions", [])}
                    elif event_type == "error":
                        status.update(label="Research failed", state="error")
                        response = f"## Research Error\n\n{data['message']}"
                        result = {"report": response, "research_questions": []}
            except Exception as e:
                status.update(label="Research failed", state="error")
                response = f"An error occurred: {str(e)}"
                result = {"report": response, "research_questions": []}


    with st.chat_message("assistant"):
        st.markdown(response)

    # Store result for sidebar export
    st.session_state.last_result = result
    st.session_state.last_query = prompt

    st.session_state.messages.append(
        {"role": "assistant", "content": response})

    # Enforce message limit: keep only last MAX_MESSAGES
    if len(st.session_state.messages) > MAX_MESSAGES:
        st.session_state.messages = st.session_state.messages[-MAX_MESSAGES:]
        st.info(f"💾 Chat history limited to last {MAX_MESSAGES} messages for token efficiency")
