"""
Name Extractor Module

Extracts candidate name from resume text using intelligent heuristics.
Analyzes only the first 3 lines and applies filtering rules.
"""

import re


def extract_name(resume_text):
    """
    Extract candidate name from resume text.
    
    Args:
        resume_text (str): Raw resume text (BEFORE lowercase conversion)
        
    Returns:
        str: Extracted name or empty string if not found
    """
    lines = resume_text.split("\n")
    top_lines = [l.strip() for l in lines[:3] if l.strip()]
    
    clean_candidates = []
    for line in top_lines:
        line_lower = line.lower()
        
        # Skip non-name lines
        if any(x in line_lower for x in ["@", "http", "linkedin", "github", "portfolio",
                                         "resume", "curriculum", "vitae", "cv"]):
            continue
        if re.search(r"\d", line):
            continue
        
        words = line.split()
        if 1 <= len(words) <= 4:
            clean_candidates.append(line)
    
    if not clean_candidates:
        return ""
    
    # Prefer lines with 2-3 words (typical name format)
    clean_candidates.sort(key=lambda x: abs(len(x.split()) - 2))
    return clean_candidates[0]
