# Documentation Analysis Tool 📝

A powerful documentation analysis tool that uses LangChain and Google's Gemini AI to analyze documentation pages and provide structured feedback on readability, structure, completeness, and style guidelines.

## Features 🌟

- **Automated Documentation Analysis**: Analyzes documentation pages for multiple quality aspects
- **Comprehensive Feedback**: Provides detailed feedback on:
  - Readability for non-technical users
  - Content structure and organization
  - Information completeness
  - Style guideline adherence
- **Multiple Interfaces**: 
  - Web interface using Streamlit
  - Command-line interface
- **Flexible Output**: Results available in both human-readable format and downloadable JSON
- **Robust Web Scraping**: Advanced content extraction with multiple fallback strategies

## Prerequisites 🛠️

- Python 3.8 or higher
- Google Gemini API key
- Chrome/Chromium browser (for Selenium)

## Installation 🔧

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables by creating a `.env` file:
```env
GEMINI_API=your_gemini_api_key_here
# or
GOOGLE_API_KEY=your_gemini_api_key_here
```

## Usage 💻

### Streamlit Interface

1. Start the Streamlit app:
```bash
streamlit run streamlit_app.py
```

2. Open your browser and navigate to the provided URL (typically http://localhost:8501)

3. Enter your documentation URL and click "Analyze Documentation"

### Command Line Interface

Run the analyzer from the command line:
```bash
python main.py https://your-documentation-url.com
```

## Project Structure 📁

```
.
├── README.md
├── requirements.txt
├── .env
├── main.py                 # Command-line interface
├── streamlit_app.py        # Streamlit web interface
├── analyzer.py            # Core analysis functionality
└── models.py             # Data models
```

## Analysis Categories 📊

1. **Readability**
   - Assesses how easily non-technical users can understand the content
   - Evaluates language complexity and clarity

2. **Structure**
   - Analyzes content organization
   - Evaluates heading hierarchy and flow

3. **Completeness**
   - Checks for comprehensive coverage
   - Identifies potential information gaps

4. **Style Guidelines**
   - Evaluates adherence to documentation best practices
   - Checks consistency in formatting and tone

## Output Format 📋

The analysis results include:
- Overall score (Excellent, Good, Fair, Poor)
- Category-specific scores
- Identified issues
- Improvement suggestions

Example JSON output:
```json
{
  "url": "https://docs.example.com",
  "timestamp": "2024-02-20T10:30:00Z",
  "overall_score": "Good",
  "analysis": {
    "readability": {
      "score": "Good",
      "issues": [...],
      "suggestions": [...]
    },
    ...
  }
}
```

## Error Handling 🔍

The tool includes robust error handling for:
- Invalid URLs
- Network issues
- Content extraction failures
- API errors

## Contributing 🤝

Contributions are welcome! Please feel free to submit pull requests.

## License 📄

[Your chosen license]

## Acknowledgments 🙏

- LangChain for the AI framework
- Google Gemini for AI capabilities
- Streamlit for the web interface
- Selenium for web scraping

---
Made with ❤️ using LangChain and Google Gemini 