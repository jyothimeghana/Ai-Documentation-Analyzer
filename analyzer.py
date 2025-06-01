import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from models import DocumentationAnalysis

def load_prompt_template(template_type: str) -> List[tuple]:
    """Load prompt templates for analysis or revision."""
    if template_type == "analysis":
        return [
            ("system", """You are an expert technical writer analyzing documentation. 
            Analyze the provided content and return structured feedback in the exact JSON format specified.
            
            Focus on:
            - Readability for non-technical users
            - Clear structure and organization
            - Completeness of information
            - Adherence to documentation style guidelines
            
            For each category, you MUST provide:
            1. A score that is EXACTLY one of: ["Excellent", "Good", "Fair", "Poor"]
            2. At least one specific issue identified
            3. At least one actionable suggestion for improvement
            
            If the content cannot be properly analyzed (e.g., error pages, security checks), score it as "Poor" and explain why.
            
            {format_instructions}"""),
            ("human", """
            Content to analyze:
            {content}
            
            Provide detailed analysis with specific, actionable feedback for each category.
            Remember to use ONLY the allowed scores: "Excellent", "Good", "Fair", or "Poor".
            """)
        ]
    elif template_type == "revision":
        return [
            ("system", """You are an expert technical writer. 
            Revise the provided content based on the analysis feedback to improve its quality.
            Keep the core information intact while enhancing:
            - Readability
            - Structure
            - Completeness
            - Style consistency"""),
            ("human", """
            Original content:
            {original_content}
            
            Analysis feedback:
            {feedback}
            
            Please provide the revised content maintaining the original information while implementing the suggested improvements.
            """)
        ]
    else:
        raise ValueError(f"Unknown template type: {template_type}")

class DocumentationAnalyzer:
    """Main class for analyzing documentation using LangChain."""
    
    def __init__(self, api_key: str):
        """Initialize the analyzer with LangChain components."""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.3,  # Added for more consistent outputs
        )
        
        # Initialize parsers
        self.json_parser = JsonOutputParser(pydantic_object=DocumentationAnalysis)
        self.str_parser = StrOutputParser()
        
        # Load prompt templates
        self.analysis_prompt = ChatPromptTemplate.from_messages(load_prompt_template("analysis"))
        self.revision_prompt = ChatPromptTemplate.from_messages(load_prompt_template("revision"))
        
        # Create chains
        self.analysis_chain = self.analysis_prompt | self.llm | self.json_parser
        self.revision_chain = self.revision_prompt | self.llm | self.str_parser

    def scrape_page(self, url: str) -> str:
        """Scrape content from a documentation page."""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=options)
        
        try:
            print(f"Scraping content from: {url}")
            driver.get(url)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            time.sleep(15)
            
            content_parts = []
            main_selectors = [
                "main", ".main-content", "#main-content", 
                ".article-content", ".content", ".post-content",
                ".entry-content", "[role='main']"
            ]
            
            # Try multiple content extraction strategies
            for selector in main_selectors:
                try:
                    main_element = driver.find_element(By.CSS_SELECTOR, selector)
                    if main_element and main_element.text.strip():
                        elements = main_element.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6, p, ul, ol, li, pre, code, div")
                        for element in elements:
                            text = element.text.strip()
                            if text and len(text) > 10:
                                tag = element.tag_name.lower()
                                if tag.startswith('h') and len(tag) == 2:
                                    content_parts.append(f"\n{'#' * int(tag[1])} {text}\n")
                                else:
                                    content_parts.append(text)
                        break
                except Exception:
                    continue
            
            if not content_parts:
                content_text = driver.execute_script("""
                    var scripts = document.querySelectorAll('script, style, nav, footer, header, .nav, .footer, .header');
                    scripts.forEach(function(el) { el.remove(); });
                    var mainContent = document.querySelector('main, .main-content, #main-content, .article-content, .content') || document.body;
                    return mainContent.innerText || mainContent.textContent || '';
                """)
                if content_text:
                    content_parts = [content_text.strip()]
            
            if content_parts:
                content = "\n\n".join(content_parts)
                lines = [line.strip() for line in content.split('\n') if line.strip() and len(line.strip()) > 3]
                return "\n".join(lines)
            
            raise Exception("No substantial content found")
            
        except Exception as e:
            print(f"Error scraping page: {e}")
            raise
        finally:
            driver.quit()

    def validate_analysis_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix analysis results to ensure valid scores."""
        valid_scores = {"Excellent", "Good", "Fair", "Poor"}
        categories = ["readability", "structure", "completeness", "style_guidelines"]
        
        validated = {}
        for category in categories:
            category_data = result.get(category, {})
            
            # Ensure valid score
            score = category_data.get("score", "Poor")
            if score not in valid_scores:
                print(f"Warning: Invalid score '{score}' in {category}, defaulting to 'Poor'")
                score = "Poor"
            
            # Ensure issues and suggestions exist
            issues = category_data.get("issues", [])
            if not issues:
                issues = ["Content could not be properly analyzed"]
            
            suggestions = category_data.get("suggestions", [])
            if not suggestions:
                suggestions = ["Review and update the content with proper documentation"]
            
            validated[category] = {
                "score": score,
                "issues": issues,
                "suggestions": suggestions
            }
        
        return validated

    def analyze_content(self, content: str, url: str) -> Dict[str, Any]:
        """Analyze content using LangChain and return structured results."""
        try:
            print("Analyzing content...")
            format_instructions = self.json_parser.get_format_instructions()
            
            result = self.analysis_chain.invoke({
                "content": content,
                "format_instructions": format_instructions
            })
            
            # Convert to dict if needed
            analysis_dict = result if isinstance(result, dict) else result.dict()
            
            # Validate and fix the results
            validated_result = self.validate_analysis_result(analysis_dict)
            
            return validated_result
            
        except Exception as e:
            print(f"Analysis error: {e}")
            # Return a valid default structure
            return self.validate_analysis_result({})

    def revise_content(self, original_content: str, analysis: Dict[str, Any]) -> str:
        """Revise content based on analysis feedback."""
        try:
            print("Generating revised content...")
            
            # Format analysis feedback
            feedback_parts = []
            for category, data in analysis.items():
                feedback_parts.append(f"\n{category.title()} Analysis:")
                feedback_parts.append(f"Score: {data.get('score', 'N/A')}")
                
                if data.get('issues'):
                    feedback_parts.append("Issues:")
                    for issue in data['issues']:
                        feedback_parts.append(f"- {issue}")
                
                if data.get('suggestions'):
                    feedback_parts.append("Suggestions:")
                    for suggestion in data['suggestions']:
                        feedback_parts.append(f"- {suggestion}")
            
            feedback = "\n".join(feedback_parts)
            
            # Generate revised content
            revised_content = self.revision_chain.invoke({
                "original_content": original_content,
                "feedback": feedback
            })
            
            return revised_content
            
        except Exception as e:
            print(f"Revision error: {e}")
            raise

    def calculate_overall_score(self, analysis: Dict[str, Any]) -> str:
        """Calculate overall score from individual category scores."""
        scores = {
            'Excellent': 4,
            'Good': 3,
            'Fair': 2,
            'Poor': 1
        }
        
        total = 0
        count = 0
        
        for category in analysis.values():
            score = category.get('score', 'Fair')
            if score in scores:
                total += scores[score]
                count += 1
        
        if count == 0:
            return "Fair"
            
        avg = total / count
        if avg >= 3.5:
            return "Excellent"
        elif avg >= 2.5:
            return "Good"
        elif avg >= 1.5:
            return "Fair"
        return "Poor"

    def print_results(self, url: str, analysis: Dict[str, Any], revised_content: Optional[str] = None):
        """Print analysis results and revised content if available."""
        print("\n=== Documentation Analysis Results ===")
        print(f"URL: {url}")
        print(f"Overall Score: {self.calculate_overall_score(analysis)}")
        
        for category, data in analysis.items():
            print(f"\n{category.upper()}")
            print(f"Score: {data.get('score', 'N/A')}")
            
            if data.get('issues'):
                print("Issues:")
                for issue in data['issues']:
                    print(f"- {issue}")
            
            if data.get('suggestions'):
                print("Suggestions:")
                for suggestion in data['suggestions']:
                    print(f"- {suggestion}")

        if revised_content:
            print("\n=== Revised Content ===")
            print(revised_content)

    def save_results(self, url: str, analysis: Dict[str, Any], revised_content: Optional[str] = None):
        """Save analysis results and revised content to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save analysis
        data = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "overall_score": self.calculate_overall_score(analysis),
            "analysis": analysis
        }
        
        analysis_file = f"analysis_{timestamp}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"\nAnalysis saved to: {analysis_file}")
        
        # Save revised content if available
        if revised_content:
            revision_file = f"revised_content_{timestamp}.txt"
            with open(revision_file, 'w', encoding='utf-8') as f:
                f.write(revised_content)
            print(f"Revised content saved to: {revision_file}")

    def analyze_documentation(self, url: str) -> Tuple[Dict[str, Any], Optional[str]]:
        """Main method to analyze documentation and generate revised content."""
        # Step 1: Scrape content
        content = self.scrape_page(url)
        
        # Step 2: Analyze content
        analysis = self.analyze_content(content, url)
        
        # Step 3: Generate revised content
        try:
            revised_content = self.revise_content(content, analysis)
        except Exception as e:
            print(f"Warning: Could not generate revised content: {e}")
            revised_content = None
        
        return analysis, revised_content 
