from pydantic import BaseModel, Field
from typing import List

class CategoryAnalysis(BaseModel):
    """Analysis for a specific category."""
    score: str = Field(description="Score must be one of: Excellent, Good, Fair, Poor")
    issues: List[str] = Field(description="List of identified issues")
    suggestions: List[str] = Field(description="List of improvement suggestions")


class DocumentationAnalysis(BaseModel):
    """Complete documentation analysis structure."""
    readability: CategoryAnalysis = Field(description="Readability analysis")
    structure: CategoryAnalysis = Field(description="Structure analysis")
    completeness: CategoryAnalysis = Field(description="Completeness analysis")
    style_guidelines: CategoryAnalysis = Field(description="Style guidelines analysis") 