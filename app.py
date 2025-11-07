# app.py
import streamlit as st
from PyPDF2 import PdfReader
import tempfile
import os

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(
    page_title="My Book Reader",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Upload & Read Your Book (PDF)")

# -------------------------------
# File Uploader
# -------------------------------
uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"],
    help="Upload any book in PDF format"
)

if uploaded_file is not None:
    # -------------------------------
    # Save uploaded file temporarily
    # -------------------------------
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    # -------------------------------
    # Read PDF Metadata & Pages
    # -------------------------------
    try:
        reader = PdfReader(tmp_file_path)
        num_pages = len(reader.pages)
        st.success(f"✅ PDF loaded successfully! **{num_pages} pages**")

        # -------------------------------
        # Show PDF Viewer
        # -------------------------------
        st.subheader("📖 View PDF")
        with open(tmp_file_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
        st.download_button(
            label="⬇️ Download PDF",
            data=pdf_bytes,
            file_name=uploaded_file.name,
            mime="application/pdf"
        )

        # Embed PDF viewer (works in most browsers)
        st.markdown(f"""
        <iframe src="data:application/pdf;base64,{uploaded_file.getvalue().decode('latin-1')}" 
                width="100%" height="800px" style="border:none;"></iframe>
        """, unsafe_allow_html=True)

        # -------------------------------
        # Extract & Show Text
        # -------------------------------
        st.subheader("📄 Extracted Text")
        page_number = st.slider("Select Page to Read", 1, num_pages, 1)
        page = reader.pages[page_number - 1]
        page_text = page.extract_text()

        if page_text.strip():
            st.text_area(f"Text from Page {page_number}", page_text, height=300)
        else:
            st.warning("No text extracted from this page (maybe scanned/image-based).")

        # -------------------------------
        # Full Text Extraction (Optional)
        # -------------------------------
        with st.expander("🔍 View Full Extracted Text"):
            full_text = ""
            for i, page in enumerate(reader.pages):
                full_text += f"\n\n--- Page {i+1} ---\n"
                full_text += page.extract_text() or "(No text - image page)"
            st.download_button(
                "⬇️ Download Full Text",
                full_text,
                file_name=f"{uploaded_file.name}_full_text.txt",
                mime="text/plain"
            )
            st.code(full_text[:5000] + ("\n\n... (truncated)" if len(full_text) > 5000 else ""), language=None)

    except Exception as e:
        st.error(f"Error reading PDF: {e}")

    finally:
        # Clean up temp file
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)

else:
    st.info("👆 Please upload a PDF to get started.")
    st.markdown("""
    ### Features
    - Upload any book in PDF  
    - View it directly in the app  
    - Read page-by-page  
    - Extract & download full text  
    """)