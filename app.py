# app.py
import streamlit as st
from PyPDF2 import PdfReader
import tempfile
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.llms import Ollama
from langchain.chains import RetrievalQA
import base64

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(page_title="My Book QA", page_icon="📚", layout="wide")
st.title("📚 Upload, Read & Ask Questions from Your Book")

# -------------------------------
# Session State Init
# -------------------------------
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False

# -------------------------------
# File Uploader
# -------------------------------
uploaded_file = st.file_uploader("Upload your book (PDF)", type="pdf")

if uploaded_file:
    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(uploaded_file.getvalue())
        temp_path = f.name

    # -------------------------------
    # PDF Viewer
    # -------------------------------
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("📖 PDF Preview")
        with open(temp_path, "rb") as pdf_file:
            base64_pdf = base64.b64encode(pdf_file.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

    # -------------------------------
    # Extract Text + Build RAG
    # -------------------------------
    with col2:
        st.subheader("🔄 Processing Book...")
        reader = PdfReader(temp_path)
        num_pages = len(reader.pages)
        st.write(f"Pages: **{num_pages}**")

        # Extract full text
        with st.spinner("Extracting text..."):
            raw_text = ""
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    raw_text += text

        if not raw_text.strip():
            st.error("No text found. Is this a scanned PDF? Use OCR version.")
            st.stop()

        # Split into chunks
        with st.spinner("Splitting into chunks..."):
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = splitter.split_text(raw_text)

        # Create embeddings + vector DB
        with st.spinner("Building knowledge base..."):
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            vectorstore = FAISS.from_texts(chunks, embeddings)
            st.session_state.vectorstore = vectorstore

        # Setup LLM + QA Chain
        with st.spinner("Loading LLM (Llama 3)..."):
            llm = Ollama(model="llama3", temperature=0.2)
            retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True
            )
            st.session_state.qa_chain = qa_chain
            st.session_state.pdf_processed = True

        st.success("✅ Book loaded! Ask anything below.")

    # -------------------------------
    # Q&A Section
    # -------------------------------
    if st.session_state.pdf_processed:
        st.markdown("---")
        st.subheader("❓ Ask a Question")
        question = st.text_input("Your question:", placeholder="e.g., What is the main theme of the book?")

        if question:
            with st.spinner("Thinking..."):
                result = st.session_state.qa_chain({"query": question})
                answer = result["result"]
                sources = result["source_documents"]

            st.markdown("### 📝 Answer")
            st.write(answer)

            with st.expander("🔍 View Sources"):
                for i, doc in enumerate(sources):
                    st.markdown(f"**Source {i+1}:**")
                    st.code(doc.page_content[:500] + ("..." if len(doc.page_content) > 500 else ""), language=None)

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

else:
    st.info("👆 Upload a PDF to start reading and asking!")
    st.markdown("""
    ### Features
    - Upload any book (PDF)  
    - View it in-browser  
    - Ask questions → **answers only from your book**  
    - 100% local (Ollama + FAISS)  
    - No internet, no API keys  
    """)