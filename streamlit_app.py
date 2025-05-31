import streamlit as st
import os
from dotenv import load_dotenv
from analyzer import DocumentationAnalyzer

# Load environment variables
load_dotenv()

# Get API key from environment
api_key = os.getenv("GEMINI_API") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("Error: Google Gemini API key not found in .env file!")
    st.stop()

# Page config
st.set_page_config(
    page_title="Documentation Analyzer",
    page_icon="📝",
    layout="wide"
)

# Title and description
st.title("📝 Documentation Analysis Tool")
st.markdown("""
This tool analyzes documentation pages and provides structured feedback on:
- Readability for non-technical users
- Content structure and organization
- Information completeness
- Style guideline adherence
""")

# Main content
url = st.text_input(
    "Documentation URL",
    placeholder="https://docs.example.com/page",
    help="Enter the URL of the documentation page you want to analyze"
)

if st.button("Analyze Documentation", type="primary", disabled=not url):
    if not url.startswith(('http://', 'https://')):
        st.error("Please provide a valid URL starting with http:// or https://")
    else:
        try:
            # Create progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Initialize analyzer
            status_text.text("Initializing analyzer...")
            progress_bar.progress(10)
            analyzer = DocumentationAnalyzer(api_key)
            
            # Scrape and analyze
            status_text.text("Analyzing documentation... This may take a few minutes.")
            progress_bar.progress(30)
            analysis = analyzer.analyze_documentation(url)
            progress_bar.progress(90)
            
            # Display results
            status_text.text("Analysis complete!")
            progress_bar.progress(100)
            
            # Overall score
            overall_score = analyzer.calculate_overall_score(analysis)
            score_color = {
                "Excellent": "🟢",
                "Good": "🟡",
                "Fair": "🟠",
                "Poor": "🔴",
                "Unknown": "⚪"
            }.get(overall_score, "⚪")
            
            st.header("Analysis Results")
            st.subheader(f"Overall Score: {score_color} {overall_score}")
            
            # Display categories in columns
            categories = ['readability', 'structure', 'completeness', 'style_guidelines']
            cols = st.columns(2)
            
            for idx, category in enumerate(categories):
                col = cols[idx % 2]
                if category in analysis:
                    data = analysis[category]
                    with col:
                        st.markdown(f"### {category.upper().replace('_', ' ')}")
                        st.markdown(f"**Score:** {data.get('score', 'N/A')}")
                        
                        if data.get('issues'):
                            st.markdown("**Issues:**")
                            for issue in data['issues']:
                                st.markdown(f"- {issue}")
                        
                        if data.get('suggestions'):
                            st.markdown("**Suggestions:**")
                            for suggestion in data['suggestions']:
                                st.markdown(f"- {suggestion}")
                        
                        st.markdown("---")
            
            # Download button for JSON results
            import json
            from datetime import datetime
            
            result_data = {
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "overall_score": overall_score,
                "analysis": analysis
            }
            
            json_str = json.dumps(result_data, indent=2)
            st.download_button(
                label="Download Analysis Results (JSON)",
                data=json_str,
                file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
        finally:
            # Clear progress indicators
            if 'progress_bar' in locals():
                progress_bar.empty()
            if 'status_text' in locals():
                status_text.empty()

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using LangChain and Google Gemini") 