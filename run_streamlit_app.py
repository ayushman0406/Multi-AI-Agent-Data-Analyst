#!/usr/bin/env python
# coding: utf-8

"""
Streamlit App Launcher
Simple script to launch the Multi-Agent Data Analysis Streamlit app
"""

import subprocess
import sys
from dotenv import load_dotenv
load_dotenv()
import os

def main():
    """Launch the Streamlit app."""
    print("🚀 Launching Multi-Agent Data Analysis Streamlit App...")
    print("📊 The app will open in your default web browser")
    print("🔗 If it doesn't open automatically, go to: http://localhost:8501")
    print("⏹️  Press Ctrl+C to stop the app")
    print("-" * 60)
    
    try:
        # Run streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 App stopped by user")
    except Exception as e:
        print(f"❌ Error launching app: {e}")
        print("💡 Make sure you have installed all requirements:")
        print("   pip install -r streamlit_requirements.txt")

if __name__ == "__main__":
    main()
