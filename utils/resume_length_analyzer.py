"""
Resume Length Analyzer Module

This module provides functions to analyze resume length based on word count.
Now includes experience-aware thresholds for more accurate categorization.
"""

def count_words(text):
    """
    Count the total number of words in text, excluding extra whitespaces, tabs, and newlines
    
    Args:
        text (str): The text to count words from
        
    Returns:
        int: Total word count
    """
    # Remove extra whitespaces, tabs, and newlines
    # Split by whitespace and filter out empty strings
    words = text.split()
    return len(words)


def categorize_resume_length_experience_based(word_count, resume_type):
    """
    Categorize resume length based on word count and experience level.
    
    Args:
        word_count (int): Total number of words in the resume
        resume_type (str): Experience level ('fresher', 'intermediate', or 'experienced')
        
    Returns:
        dict: Dictionary with category, color, and description
    """
    # Define thresholds for each experience level
    thresholds = {
        'fresher': {
            'too_short': 150,
            'good': 300,
            'slightly_long': 450
        },
        'intermediate': {
            'too_short': 250,
            'good': 450,
            'slightly_long': 650
        },
        'experienced': {
            'too_short': 350,
            'good': 650,
            'slightly_long': 900
        }
    }
    
    # Get thresholds for the experience level (default to experienced if unknown)
    level_thresholds = thresholds.get(resume_type, thresholds['experienced'])
    
    # Categorize based on word count and experience level
    if word_count < level_thresholds['too_short']:
        return {
            'category': 'Short',
            'color': '#FFBF00',  # Amber
            'description': f'Your resume is too brief for a {resume_type} level position'
        }
    elif word_count <= level_thresholds['good']:
        return {
            'category': 'Good',
            'color': '#10b981',  # Green
            'description': f'Your resume has an ideal length for a {resume_type} level position'
        }
    elif word_count <= level_thresholds['slightly_long']:
        return {
            'category': 'Long',
            'color': '#f97316',  # Orange
            'description': f'Your resume is detailed but slightly lengthy for a {resume_type} level position'
        }
    else:
        return {
            'category': 'Overly Long',
            'color': '#ef4444',  # Red
            'description': f'Your resume may be too long for a {resume_type} level position'
        }


def analyze_resume_length(resume_text, resume_type='experienced'):
    """
    Analyze resume length and return categorization based on experience level.
    
    Args:
        resume_text (str): The resume text content
        resume_type (str): Experience level ('fresher', 'intermediate', or 'experienced')
                          Defaults to 'experienced' for backward compatibility
        
    Returns:
        dict: Dictionary with word_count, category, color, description, and resume_type
    """
    
    word_count = count_words(resume_text)
    category_info = categorize_resume_length_experience_based(word_count, resume_type)
    
    
    return {
        'word_count': word_count,
        'category': category_info['category'],
        'color': category_info['color'],
        'description': category_info['description'],
        'resume_type': resume_type
    }
