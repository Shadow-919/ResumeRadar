"""
Education Section Extractor

Extracts only the education section from resume text for more accurate education analysis.
Uses section detection from sections.json to isolate education content.
"""

import json
import os
import re


def load_sections_data():
    """Load section keywords from sections.json"""
    path = os.path.join("analysis_data", "sections.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_education_section(resume_text):
    """
    Extract only the education section from resume text
    
    Args:
        resume_text: Full resume text
        
    Returns:
        str: Extracted education section text, or full text if section not found
    """
    sections_data = load_sections_data()
    
    # Get all section keywords
    all_section_keywords = []
    education_keywords = []
    
    for section_name, section_info in sections_data["sections"].items():
        keywords = section_info["keywords"]
        all_section_keywords.extend(keywords)
        
        if section_name == "Education":
            education_keywords = keywords
    
    # Find education section start
    education_start = -1
    education_keyword_found = ""
    
    lines = resume_text.split('\n')
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        
        # Check if this line is an education section heading
        for keyword in education_keywords:
            # Match keyword as standalone heading (not part of larger text)
            if line_lower == keyword or \
               line_lower.startswith(keyword + ":") or \
               line_lower.startswith(keyword + " ") or \
               (len(line_lower) < 30 and keyword in line_lower and len(line_lower.split()) <= 3):
                education_start = i
                education_keyword_found = keyword
                break
        
        if education_start != -1:
            break
    
    # If education section not found, return full text
    if education_start == -1:
        return resume_text
    
    # Find the next section start (to know where education section ends)
    education_end = len(lines)
    
    for i in range(education_start + 1, len(lines)):
        line_lower = lines[i].lower().strip()
        
        # Skip empty lines
        if not line_lower:
            continue
        
        # Check if this line is a new section heading
        for keyword in all_section_keywords:
            # Skip the education keyword itself
            if keyword == education_keyword_found:
                continue
            
            # Match keyword as standalone heading
            if line_lower == keyword or \
               line_lower.startswith(keyword + ":") or \
               line_lower.startswith(keyword + " ") or \
               (len(line_lower) < 30 and keyword in line_lower and len(line_lower.split()) <= 3):
                education_end = i
                break
        
        if education_end != len(lines):
            break
    
    # Extract education section content (skip the heading line itself)
    education_lines = lines[education_start + 1:education_end]
    education_text = '\n'.join(education_lines).strip()
    
    # If extracted text is empty or too short, return full text as fallback
    if len(education_text) < 10:
        return resume_text
    
    return education_text


def save_education_section(resume_text, output_path):
    """
    Extract and optionally save education section to file
    
    Args:
        resume_text: Full resume text
        output_path: Path to save extracted education text (None for in-memory only)
        
    Returns:
        str: Extracted education text
    """
    education_text = extract_education_section(resume_text)
    
    # Save to file only if output_path is provided
    if output_path is not None:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(education_text)
    
    return education_text
