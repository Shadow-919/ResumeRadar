"""
Action Verb Analyzer Module

Analyzes action verb usage in resume text and computes density metrics.
Uses word count from resume_length_analyzer for consistency.
Applies experience-specific thresholds for more accurate categorization.
"""

import json
import os
import re
from collections import Counter


def categorize_resume_by_experience(years, months):
    """
    Categorize resume by total experience.
    
    Args:
        years (int): Total years of experience
        months (int): Additional months of experience
        
    Returns:
        str: Experience level ('fresher', 'intermediate', or 'experienced')
    """
    total_months = (years * 12) + months
    
    if total_months < 12:  # Less than 1 year
        return 'fresher'
    elif total_months < 36:  # 1-3 years
        return 'intermediate'
    else:  # 3+ years
        return 'experienced'


def get_density_category(density, experience_level):
    """
    Get action verb density category based on experience level.
    
    Args:
        density (float): Action verb density percentage
        experience_level (str): 'fresher', 'intermediate', or 'experienced'
        
    Returns:
        tuple: (category, color, description)
    """
    # Define thresholds for each experience level
    thresholds = {
        'fresher': {
            'very_weak': 0.40,
            'weak': 0.80,
            'average': 1.40,
            'strong': 2.50
        },
        'intermediate': {
            'very_weak': 0.30,
            'weak': 0.60,
            'average': 1.20,
            'strong': 2.00
        },
        'experienced': {
            'very_weak': 0.20,
            'weak': 0.45,
            'average': 0.80,
            'strong': 1.60
        }
    }
    
    # Get thresholds for the experience level (default to experienced if unknown)
    level_thresholds = thresholds.get(experience_level, thresholds['experienced'])
    
    # Categorize based on density
    if density < level_thresholds['very_weak']:
        return (
            "Very Weak",
            "#ef4444",  # red
            "Your resume uses very few action verbs and may feel passive."
        )
    elif density < level_thresholds['weak']:
        return (
            "Weak",
            "#f97316",  # orange
            "Your resume has some action verbs but could be more impactful."
        )
    elif density < level_thresholds['average']:
        return (
            "Average",
            "#3b82f6",  # blue
            "Your action verb usage is acceptable but can still be strengthened."
        )
    elif density < level_thresholds['strong']:
        return (
            "Strong",
            "#10b981",  # green
            "Your resume has strong use of action verbs and shows good initiative."
        )
    else:
        return (
            "Outstanding",
            "#8b5cf6",  # purple
            "Your resume has excellent action verb density and is highly impactful."
        )


def analyze_action_verbs(resume_text, word_count, experience_years=0, experience_months=0):
    """
    Analyze action verb usage in the resume text with experience-based thresholds.
    
    Args:
        resume_text (str): Raw resume text
        word_count (int): Total word count from resume_length_analyzer
        experience_years (int): Total years of experience (optional, default=0)
        experience_months (int): Additional months of experience (optional, default=0)
        
    Returns:
        dict: Dictionary containing:
            - action_verb_count (int): Count of action verb occurrences
            - category (str): Category based on density and experience
            - color (str): Hex color for category
            - description (str): Description of the category
            - resume_type (str): Experience level classification
    """
    # Load action verbs from JSON
    try:
        verbs_path = os.path.join("analysis_data", "large_action_verbs.json")
        with open(verbs_path, 'r', encoding='utf-8') as f:
            verbs_data = json.load(f)
        
        # Normalize to lowercase and store in set for fast lookup
        action_verbs_set = set(verb.lower() for verb in verbs_data['action_verbs'])
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        # Fallback if file not found or malformed
        print(f"Warning: Could not load action verbs: {e}")
        action_verbs_set = set()
    
    # Categorize resume by experience
    resume_type = categorize_resume_by_experience(experience_years, experience_months)
    
    # Handle empty text or zero word count
    if not resume_text or not resume_text.strip() or word_count == 0:
        return {
            "action_verb_count": 0,
            "category": "Unknown",
            "color": "#666666",
            "description": "Unable to analyze action verbs (no text).",
            "resume_type": resume_type
        }
    
    # Tokenize words (lowercase for matching)
    text_lower = resume_text.lower()
    tokens = re.findall(r"\b\w+\b", text_lower)
    
    # Count word occurrences
    word_counts = Counter(tokens)
   
    # Calculate action verb count (sum of occurrences of action verbs)
    action_verb_count = sum(word_counts[word] for word in action_verbs_set if word in word_counts)
    
    # Calculate density as percentage using external word count
    density = (action_verb_count / word_count) * 100 if word_count > 0 else 0.0
    
    # Get category based on experience level and density
    category, color, description = get_density_category(density, resume_type)
    
    return {
        "action_verb_count": action_verb_count,
        "category": category,
        "color": color,
        "description": description,
        "resume_type": resume_type
    }
