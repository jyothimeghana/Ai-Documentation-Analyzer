import os
import time
import json
from datetime import datetime
from typing import Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

from models import DocumentationAnalysis

class DocumentationAnalyzer:
    """Main class for analyzing documentation using LangChain."""
    
    def __init__(self, api_key: str):
        """Initialize the analyzer with LangChain components."""
        # Initialize the LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
        )
        
        # Initialize parsers
        self.json_parser = JsonOutputParser(pydantic_object=DocumentationAnalysis)
        
        # Create analysis prompt template
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert technical writer analyzing MoEngage documentation. 
            Analyze the provided content and return structured feedback in the exact JSON format specified.
            
            Focus on:
            - Readability for non-technical marketers
            - Clear structure and organization
            - Completeness of information
            - Adherence to documentation style guidelines
            
            {format_instructions}"""),
            ("human", """
            Article URL: {url}
            
            Content to analyze:
            {content}
            
            Provide detailed analysis with specific, actionable feedback for each category.
            """)
        ])
        
        # Create chain
        self.analysis_chain = self.analysis_prompt | self.llm | self.json_parser

    def scrape_page(self, url: str) -> str:
        """
        Scrape content from a documentation page with robust error handling.
        
        Args:
            url (str): URL to scrape
            
        Returns:
            str: Extracted content
        """
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
            
            # Execute script to disable automation detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Wait longer for dynamic content
            print("Waiting for page to load completely...")
            time.sleep(15)
            
            # Try multiple strategies to get content
            content_parts = []
            
            # Strategy 1: Try to get main content area first
            main_selectors = [
                "main", ".main-content", "#main-content", 
                ".article-content", ".content", ".post-content",
                ".entry-content", "[role='main']"
            ]
            
            main_content_found = False
            for selector in main_selectors:
                try:
                    main_element = driver.find_element(By.CSS_SELECTOR, selector)
                    if main_element and main_element.text.strip():
                        print(f"Found main content using selector: {selector}")
                        # Get all text content from main area
                        elements = main_element.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6, p, ul, ol, li, pre, code, div")
                        for element in elements:
                            try:
                                text = element.text.strip()
                                if text and len(text) > 10:  # Filter out very short text
                                    tag = element.tag_name.lower()
                                    if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                                        content_parts.append(f"\n{'#' * int(tag[1])} {text}\n")
                                    else:
                                        content_parts.append(text)
                            except Exception:
                                continue
                        main_content_found = True
                        break
                except Exception:
                    continue
            
            # Strategy 2: If main content not found, try body content
            if not main_content_found:
                print("Main content not found, trying body content...")
                try:
                    # Wait for any content to be present
                    wait = WebDriverWait(driver, 30)
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    
                    # Get page source and extract text using JavaScript
                    content_text = driver.execute_script("""
                        // Remove script and style elements
                        var scripts = document.querySelectorAll('script, style, nav, footer, header, .nav, .footer, .header');
                        scripts.forEach(function(el) { el.remove(); });
                        
                        // Get main content
                        var mainContent = document.querySelector('main, .main-content, #main-content, .article-content, .content') || document.body;
                        return mainContent.innerText || mainContent.textContent || '';
                    """)
                    
                    if content_text and len(content_text.strip()) > 100:
                        content_parts = [content_text.strip()]
                    else:
                        # Fallback: get visible text from body
                        body_text = driver.find_element(By.TAG_NAME, "body").text
                        if body_text:
                            content_parts = [body_text.strip()]
                        
                except Exception as e:
                    print(f"Error with body content extraction: {e}")
            
            # Strategy 3: Last resort - get all text content
            if not content_parts:
                print("Trying fallback content extraction...")
                try:
                    all_text = driver.execute_script("return document.body.innerText || document.body.textContent || '';")
                    if all_text and len(all_text.strip()) > 50:
                        content_parts = [all_text.strip()]
                except Exception:
                    pass
            
            # Combine all content
            if content_parts:
                content = "\n\n".join(content_parts)
                # Clean up the content
                lines = content.split('\n')
                cleaned_lines = []
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 3:  # Filter out very short lines
                        cleaned_lines.append(line)
                
                content = "\n".join(cleaned_lines)
                
                if len(content.strip()) > 100:
                    print(f"Successfully extracted {len(content)} characters")
                    return content
            
            raise Exception("No substantial content found on the page")
            
        except Exception as e:
            print(f"Error scraping page: {e}")
            # Try one more time with a different approach
            try:
                print("Attempting alternative scraping method...")
                time.sleep(5)
                page_source = driver.page_source
                if page_source and len(page_source) > 1000:
                    # Use BeautifulSoup-like approach with Selenium
                    text_content = driver.execute_script("""
                        var walker = document.createTreeWalker(
                            document.body,
                            NodeFilter.SHOW_TEXT,
                            null,
                            false
                        );
                        var textNodes = [];
                        var node;
                        while(node = walker.nextNode()) {
                            if(node.nodeValue.trim().length > 10) {
                                textNodes.push(node.nodeValue.trim());
                            }
                        }
                        return textNodes.join(' ');
                    """)
                    
                    if text_content and len(text_content.strip()) > 100:
                        print(f"Alternative method extracted {len(text_content)} characters")
                        return text_content.strip()
            except Exception as fallback_error:
                print(f"Alternative method also failed: {fallback_error}")
            
            raise Exception(f"All scraping methods failed. Original error: {e}")
        finally:
            try:
                driver.quit()
            except Exception:
                pass

    def analyze_content(self, content: str, url: str) -> Dict[str, Any]:
        """
        Analyze content using LangChain and return structured results.
        
        Args:
            content (str): Content to analyze
            url (str): URL of the content
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            print("Analyzing content with LangChain + Gemini...")
            
            # Get format instructions from the parser
            format_instructions = self.json_parser.get_format_instructions()
            
            # Invoke the analysis chain
            result = self.analysis_chain.invoke({
                "content": content,
                "url": url,
                "format_instructions": format_instructions
            })
            
            # Convert Pydantic model to dict for compatibility
            if hasattr(result, 'dict'):
                analysis_dict = result.dict()
            else:
                analysis_dict = result
                
            print("Analysis completed successfully")
            return analysis_dict
            
        except Exception as e:
            print(f"Error during analysis: {e}")
            # Return a valid default structure
            categories = ["readability", "structure", "completeness", "style_guidelines"]
            return {
                cat: {
                    "score": "Fair",
                    "issues": ["Analysis failed to generate proper response"],
                    "suggestions": ["Please try again"]
                } for cat in categories
            }

    def calculate_overall_score(self, analysis: Dict[str, Any]) -> str:
        """Calculate overall score from individual category scores."""
        scores = []
        score_values = {'Excellent': 4, 'Good': 3, 'Fair': 2, 'Poor': 1}
        
        for category_data in analysis.values():
            score = category_data.get('score', 'Fair')
            if score in score_values:
                scores.append(score_values[score])
        
        if not scores:
            return "Unknown"
        
        avg = sum(scores) / len(scores)
        
        if avg >= 3.5:
            return "Excellent"
        elif avg >= 2.5:
            return "Good"
        elif avg >= 1.5:
            return "Fair"
        else:
            return "Poor"

    def print_results(self, url: str, analysis: Dict[str, Any]):
        """Print analysis results in a readable format."""
        print("\n" + "="*60)
        print("DOCUMENTATION ANALYSIS RESULTS")
        print("="*60)
        
        print(f"\nURL: {url}")
        print(f"Overall Score: {self.calculate_overall_score(analysis)}")
        print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Print each category
        categories = ['readability', 'structure', 'completeness', 'style_guidelines']
        
        for category in categories:
            if category in analysis:
                data = analysis[category]
                print(f"\n{'-'*30}")
                print(f"{category.upper().replace('_', ' ')}")
                print(f"{'-'*30}")
                print(f"Score: {data.get('score', 'N/A')}")
                
                if data.get('issues'):
                    print("\nIssues:")
                    for i, issue in enumerate(data['issues'], 1):
                        print(f"  {i}. {issue}")
                
                if data.get('suggestions'):
                    print("\nSuggestions:")
                    for i, suggestion in enumerate(data['suggestions'], 1):
                        print(f"  {i}. {suggestion}")

    def save_results(self, url: str, analysis: Dict[str, Any]):
        """Save results to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save analysis as JSON
        result_data = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "overall_score": self.calculate_overall_score(analysis),
            "analysis": analysis
        }
        
        json_file = f"analysis_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nAnalysis saved to: {json_file}")

    def analyze_documentation(self, url: str) -> Dict[str, Any]:
        """
        Main method to analyze documentation.
        
        Args:
            url (str): URL to analyze
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        # Step 1: Scrape content
        content = self.scrape_page(url)
        
        # Step 2: Analyze content
        analysis = self.analyze_content(content, url)
        
        return analysis 