"""
Contact Extractor Module

Extracts email and phone number from resume text using regex patterns.
"""

import re


def extract_email(resume_text):
    """Extract email address from resume text."""
    if not resume_text or not resume_text.strip():
        return ""
    
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, resume_text)
    
    return match.group() if match else ""


def extract_phone(resume_text):
    """
    Extract and normalize phone number.
    Ensures return is always EXACT 10 digits (Indian mobile number).
    Removes +91, 91, prefixes, symbols, and spaces.
    """
    if not resume_text or not resume_text.strip():
        return ""
    
    # Find any number sequence with at least 10 digits
    phone_pattern = r'[\+\d][\d\s\-\(\)]{8,}'
    matches = re.findall(phone_pattern, resume_text)
    
    for match in matches:
        digits = re.sub(r'\D', '', match)  # Keep only digits
        
        # If number has 10+ digits → return last 10 (removes 91, +91, 0091, etc.)
        if len(digits) >= 10:
            return digits[-10:]
    
    return ""
