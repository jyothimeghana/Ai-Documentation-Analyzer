#!/usr/bin/env python3
"""
LangChain-Powered Documentation Improvement Agent
Analyzes MoEngage documentation and suggests improvements using LangChain.
"""

import os
import argparse
from dotenv import load_dotenv
from analyzer import DocumentationAnalyzer

def main():
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API')
    if not api_key:
        raise ValueError("Please set GOOGLE_API_KEY or GEMINI_API in your environment variables")

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Analyze documentation for quality and readability.')
    parser.add_argument('url', help='URL of the documentation to analyze')
    parser.add_argument('--save', action='store_true', help='Save results to files')
    parser.add_argument('--revise', action='store_true', help='Generate revised content')
    args = parser.parse_args()

    try:
        # Initialize analyzer
        analyzer = DocumentationAnalyzer(api_key=api_key)
        
        # Analyze documentation
        if args.revise:
            analysis, revised_content = analyzer.analyze_documentation(args.url)
        else:
            analysis = analyzer.analyze_content(analyzer.scrape_page(args.url), args.url)
            revised_content = None

        # Print results
        analyzer.print_results(args.url, analysis, revised_content if args.revise else None)

        # Save results if requested
        if args.save:
            analyzer.save_results(args.url, analysis, revised_content if args.revise else None)

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main()) 
