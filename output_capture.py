#!/usr/bin/env python
# coding: utf-8

"""
Output Capture Utility
Handles capturing and cleaning AI agent output for Streamlit display
"""

import re
import io
from dotenv import load_dotenv
load_dotenv()
from contextlib import redirect_stdout, redirect_stderr
import sys

class CleanOutputCapture:
    """Captures and cleans AI agent output for display."""
    
    def __init__(self):
        self.output_buffer = io.StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
    
    def __enter__(self):
        sys.stdout = self.output_buffer
        sys.stderr = self.output_buffer
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
    
    def get_clean_output(self):
        """Get cleaned output without terminal formatting codes."""
        raw_output = self.output_buffer.getvalue()
        
        # Remove various types of terminal formatting codes
        clean_output = raw_output
        
        # Remove ANSI escape sequences
        clean_output = re.sub(r'\x1b\[[0-9;]*m', '', clean_output)
        clean_output = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', clean_output)
        
        # Remove bracket color codes (like [36m, [0m, etc.)
        clean_output = re.sub(r'\[[0-9;]*m', '', clean_output)
        
        # Remove other common terminal codes
        clean_output = re.sub(r'\[[0-9;]*[a-zA-Z]', '', clean_output)
        
        # Keep the terminal box formatting but clean up color codes
        # Don't remove the box characters, just clean up the content
        
        # Clean up extra whitespace but preserve structure
        clean_output = re.sub(r'\n\s*\n\s*\n', '\n\n', clean_output)
        clean_output = clean_output.strip()
        
        return clean_output
    
    def get_raw_output(self):
        """Get raw output without cleaning."""
        return self.output_buffer.getvalue()

def clean_agent_output(text):
    """Clean agent output text for display."""
    if not text:
        return ""
    
    # Remove terminal formatting codes but preserve structure
    clean_text = re.sub(r'\x1b\[[0-9;]*m', '', text)
    clean_text = re.sub(r'\[[0-9;]*m', '', clean_text)
    clean_text = re.sub(r'\[[0-9;]*[a-zA-Z]', '', clean_text)
    
    # Keep the terminal box formatting - don't remove box characters
    # clean_text = re.sub(r'\|{20,}', '', clean_text)  # Commented out to preserve boxes
    
    # Clean up whitespace but preserve structure
    clean_text = re.sub(r'\n\s*\n\s*\n', '\n\n', clean_text)
    clean_text = clean_text.strip()
    
    return clean_text

def format_agent_output_for_streamlit(text):
    """Format agent output for better Streamlit display."""
    if not text:
        return "No output generated."
    
    # Clean the text
    clean_text = clean_agent_output(text)
    
    # Split into sections if there are clear separators
    sections = clean_text.split('\n\n')
    
    formatted_output = []
    for section in sections:
        section = section.strip()
        if section:
            # Check if it looks like a header
            if len(section) < 100 and ':' in section and not section.endswith('.'):
                formatted_output.append(f"**{section}**")
            else:
                formatted_output.append(section)
    
    return '\n\n'.join(formatted_output)
