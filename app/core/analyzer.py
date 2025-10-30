# # app/core/analyzer.py
# import re
# import uuid
# from typing import List, Dict, Any
# import structlog
# from app.models import CodeIssue, Severity, IssueCategory, CodeReviewResult
# from app.core.bedrock_client import BedrockClient

# logger = structlog.get_logger()

# class CodeAnalyzer:
#     """Analyzes code for issues using AI and pattern matching"""
    
#     def __init__(self):
#         self.bedrock = BedrockClient()
    
#     def _static_analysis(self, code: str, language: str) -> List[CodeIssue]:
#         """Quick pattern-based static analysis"""
#         issues = []
        
#         if language == "python":
#             # Check for SQL injection patterns
#             sql_patterns = [
#                 (r'f["\'].*SELECT.*\{.*\}.*["\']', 'sql_injection_fstring'),
#                 (r'["\'].*SELECT.*\+.*["\']', 'sql_injection_concat'),
#                 (r'\.format\(.*SELECT.*\)', 'sql_injection_format')
#             ]
            
#             for i, line in enumerate(code.split('\n'), 1):
#                 for pattern, issue_type in sql_patterns:
#                     if re.search(pattern, line, re.IGNORECASE):
#                         issues.append(CodeIssue(
#                             id=f"issue-{uuid.uuid4().hex[:8]}",
#                             severity=Severity.CRITICAL,
#                             category=IssueCategory.SECURITY,
#                             type=issue_type,
#                             message="Potential SQL injection vulnerability",
#                             description="User input appears to be directly concatenated into SQL query without parameterization",
#                             line=i,
#                             code_snippet=line.strip(),
#                             suggestion="Use parameterized queries with placeholders (e.g., cursor.execute(query, (param,)))",
#                             fixed_code=self._suggest_sql_fix(line),
#                             references=[
#                                 "https://owasp.org/www-community/attacks/SQL_Injection"
#                             ]
#                         ))
            
#             # Check for hardcoded secrets
#             secret_patterns = [
#                 (r'(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']', 'hardcoded_password'),
#                 (r'(api_key|apikey|token)\s*=\s*["\'][^"\']+["\']', 'hardcoded_api_key'),
#                 (r'(secret|secret_key)\s*=\s*["\'][^"\']+["\']', 'hardcoded_secret')
#             ]
            
#             for i, line in enumerate(code.split('\n'), 1):
#                 for pattern, issue_type in secret_patterns:
#                     if re.search(pattern, line, re.IGNORECASE):
#                         issues.append(CodeIssue(
#                             id=f"issue-{uuid.uuid4().hex[:8]}",
#                             severity=Severity.HIGH,
#                             category=IssueCategory.SECURITY,
#                             type=issue_type,
#                             message="Hardcoded secret detected",
#                             description="Secrets should never be hardcoded in source code",
#                             line=i,
#                             code_snippet=line.strip(),
#                             suggestion="Use environment variables or AWS Secrets Manager",
#                             fixed_code="# Use: password = os.environ.get('PASSWORD')",
#                             references=[
#                                 "https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html"
#                             ]
#                         ))
        
#         return issues
    
#     def _suggest_sql_fix(self, line: str) -> str:
#         """Suggest parameterized query fix"""
#         if 'execute' in line:
#             return 'cursor.execute("SELECT * FROM users WHERE name = %s", (username,))'
#         return 'Use parameterized queries'
    
#     async def analyze_with_ai(
#         self,
#         code: str,
#         language: str,
#         static_issues: List[CodeIssue]
#     ) -> Dict[str, Any]:
#         """Deep analysis using AI"""
        
#         system_prompt = """You are a senior security engineer performing code review.
# Analyze the code for:
# 1. Security vulnerabilities (OWASP Top 10)
# 2. Performance issues
# 3. Best practices violations
# 4. Code quality concerns

# Provide specific, actionable feedback."""

#         user_prompt = f"""Analyze this {language} code: {code}

# Static analysis already found {len(static_issues)} issues.
# Provide additional insights on:
# - Code complexity
# - Error handling
# - Design patterns
# - Optimization opportunities

# Be specific and provide code examples for fixes."""

#         result = await self.bedrock.invoke_model(
#             prompt=user_prompt,
#             system_prompt=system_prompt,
#             max_tokens=2048,
#             temperature=0.3
#         )
        
#         if not result['success']:
#             logger.error("ai_analysis_failed", error=result.get('error'))
#             return {
#                 'insights': 'AI analysis unavailable',
#                 'tokens_used': 0
#             }
        
#         return {
#             'insights': result['text'],
#             'tokens_used': result['usage']['input_tokens'] + result['usage']['output_tokens']
#         }
    
#     async def analyze_code(
#         self,
#         code: str,
#         language: str,
#         filename: str = None
#     ) -> CodeReviewResult:
#         """
#         Complete code analysis
        
#         Args:
#             code: Source code
#             language: Programming language
#             filename: Optional filename
        
#         Returns:
#             CodeReviewResult with all findings
#         """
#         logger.info("analyzing_code", language=language, filename=filename)
        
#         # Static analysis (fast)
#         static_issues = self._static_analysis(code, language)
        
#         # AI analysis (deep)
#         ai_result = await self.analyze_with_ai(code, language, static_issues)
        
#         # Calculate metrics
#         lines = code.split('\n')
#         metrics = {
#             'total_lines': len(lines),
#             'code_lines': len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
#             'total_issues': len(static_issues),
#             'critical_count': len([i for i in static_issues if i.severity == Severity.CRITICAL]),
#             'high_count': len([i for i in static_issues if i.severity == Severity.HIGH]),
#             'medium_count': len([i for i in static_issues if i.severity == Severity.MEDIUM]),
#             'low_count': len([i for i in static_issues if i.severity == Severity.LOW]),
#             'tokens_used': ai_result.get('tokens_used', 0)
#         }
        
#         # Generate summary
#         summary = f"Found {len(static_issues)} issues "
#         if metrics['critical_count'] > 0:
#             summary += f"({metrics['critical_count']} critical) "
#         summary += f"in {metrics['code_lines']} lines of code."
        
#         # Positive feedback (if no critical issues)
#         positive = []
#         if metrics['critical_count'] == 0:
#             positive.append("No critical security vulnerabilities detected")
#         if metrics['code_lines'] < 100:
#             positive.append("Code is concise and focused")
        
#         # Recommendations
#         recommendations = []
#         if metrics['critical_count'] > 0:
#             recommendations.append("Address critical security issues immediately")
#         recommendations.append("Add comprehensive error handling")
#         recommendations.append("Consider adding type hints for better code clarity")
        
#         return CodeReviewResult(
#             summary=summary,
#             issues=static_issues,
#             metrics=metrics,
#             positive_feedback=positive,
#             recommendations=recommendations
#         )

# # Test analyzer
# async def test_analyzer():
#     """Test code analyzer"""
#     analyzer = CodeAnalyzer()
    
#     # Test code with SQL injection
#     test_code = """
# def authenticate(username, password):
#     query = f"SELECT * FROM users WHERE username='{username}'"
#     cursor.execute(query)
#     return cursor.fetchone()

# def get_user(user_id):
#     api_key = "sk-1234567890abcdef"
#     return api_key
# """
    
#     result = await analyzer.analyze_code(
#         code=test_code,
#         language="python",
#         filename="auth.py"
#     )
    
#     print(f"\n✅ Analysis complete!")
#     print(f"Summary: {result.summary}")
#     print(f"\nIssues found: {len(result.issues)}")
#     for issue in result.issues:
#         print(f"  - {issue.severity.value}: {issue.message} (line {issue.line})")
#     print(f"\nMetrics: {result.metrics}")

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(test_analyzer())

# app/core/analyzer.py (UPDATED)
import uuid
from typing import List
import structlog
from app.models import CodeIssue, Severity, IssueCategory, CodeReviewResult
from app.agents.multi_agent_orchestrator import MultiAgentOrchestrator
# from app.agents.multi_agent_orchestrator import MultiAgentOrchestrator 
logger = structlog.get_logger()

class CodeAnalyzer:
    """Code analyzer using Multi-Agent Orchestration"""
    
    def __init__(self):
        self.orchestrator = MultiAgentOrchestrator()
    
    async def analyze_code(
        self,
        code: str,
        language: str,
        filename: str = None
    ) -> CodeReviewResult:
        """
        Complete code analysis using multi-agent system
        
        Agents (running in parallel):
        1. Code Review Agent (security & quality)
        2. Testing Agent (test generation)
        3. Documentation Agent (docs generation)
        """
        
        logger.info("analyzing_code_with_multi_agents", language=language)
        
        # Get multi-agent analysis
        result = await self.orchestrator.analyze_code(
            code=code,
            language=language,
            filename=filename
        )
        
        if not result['success']:
            return CodeReviewResult(
                summary="Analysis failed",
                issues=[],
                metrics={'error': True}
            )
        
        results = result['results']
        
        # Parse code review issues
        issues = []
        code_review = results.get('code_review', {})
        
        if 'issues' in code_review:
            for issue_data in code_review['issues']:
                try:
                    issues.append(CodeIssue(
                        id=f"issue-{uuid.uuid4().hex[:8]}",
                        severity=Severity(issue_data.get('severity', 'MEDIUM')),
                        category=IssueCategory(issue_data.get('category', 'security')),
                        type=issue_data.get('type', 'unknown'),
                        message=issue_data.get('message', ''),
                        description=issue_data.get('description', ''),
                        line=issue_data.get('line'),
                        suggestion=issue_data.get('suggestion', ''),
                        fixed_code=issue_data.get('fixed_code')
                    ))
                except Exception as e:
                    logger.warning("failed_to_parse_issue", error=str(e))
        
        # Metrics
        testing = results.get('testing', {})
        docs = results.get('documentation', {})
        
        metrics = {
            'total_issues': len(issues),
            'critical_count': len([i for i in issues if i.severity == Severity.CRITICAL]),
            'high_count': len([i for i in issues if i.severity == Severity.HIGH]),
            'medium_count': len([i for i in issues if i.severity == Severity.MEDIUM]),
            'low_count': len([i for i in issues if i.severity == Severity.LOW]),
            'tests_generated': len(testing.get('test_cases', [])),
            'documentation_generated': bool(docs.get('documentation'))
        }
        
        summary = f"Multi-agent analysis: Found {len(issues)} issues"
        if metrics['tests_generated'] > 0:
            summary += f", generated {metrics['tests_generated']} tests"
        if metrics['documentation_generated']:
            summary += ", created documentation"
        
        return CodeReviewResult(
            summary=summary,
            issues=issues,
            metrics=metrics,
            positive_feedback=code_review.get('positive_feedback', [])
        )

# Test
async def test():
    analyzer = CodeAnalyzer()
    result = await analyzer.analyze_code(
        "def auth(u, p):\n    sql = f\"SELECT * FROM users WHERE name='{u}'\"\n    db.execute(sql)",
        "python"
    )
    print(f"Summary: {result.summary}")
    print(f"Issues: {len(result.issues)}")
    for issue in result.issues:
        print(f"  - {issue.severity.value}: {issue.message}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test())
