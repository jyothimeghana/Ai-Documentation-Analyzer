#!/usr/bin/env python3
"""
LangChain-Powered Documentation Improvement Agent
Analyzes MoEngage documentation and suggests improvements using LangChain.
"""

import os
import sys
from dotenv import load_dotenv
from analyzer import DocumentationAnalyzer

def main():
    """Main function to run the documentation analyzer."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get API key
        GEMINI_API_KEY = os.getenv("GEMINI_API") or os.getenv("GOOGLE_API_KEY")
        if not GEMINI_API_KEY:
            print("Error: Google Gemini API key not found!")
            sys.exit(1)
        
        # Get URL from command line or user input
        if len(sys.argv) < 2:
            url = input("Enter the MoEngage documentation URL: ").strip()
            if not url:
                print("No URL provided. Exiting.")
                sys.exit(1)
        else:
            url = sys.argv[1]
        
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            print("Please provide a valid URL starting with http:// or https://")
            sys.exit(1)
        
        print("Starting LangChain-powered documentation analysis...")
        print("This may take a few minutes...\n")
        
        # Initialize analyzer
        analyzer = DocumentationAnalyzer(GEMINI_API_KEY)
        
        # Run analysis
        analysis = analyzer.analyze_documentation(url)
        
        # Display and save results
        analyzer.print_results(url, analysis)
        analyzer.save_results(url, analysis)
        
        print("\n" + "="*60)
        print("LANGCHAIN ANALYSIS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 