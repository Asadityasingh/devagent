# # app/models.py (UPDATED: Consistent lowercase enum keys)
# from pydantic import BaseModel, Field, validator
# from typing import Optional, List, Dict, Any
# from datetime import datetime
# from enum import Enum


# class ReviewDepth(str, Enum):
#     """Review depth levels"""
#     QUICK = "quick"
#     STANDARD = "standard"
#     THOROUGH = "thorough"


# class Severity(str, Enum):
#     """Issue severity levels"""
#     CRITICAL = "CRITICAL"
#     HIGH = "HIGH"
#     MEDIUM = "MEDIUM"
#     LOW = "LOW"


# class IssueCategory(str, Enum):
#     """Issue categories (lowercase for consistency with agent responses)"""
#     security = "security"
#     performance = "performance"
#     maintainability = "maintainability"
#     style = "style"
#     error_handling = "error_handling"
#     best_practice = "best_practice"


# # ===== REQUEST MODELS =====


# class AnalyzeCodeRequest(BaseModel):
#     """Request model for code analysis"""
#     language: str = Field(..., description="Programming language (python, cpp)")
#     code: str = Field(..., min_length=1, description="Source code to analyze")
#     filename: Optional[str] = Field(None, description="Optional filename")
#     context: Optional[str] = Field(None, description="Additional context")
#     review_depth: ReviewDepth = Field(default=ReviewDepth.STANDARD)
    
#     @validator('language')
#     def validate_language(cls, v):
#         """Validate supported languages"""
#         supported = ['python', 'cpp', 'javascript', 'typescript', 'java', 'go', 'php']
#         if v.lower() not in supported:
#             raise ValueError(f"Language must be one of: {', '.join(supported)}")
#         return v.lower()
    
#     class Config:
#         schema_extra = {
#             "example": {
#                 "language": "python",
#                 "code": "def login(user, pwd):\n    sql = f\"SELECT * FROM users WHERE name='{user}'\"\n    db.execute(sql)",
#                 "filename": "auth.py",
#                 "review_depth": "thorough"
#             }
#         }


# class AnalyzePRRequest(BaseModel):
#     """Request model for PR analysis"""
#     repository: str = Field(..., pattern=r'^[a-zA-Z0-9\-_]+/[a-zA-Z0-9\-_]+$')
#     pr_number: int = Field(..., gt=0)
#     review_depth: ReviewDepth = Field(default=ReviewDepth.STANDARD)
#     options: Optional[Dict[str, bool]] = Field(default_factory=dict)
    
#     class Config:
#         schema_extra = {
#             "example": {
#                 "repository": "owner/repo",
#                 "pr_number": 123,
#                 "review_depth": "thorough",
#                 "options": {"generate_tests": True}
#             }
#         }


# # ===== RESPONSE MODELS =====


# class CodeIssue(BaseModel):
#     """Code issue/vulnerability"""
#     id: str = Field(..., description="Unique issue ID")
#     severity: Severity
#     category: IssueCategory
#     type: str = Field(..., description="Specific issue type (e.g., SQL Injection)")
#     message: str = Field(..., description="Short message")
#     description: str = Field(..., description="Detailed description")
#     file: Optional[str] = None
#     line: Optional[int] = None
#     column: Optional[int] = None
#     code_snippet: Optional[str] = None
#     suggestion: str = Field(..., description="How to fix")
#     fixed_code: Optional[str] = None
#     references: List[str] = Field(default_factory=list)


# class CodeReviewResult(BaseModel):
#     """Code review results"""
#     summary: str
#     issues: List[CodeIssue]
#     metrics: Dict[str, Any]
#     positive_feedback: List[str] = Field(default_factory=list)
#     recommendations: List[str] = Field(default_factory=list)


# class AnalyzeResponse(BaseModel):
#     """Response model for analysis"""
#     request_id: str
#     status: str = Field(..., pattern="^(completed|failed|processing)$")
#     execution_time_ms: int = Field(..., ge=0)
#     timestamp: datetime
#     results: Dict[str, Any]
#     error: Optional[str] = None


# # ===== NEW: AST RESULT MODELS =====


# class ASTFunction(BaseModel):
#     """Detected function from AST parsing"""
#     name: str = Field(..., description="Function/method name")
#     file: str = Field(..., description="Source file")
#     start_line: int = Field(..., ge=1)
#     end_line: int = Field(..., ge=1)
#     params: List[str] = Field(default_factory=list)


# class ASTVariable(BaseModel):
#     """Detected variable from AST parsing"""
#     name: str = Field(..., description="Variable name")
#     file: str = Field(..., description="Source file")
#     line: int = Field(..., ge=1)
#     value: Optional[str] = Field(None, description="Variable value preview")
#     type: str = Field(..., description="Variable type (e.g., potential_secret)")


# class ASTResult(BaseModel):
#     """AST parsing results"""
#     functions: List[ASTFunction] = Field(default_factory=list)
#     variables: List[ASTVariable] = Field(default_factory=list)
#     total_lines: int = Field(default=0, ge=0)
#     language: str = Field(..., description="Parsed language")


# # Test models
# if __name__ == "__main__":
#     # Test request
#     request = AnalyzeCodeRequest(
#         language="python",
#         code="def test(): pass",
#         filename="test.py"
#     )
#     print("✅ Request model valid:", request.dict())
    
#     # Test issue with lowercase category
#     issue = CodeIssue(
#         id="issue-001",
#         severity=Severity.CRITICAL,
#         category=IssueCategory.security,  # Updated to lowercase
#         type="sql_injection",
#         message="SQL injection vulnerability",
#         description="User input in SQL query",
#         suggestion="Use parameterized queries",
#         line=47
#     )
#     print("✅ Issue model valid:", issue.dict())
    
#     # Test best_practice category
#     issue_bp = CodeIssue(
#         id="issue-002",
#         severity=Severity.MEDIUM,
#         category=IssueCategory.best_practice,  # Test best_practice
#         type="naming_convention",
#         message="Function name should use snake_case",
#         description="PEP 8 naming conventions",
#         suggestion="Rename to snake_case",
#         line=10
#     )
#     print("✅ Best practice issue valid:", issue_bp.dict())
    
#     # Test AST models
#     ast_func = ASTFunction(
#         name="login",
#         file="auth.py",
#         start_line=1,
#         end_line=5,
#         params=["username", "password"]
#     )
#     print("✅ AST function model valid:", ast_func.dict())
    
#     ast_var = ASTVariable(
#         name="API_KEY",
#         file="config.py",
#         line=10,
#         value="sk_test_1234567890",
#         type="potential_secret"
#     )
#     print("✅ AST variable model valid:", ast_var.dict())

# app/models.py (UPDATED: All Detection Categories)
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
    """Issue categories - All detection types"""
    security = "security"
    performance = "performance"
    maintainability = "maintainability"
    style = "style"
    error_handling = "error_handling"
    best_practice = "best_practice"
    # NEW: Enhanced detection categories
    concurrency = "concurrency"
    resource_leak = "resource_leak"
    code_quality = "code_quality"
    complexity = "code_quality"
    resource_leaks = "resource_leak"

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
        supported = ['python', 'cpp', 'javascript', 'typescript', 'java', 'go', 'php']
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
    type: str = Field(..., description="Specific issue type (e.g., SQL Injection, Race Condition)")
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


# ===== AST RESULT MODELS =====


class ASTFunction(BaseModel):
    """Detected function from AST parsing"""
    name: str = Field(..., description="Function/method name")
    file: str = Field(..., description="Source file")
    start_line: int = Field(..., ge=1)
    end_line: int = Field(..., ge=1)
    params: List[str] = Field(default_factory=list)


class ASTVariable(BaseModel):
    """Detected variable from AST parsing"""
    name: str = Field(..., description="Variable name")
    file: str = Field(..., description="Source file")
    line: int = Field(..., ge=1)
    value: Optional[str] = Field(None, description="Variable value preview")
    type: str = Field(..., description="Variable type (e.g., potential_secret)")


class ASTResult(BaseModel):
    """AST parsing results"""
    functions: List[ASTFunction] = Field(default_factory=list)
    variables: List[ASTVariable] = Field(default_factory=list)
    total_lines: int = Field(default=0, ge=0)
    language: str = Field(..., description="Parsed language")


# ===== DETECTION TYPE MAPPINGS =====


DETECTION_CATEGORY_MAP = {
    # Security
    "SQL Injection": IssueCategory.security,
    "Hardcoded Secret": IssueCategory.security,
    "Hardcoded API secret": IssueCategory.security,
    "Hardcoded token": IssueCategory.security,
    "Path Traversal": IssueCategory.security,
    "Command Injection": IssueCategory.security,
    "XSS": IssueCategory.security,
    "Authentication/Authorization Issue": IssueCategory.security,
    "Authentication bypass": IssueCategory.security,
    "CSRF": IssueCategory.security,
    
    # Concurrency & Race Conditions
    "Race Condition": IssueCategory.concurrency,
    "Deadlock": IssueCategory.concurrency,
    "Thread Safety": IssueCategory.concurrency,
    
    # Resource Leaks & Performance
    "Memory Leak": IssueCategory.resource_leak,
    "N+1 Query": IssueCategory.resource_leak,
    "N+1 Query Problem": IssueCategory.resource_leak,
    "Performance Bottleneck": IssueCategory.performance,
    
    # Code Quality
    "Code Duplication": IssueCategory.code_quality,
    "High Complexity": IssueCategory.code_quality,
    "Complexity": IssueCategory.code_quality,
    "Type Mismatch": IssueCategory.code_quality,
    
    # Error Handling
    "Missing Error Handling": IssueCategory.error_handling,
    "Division by Zero": IssueCategory.error_handling,
    
    # Best Practices
    "Missing Type Hint": IssueCategory.best_practice,
    "Missing Docstring": IssueCategory.best_practice,
}


# Test models
if __name__ == "__main__":
    # Test request
    request = AnalyzeCodeRequest(
        language="python",
        code="def test(): pass",
        filename="test.py"
    )
    print("✅ Request model valid:", request.dict())
    
    # Test all issue categories
    categories_to_test = [
        IssueCategory.security,
        IssueCategory.performance,
        IssueCategory.maintainability,
        IssueCategory.style,
        IssueCategory.error_handling,
        IssueCategory.best_practice,
        IssueCategory.concurrency,
        IssueCategory.resource_leak,
        IssueCategory.code_quality,
    ]
    
    for category in categories_to_test:
        issue = CodeIssue(
            id=f"issue-{category.value}",
            severity=Severity.HIGH,
            category=category,
            type=f"test_{category.value}",
            message=f"Test {category.value} issue",
            description=f"Testing {category.value} category",
            suggestion="Fix this issue",
            line=10
        )
        print(f"✅ {category.value}: {issue.category.value}")
    
    print("\n✅ All categories valid!")
