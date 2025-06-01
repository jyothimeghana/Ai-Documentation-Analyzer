from pydantic import BaseModel
from typing import List, Optional

class CategoryAnalysis(BaseModel):
    """Model for individual category analysis results."""
    score: str
    issues: List[str]
    suggestions: List[str]

class DocumentationAnalysis(BaseModel):
    """Model for complete documentation analysis results."""
    readability: CategoryAnalysis
    structure: CategoryAnalysis
    completeness: CategoryAnalysis
    style_guidelines: CategoryAnalysis 
