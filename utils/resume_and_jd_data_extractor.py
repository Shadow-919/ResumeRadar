"""
Resume and Job Description Data Extractor Module
Improved Version Using PyMuPDF for Accurate PDF Extraction
IN-MEMORY PROCESSING - No disk writes
"""

import fitz  # PyMuPDF
from docx import Document
from io import BytesIO


def extract_text_from_pdf(file_bytes):
    """
    Extract text from PDF using PyMuPDF (in-memory processing)
    
    Args:
        file_bytes (bytes): PDF file content as bytes
        
    Returns:
        str: Extracted text from the PDF
    """
    text = ""
    try:
        # Open PDF from memory using BytesIO
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page in doc:
            # Extract text in "text" mode (best for structured text)
            page_text = page.get_text("text")
            if page_text:
                text += page_text + "\n"
        doc.close()
    except Exception as e:
        print(f"Error extracting PDF using PyMuPDF: {e}")
    
    return text


def extract_text_from_docx(file_bytes):
    """
    Extract text from DOCX file (in-memory processing)
    
    Args:
        file_bytes (bytes): DOCX file content as bytes
        
    Returns:
        str: Extracted text from the DOCX
    """
    text = ""
    try:
        # Open DOCX from memory using BytesIO
        doc = Document(BytesIO(file_bytes))
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        print(f"Error extracting DOCX: {e}")
    return text


def extract_resume_text(file_bytes, filename):
    """
    Extract text from resume based on file type (in-memory processing)
    
    Args:
        file_bytes (bytes): Resume file content as bytes
        filename (str): Name of the file (used to determine extension)
        
    Returns:
        str: Extracted text from the resume
    """
    extension = filename.rsplit('.', 1)[1].lower()
    
    if extension == 'pdf':
        return extract_text_from_pdf(file_bytes)
    elif extension == 'docx':
        return extract_text_from_docx(file_bytes)
    
    return ""

