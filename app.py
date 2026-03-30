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
    Handles: H1 (#), H2 (##), H3 (###), bold (**text**), lists, and plain text.
    Returns raw PDF bytes suitable for st.download_button.
    """
    from fpdf.errors import FPDFException
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    def safe_encode(text: str) -> str:
        """Encode text to latin-1 with fallback for unsupported chars."""
        try:
            return text.encode("latin-1", "replace").decode("latin-1")
        except Exception:
            return text

    def wrap_long_text(text: str, max_length: int = 100) -> str:
        """Insert breaks in very long words to prevent layout issues."""
        words = text.split()
        result = []
        for word in words:
            if len(word) > max_length:
                # Break long words every max_length chars
                for i in range(0, len(word), max_length):
                    result.append(word[i:i+max_length])
            else:
                result.append(word)
        return " ".join(result)

    def safe_multi_cell(pdf_obj, width, height, text):
        """Safely add multi_cell, handling layout exceptions."""
        try:
            pdf_obj.multi_cell(width, height, text)
        except FPDFException:
            # If text doesn't fit, try wrapping long words and retry
            try:
                wrapped = wrap_long_text(text, 80)
                pdf_obj.multi_cell(width, height, wrapped)
            except FPDFException:
                # If still doesn't fit, use smaller font or skip
                try:
                    pdf_obj.set_font("Helvetica", size=8)
                    pdf_obj.multi_cell(width, height, wrapped)
                except FPDFException:
                    # Last resort: add a placeholder line
                    pdf_obj.set_font("Helvetica", size=10)
                    pdf_obj.cell(0, 6, "[Content too long to render]")
                    pdf_obj.ln()

    for raw_line in report.splitlines():
        line = raw_line.rstrip()

        # Skip empty encoding issues, just process the line
        if not line:
            pdf.ln(4)
            continue

        # Process headers
        if line.startswith("# "):
            pdf.set_font("Helvetica", style="B", size=16)
            safe_multi_cell(pdf, 0, 10, safe_encode(line[2:]))
        elif line.startswith("## "):
            pdf.set_font("Helvetica", style="B", size=14)
            safe_multi_cell(pdf, 0, 8, safe_encode(line[3:]))
        elif line.startswith("### "):
            pdf.set_font("Helvetica", style="B", size=12)
            safe_multi_cell(pdf, 0, 7, safe_encode(line[4:]))
        # Process bullet points and numbered lists
        elif line.startswith("- "):
            pdf.set_font("Helvetica", size=10)
            # Add bullet point indentation
            safe_multi_cell(pdf, 0, 6, "• " + safe_encode(line[2:]))
        elif re.match(r"^\d+\.\s", line):
            pdf.set_font("Helvetica", size=10)
            # Keep numbered format
            safe_multi_cell(pdf, 0, 6, safe_encode(line))
        # Process code blocks
        elif line.startswith("```"):
            pdf.set_font("Courier", size=9)
            pdf.ln(2)
        # Regular text
        else:
            # Clean markdown formatting but preserve content
            clean = re.sub(r"\*\*(.+?)\*\*", r"", line)  # Remove bold markers
            clean = re.sub(r"\*(.+?)\*", r"", clean)      # Remove italic markers
            clean = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"", clean)  # Remove links but keep text
            clean = re.sub(r"`([^`]+)`", r"", clean)      # Remove inline code markers
            pdf.set_font("Helvetica", size=10)
            safe_multi_cell(pdf, 0, 6, safe_encode(clean))

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
