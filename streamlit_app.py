import os
import streamlit as st
from dotenv import load_dotenv
from analyzer import DocumentationAnalyzer

def main():
    # Page config
    st.set_page_config(
        page_title="Documentation Analyzer",
        page_icon="📝",
        layout="wide"
    )

    # Header
    st.title("Documentation Analysis Tool 📝")
    st.markdown("""
    Analyze documentation for readability, structure, completeness, and style guidelines using AI.
    """)

    # Load API key
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API')
    
    if not api_key:
        st.error("Please set GOOGLE_API_KEY or GEMINI_API in your environment variables")
        return

    # URL input
    url = st.text_input("Enter documentation URL:", placeholder="https://docs.example.com/page")
    
    # Analysis options
    col1, col2 = st.columns(2)
    with col1:
        generate_revision = st.checkbox("Generate revised content", value=False)
    with col2:
        save_results = st.checkbox("Save results to files", value=False)

    if st.button("Analyze Documentation"):
        if not url:
            st.warning("Please enter a URL")
            return

        try:
            with st.spinner("Analyzing documentation..."):
                # Initialize analyzer
                analyzer = DocumentationAnalyzer(api_key=api_key)
                
                # Run analysis
                if generate_revision:
                    analysis, revised_content = analyzer.analyze_documentation(url)
                else:
                    analysis = analyzer.analyze_content(analyzer.scrape_page(url), url)
                    revised_content = None

                # Display results
                st.success("Analysis completed!")
                
                # Overall score
                st.header("Overall Score")
                overall_score = analyzer.calculate_overall_score(analysis)
                st.metric("Documentation Quality", overall_score)

                # Category results
                st.header("Analysis by Category")
                categories = ['readability', 'structure', 'completeness', 'style_guidelines']
                
                for category in categories:
                    if category in analysis:
                        with st.expander(f"{category.title().replace('_', ' ')}"):
                            data = analysis[category]
                            st.metric("Score", data.get('score', 'N/A'))
                            
                            if data.get('issues'):
                                st.subheader("Issues")
                                for issue in data['issues']:
                                    st.markdown(f"- {issue}")
                            
                            if data.get('suggestions'):
                                st.subheader("Suggestions")
                                for suggestion in data['suggestions']:
                                    st.markdown(f"- {suggestion}")

                # Revised content
                if revised_content:
                    st.header("Revised Content")
                    st.text_area("", revised_content, height=300)

                # Save results
                if save_results:
                    analyzer.save_results(url, analysis, revised_content if generate_revision else None)
                    st.success("Results saved to files!")

        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 
