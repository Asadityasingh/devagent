# app/models.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ReviewDepth(str, Enum):
    """Review depth levels"""
    QUICK = "quick"
    STANDARD = "standard"
    THOROUGH = "thorough"

class Severity(str, Enum):
    """Issue severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class IssueCategory(str, Enum):
    """Issue categories"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    STYLE = "style"

# ===== REQUEST MODELS =====

class AnalyzeCodeRequest(BaseModel):
    """Request model for code analysis"""
    language: str = Field(..., description="Programming language (python, cpp)")
    code: str = Field(..., min_length=1, description="Source code to analyze")
    filename: Optional[str] = Field(None, description="Optional filename")
    context: Optional[str] = Field(None, description="Additional context")
    review_depth: ReviewDepth = Field(default=ReviewDepth.STANDARD)
    
    @validator('language')
    def validate_language(cls, v):
        """Validate supported languages"""
        supported = ['python', 'cpp', 'javascript', 'typescript', 'java']
        if v.lower() not in supported:
            raise ValueError(f"Language must be one of: {', '.join(supported)}")
        return v.lower()
    
    class Config:
        schema_extra = {
            "example": {
                "language": "python",
                "code": "def login(user, pwd):\n    sql = f\"SELECT * FROM users WHERE name='{user}'\"\n    db.execute(sql)",
                "filename": "auth.py",
                "review_depth": "thorough"
            }
        }

class AnalyzePRRequest(BaseModel):
    """Request model for PR analysis"""
    repository: str = Field(..., pattern=r'^[a-zA-Z0-9\-_]+/[a-zA-Z0-9\-_]+$')
    pr_number: int = Field(..., gt=0)
    review_depth: ReviewDepth = Field(default=ReviewDepth.STANDARD)
    options: Optional[Dict[str, bool]] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "repository": "owner/repo",
                "pr_number": 123,
                "review_depth": "thorough",
                "options": {"generate_tests": True}
            }
        }

# ===== RESPONSE MODELS =====

class CodeIssue(BaseModel):
    """Code issue/vulnerability"""
    id: str = Field(..., description="Unique issue ID")
    severity: Severity
    category: IssueCategory
    type: str = Field(..., description="Specific issue type")
    message: str = Field(..., description="Short message")
    description: str = Field(..., description="Detailed description")
    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: str = Field(..., description="How to fix")
    fixed_code: Optional[str] = None
    references: List[str] = Field(default_factory=list)

class CodeReviewResult(BaseModel):
    """Code review results"""
    summary: str
    issues: List[CodeIssue]
    metrics: Dict[str, Any]
    positive_feedback: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

class AnalyzeResponse(BaseModel):
    """Response model for analysis"""
    request_id: str
    status: str = Field(..., pattern="^(completed|failed|processing)$")
    execution_time_ms: int = Field(..., ge=0)
    timestamp: datetime
    results: Dict[str, Any]
    error: Optional[str] = None

# Test models
if __name__ == "__main__":
    # Test request
    request = AnalyzeCodeRequest(
        language="python",
        code="def test(): pass",
        filename="test.py"
    )
    print("✅ Request model valid:", request.dict())
    
    # Test issue
    issue = CodeIssue(
        id="issue-001",
        severity=Severity.CRITICAL,
        category=IssueCategory.SECURITY,
        type="sql_injection",
        message="SQL injection vulnerability",
        description="User input in SQL query",
        suggestion="Use parameterized queries",
        line=47
    )
    print("✅ Issue model valid:", issue.dict())
