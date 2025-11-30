"""
Section Analyzer Module

Improved version with more robust section and contact detection.

This module provides functions to analyze resume sections and determine which sections
are present or missing based on keyword matching and special rules.
"""

import json
import re
import os


def check_contact_info(resume_text):
    """
    Check if contact information is present using special rules
    
    Args:
        resume_text (str): The resume text to analyze
        
    Returns:
        bool: True if contact info is found (email OR phone), False otherwise
    """
    text = resume_text

    # --- Email detection (robust but safe) ---
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    has_email = bool(re.search(email_pattern, text))

    # --- Phone detection ---
    # Support:
    #   9876543210
    #   +91 98765 43210
    #   98765-43210
    #   (987) 654-3210
    # Strategy: look for sequences of digits, spaces, (), +, - with >= 10 digits total
    phone_candidate_pattern = r'[\+\d][\d\s\-\(\)]{8,}'
    has_phone = False

    for match in re.finditer(phone_candidate_pattern, text):
        chunk = match.group()
        digits = re.sub(r'\D', '', chunk)
        # Consider it a phone if it has at least 10 digits
        if len(digits) >= 10:
            has_phone = True
            break

    return has_email or has_phone


def _keyword_to_pattern(keyword: str) -> re.Pattern:
    """
    Convert a section keyword into a flexible regex pattern.

    - Case-insensitive
    - Spaces in keyword can match space, dash, pipe, or slash in text
      e.g., "work experience" -> matches "Work Experience", "Work-Experience", "Work | Experience"
    """
    kw = keyword.lower().strip()
    # Escape everything first
    escaped = re.escape(kw)
    # Replace escaped space with flexible separator: space, dash, pipe, slash, colon
    escaped = escaped.replace(r'\ ', r'[\s\-|/:]+')
    # Use custom "word-ish" boundaries to allow punctuation after headings
    pattern = r'(?<!\w)' + escaped + r'(?!\w)'
    return re.compile(pattern, re.IGNORECASE)


def analyze_sections(resume_text):
    """
    Analyze resume for section coverage
    
    Args:
        resume_text (str): The resume text to analyze
        
    Returns:
        dict: Dictionary with 'present' and 'missing' section lists
    """
    # Load sections data from analysis_data folder
    sections_file_path = os.path.join('analysis_data', 'sections.json')
    
    with open(sections_file_path, 'r', encoding='utf-8') as f:
        sections_data = json.load(f)
    
    resume_lower = resume_text.lower()

    present_sections = []
    missing_sections = []
    
    for section_name, section_info in sections_data['sections'].items():
        # Special handling for Contact Info
        if section_info.get('special_rule'):
            if check_contact_info(resume_text):
                present_sections.append(section_name)
            else:
                missing_sections.append(section_name)
        else:
            found = False
            for keyword in section_info['keywords']:
                pattern = _keyword_to_pattern(keyword)
                if pattern.search(resume_lower):
                    found = True
                    break
            
            if found:
                present_sections.append(section_name)
            else:
                missing_sections.append(section_name)
    
    return {
        'present': present_sections,
        'missing': missing_sections
    }
