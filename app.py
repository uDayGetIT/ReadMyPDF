import streamlit as st
import fitz  # PyMuPDF
import requests
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Inject minimal CSS for clean theme
st.markdown(
    """
    <style>
    body {
        background-color: #f7f7f7;
        color: #333333;
        font-family: 'Segoe UI', sans-serif;
    }
    .stButton > button, .stDownloadButton > button {
        background-color: #2a6cd6;
        color: white;
        border-radius: 4px;
        border: none;
        padding: 0.4em 1em;
    }
    .stRadio > div {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 0.5em;
    }
    .stTextInput > div > input {
        border-radius: 4px;
        border: 1px solid #ccc;
        padding: 0.5em;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Summarizer
def summarize_text(document_text):
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "llama3-8b-8192",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a professional summarizer. Please produce a concise, clear summary with 5 bullet points, "
                        "focused on the most relevant points for business users."
                    )
                },
                {"role": "user", "content": document_text[:6000]}
            ],
            "temperature": 0.2,
        }
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=45
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error while summarizing: {e}")
        return ""

# Q&A
def ask_about_document(document_text, question):
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        prompt = (
            f"Document:\n{document_text[:6000]}\n\n"
            f"Question: {question}\n\n"
            "Answer accurately using the document only. If unsure, reply with 'I don't know.'"
        )
        data = {
            "model": "llama3-8b-8192",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a precise, business-like assistant. Only answer based on the provided document."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
        }
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=45
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error answering the question: {e}")
        return "Sorry, I couldn’t answer."

# PDF
def extract_text(uploaded_file):
    try:
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            return "".join(page.get_text() for page in doc)
    except Exception as e:
        st.error(f"Error reading the PDF: {e}")
        return ""

# Streamlit config
st.set_page_config(page_title="PDF Document Assistant", layout="wide")

st.title("PDF Document Assistant")
st.write("""
Upload a PDF document, then select to either get a concise summary or ask questions about its contents.
""")

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

if uploaded_file:
    document_text = extract_text(uploaded_file)
    if not document_text.strip():
        st.warning("This PDF seems empty or could not be parsed.")
    else:
        st.session_state["document_text"] = document_text

        mode = st.radio(
            "Choose your mode:",
            ["Summarize", "Ask Questions"]
        )

        if mode == "Summarize":
            st.subheader("Summary")
            with st.spinner("Creating summary, please wait..."):
                summary = summarize_text(document_text)
            st.success("Summary completed.")
            st.markdown(summary)

            st.download_button(
                "Download Summary",
                data=summary,
                file_name="summary.txt",
                mime="text/plain"
            )

        elif mode == "Ask Questions":
            st.subheader("Ask about this Document")
            question = st.text_input("Type your question here:")
            if st.button("Get Answer"):
                if question.strip() == "":
                    st.warning("Please enter a question.")
                else:
                    with st.spinner("Getting answer..."):
                        answer = ask_about_document(document_text, question)
                    st.success("Answer:")
                    st.write(answer)
else:
    st.info("Please upload a PDF file above to begin.")
