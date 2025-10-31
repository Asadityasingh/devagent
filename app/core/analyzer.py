# # app/core/analyzer.py (COMPLETE: AST + LTM Integration)
# import uuid
# from typing import List
# import structlog
# from app.models import CodeIssue, Severity, IssueCategory, CodeReviewResult
# from app.agents.multi_agent_orchestrator import MultiAgentOrchestrator
# from app.core.parsers.ast_parser import parser as ast_parser

# logger = structlog.get_logger()

# class CodeAnalyzer:
#     """Code analyzer using Multi-Agent Orchestration with LTM Context + AST"""
    
#     def __init__(self):
#         self.orchestrator = MultiAgentOrchestrator()
    
#     async def analyze_code(
#         self,
#         code: str,
#         language: str,
#         filename: str = None,
#         ltm_context: str = ""
#     ) -> CodeReviewResult:
#         """
#         Complete code analysis with multi-agent system + LTM + AST
#         """
#         logger.info("analyzing_code_with_multi_agents", language=language, has_ltm_context=bool(ltm_context))
#         print(f"🔍 Analyzing {language} code with LTM context: {bool(ltm_context)}")
        
#         # AST parsing for Python/C++
#         ast_info = {}
#         func_context = var_context = ""
#         if language in ['python', 'cpp']:
#             ast_info = ast_parser.parse_file_content(code, language)
#             functions = ast_info.get('functions', [])
#             secrets = [v for v in ast_info.get('variables', []) if v.get('type') == 'potential_secret']
            
#             func_context = (
#                 "Functions: " +
#                 ", ".join([f"{f['name']} (lines {f['start_line']}-{f['end_line']})" for f in functions])
#             ) if functions else "No functions detected"

#             var_context = (
#                 "Potential secrets: " +
#                 ", ".join([f"{v['name']} at line {v['line']}" for v in secrets])
#             ) if secrets else "No hardcoded secrets detected"

            
#             logger.info("ast_enhanced_analysis", functions=len(functions), secrets=len(secrets))
#             print(f"🌳 AST Parsed ({language}): {len(functions)} functions, {len(secrets)} secrets")
        
#         # Build enhanced prompts with LTM + AST context
#         code_review_prompt = self._build_code_review_prompt(code, language, filename, ltm_context, func_context, var_context)
#         testing_prompt = self._build_testing_prompt(code, language, filename, ltm_context, func_context)
#         docs_prompt = self._build_docs_prompt(code, language, filename, ltm_context, func_context)
        
#         # Get multi-agent analysis
#         result = await self.orchestrator.analyze_code(
#             code=code,
#             language=language,
#             filename=filename,
#             code_review_prompt=code_review_prompt,
#             testing_prompt=testing_prompt,
#             docs_prompt=docs_prompt
#         )
        
#         if not result['success']:
#             logger.error("analysis_failed", error=result.get('error'))
#             return CodeReviewResult(
#                 summary="Analysis failed: Unable to complete multi-agent analysis",
#                 issues=[],
#                 metrics={'error': True}
#             )
        
#         results = result['results']
        
#         # Parse code review issues
#         issues = []
#         code_review = results.get('code_review', {})
        
#         if 'issues' in code_review:
#             for issue_data in code_review['issues']:
#                 try:
#                     description = issue_data.get('description', '')
#                     if ltm_context and 'similar' not in description.lower():
#                         description += f" [Pattern detected from LTM: Check past fixes in this repo]"
                    
#                     issues.append(CodeIssue(
#                         id=f"issue-{uuid.uuid4().hex[:8]}",
#                         severity=Severity(issue_data.get('severity', 'MEDIUM')),
#                         category=IssueCategory(issue_data.get('category', 'security')),
#                         type=issue_data.get('type', 'unknown'),
#                         message=issue_data.get('message', ''),
#                         description=description,
#                         line=issue_data.get('line'),
#                         suggestion=issue_data.get('suggestion', ''),
#                         fixed_code=issue_data.get('fixed_code')
#                     ))
#                 except Exception as e:
#                     logger.warning("failed_to_parse_issue", error=str(e))
        
#         # Refine issue lines with AST
#         if issues and language in ['python', 'cpp']:
#             for issue in issues:
#                 approx = issue.line or 1
#                 exact = ast_parser.get_exact_line_for_issue(code, issue.type or 'general', approx, language)
#                 if exact != approx:
#                     issue.line = exact
#                     logger.info("ast_line_refined", old=approx, new=exact, issue_type=issue.type)
        
#         # Metrics
#         testing = results.get('testing', {})
#         docs = results.get('documentation', {})
        
#         metrics = {
#             'total_issues': len(issues),
#             'critical_count': len([i for i in issues if i.severity == Severity.CRITICAL]),
#             'high_count': len([i for i in issues if i.severity == Severity.HIGH]),
#             'medium_count': len([i for i in issues if i.severity == Severity.MEDIUM]),
#             'low_count': len([i for i in issues if i.severity == Severity.LOW]),
#             'tests_generated': len(testing.get('test_cases', [])),
#             'documentation_generated': bool(docs.get('documentation')),
#             'ltm_context_used': bool(ltm_context),
#             'ast_enhanced': bool(ast_info)
#         }
        
#         summary = f"Multi-agent analysis: Found {len(issues)} issues"
#         if metrics['tests_generated'] > 0:
#             summary += f", generated {metrics['tests_generated']} tests"
#         if metrics['documentation_generated']:
#             summary += ", created documentation"
#         if ltm_context:
#             summary += " (with LTM pattern matching)"
#         if ast_info:
#             summary += " (AST-enhanced)"
        
#         logger.info("analysis_complete", issues_count=len(issues), metrics=metrics)
#         print(f"✅ Analysis complete: {len(issues)} issues, {metrics['tests_generated']} tests, LTM: {bool(ltm_context)}, AST: {bool(ast_info)}")
        
#         return CodeReviewResult(
#             summary=summary,
#             issues=issues,
#             metrics=metrics,
#             positive_feedback=code_review.get('positive_feedback', [])
#         )
    
#     def _build_code_review_prompt(self, code: str, language: str, filename: str, ltm_context: str, func_context: str = "", var_context: str = "") -> str:
#         ltm_section = f"**LTM Context:** {ltm_context[:200]}... (Align fixes with past repo patterns.)" if ltm_context else ""
#         ast_section = f"**AST Context:** {func_context}. {var_context}." if func_context or var_context else ""
        
#         prompt = f"""You are a senior code reviewer with expertise in {language} security, performance, and best practices.

# {ltm_section}
# {ast_section}

# **File:** {filename or 'unknown.py'}
# **Language:** {language}

# **Code to Review:** {code}

# **Task:** Perform a comprehensive code review focusing on:
# 1. **Security Issues** (SQL injection, hardcoded secrets, input validation, XSS, CSRF, etc.)
# 2. **Code Quality** (readability, maintainability, performance, type safety)
# 3. **Best Practices** (error handling, logging, documentation, design patterns)
# 4. **Consistency** (align with past patterns found in this repository if applicable)

# For each issue, provide:
# - **Severity:** CRITICAL / HIGH / MEDIUM / LOW
# - **Category:** security / performance / maintainability / best_practice / error_handling
# - **Type:** Specific issue type (e.g., SQL Injection, Hardcoded Secret)
# - **Message:** Brief, clear description
# - **Description:** Detailed explanation of why this is an issue
# - **Line:** Line number where issue occurs
# - **Suggestion:** Actionable fix with code example if applicable
# - **Fixed Code:** Corrected code snippet (if applicable)

# **CRITICAL: Return ONLY valid JSON, no extra text/markdown:**
# {{
#   "issues": [
#     {{
#       "severity": "CRITICAL",
#       "category": "security",
#       "type": "SQL Injection",
#       "line": 3,
#       "message": "SQL injection vulnerability",
#       "description": "User input directly concatenated into SQL query",
#       "suggestion": "Use parameterized queries",
#       "fixed_code": "db.execute('SELECT * FROM users WHERE name = %s', (user_input,))"
#     }}
#   ],
#   "positive_feedback": ["Good structure", "Clear naming"]
# }}"""
#         return prompt
    
# #     def _build_testing_prompt(self, code: str, language: str, filename: str, ltm_context: str, func_context: str = "") -> str:
# #         ltm_patterns = f"**LTM:** {ltm_context[:150]}... (Follow repo testing patterns.)" if ltm_context else ""
# #         ast_section = f"**AST:** Test functions: {func_context}" if func_context else ""
        
# #         prompt = f"""You are an expert in {language} testing and QA.

# # {ltm_patterns}
# # {ast_section}

# # **File:** {filename or 'unknown.py'}
# # **Language:** {language}

# # **Code to Test:**{code}

# # **Task:** Generate comprehensive test cases for this code:
# # 1. **Happy Path:** Valid inputs, expected behavior
# # 2. **Edge Cases:** Empty inputs, null values, boundary conditions
# # 3. **Error Cases:** Invalid inputs, type mismatches, exceptions
# # 4. **Security Cases:** If applicable, test injection attacks, boundary exploits

# # Output format: Generate {language} test code (pytest for Python, mocha for JS, etc.) with:
# # - Test function names starting with 'test_'
# # - Clear assertions
# # - Comments explaining each test
# # - Fixtures or setup if needed

# # **CRITICAL: Return ONLY valid JSON, no extra text/markdown:**
# # {{
# #   "test_cases": [
# #     {{
# #       "name": "test_get_user_data_valid",
# #       "description": "Test with valid user input",
# #       "test_code": "def test_get_user_data_valid():\\n    assert get_user_data('test') is not None"
# #     }}
# #   ],
# #   "estimated_coverage": 0.85,
# #   "summary": "Generated 4 test cases covering 85% of code"
# # }}"""
# #         return prompt


#     def _build_testing_prompt(self, code: str, language: str, filename: str, ltm_context: str, func_context: str = "") -> str:
#         ltm_patterns = f"**LTM:** {ltm_context[:150]}... (Follow repo testing patterns.)" if ltm_context else ""
#         ast_section = f"**AST:** Test functions: {func_context}" if func_context else ""
        
#         prompt = f"""You are an expert in {language} testing and QA.

#                     {ltm_patterns}
#                     {ast_section}

#                     **File:** {filename or 'unknown.py'}
#                     **Language:** {language}

#                     **Code to Test:**{code}

#                     **Task:** Generate comprehensive test cases for this code:
#                     1. **Happy Path:** Valid inputs, expected behavior
#                     2. **Edge Cases:** Empty inputs, null values, boundary conditions
#                     3. **Error Cases:** Invalid inputs, type mismatches, exceptions
#                     4. **Security Cases:** If applicable, test injection attacks, boundary exploits

#                     Output format: Generate {language} test code (pytest for Python, mocha for JS, etc.) with:
#                     - Test function names starting with 'test_'
#                     - Clear assertions
#                     - Comments explaining each test
#                     - Fixtures or setup if needed

#                     **CRITICAL JSON FORMATTING RULES:**
#                     1. Return ONLY valid JSON, no extra text/markdown
#                     2. Escape all backslashes in test code: Use \\n for newlines, \\t for tabs, \\\\ for literal backslashes
#                     3. DO NOT include actual newlines in "test_code" strings - use \\n instead
#                     4. Example valid format:
#                     {{"test_cases": [{{"name": "test_example", "test_code": "def test_example():\\n    assert True"}}]}}

#                     **CRITICAL: Return ONLY valid JSON with properly escaped strings:**
#                     {{
#                     "test_cases": [
#                         {{
#                         "name": "test_function_name_valid",
#                         "description": "Test with valid input",
#                         "test_code": "def test_function_name_valid():\\n    result = function_name('valid')\\n    assert result is not None"
#                         }}
#                     ],
#                     "estimated_coverage": 0.85,
#                     "summary": "Generated 4 test cases covering 85% of code"
#                     }}"""
#         return prompt


    
#     def _build_docs_prompt(self, code: str, language: str, filename: str, ltm_context: str, func_context: str = "") -> str:
#         doc_style = f"**LTM:** {ltm_context[:150]}... (Match repo documentation style.)" if ltm_context else ""
#         ast_section = f"**AST:** Document functions: {func_context}" if func_context else ""
        
#         prompt = f"""You are a technical writer specializing in {language} documentation.

# {doc_style}
# {ast_section}

# **File:** {filename or 'unknown.py'}
# **Language:** {language}

# **Code to Document:**{code}

# **Task:** Generate comprehensive documentation:
# 1. **Module/Class Docstring:** Overview, purpose, usage
# 2. **Function Docstrings:** Parameters, return values, exceptions, examples
# 3. **Inline Comments:** Clarify complex logic, non-obvious decisions
# 4. **Type Hints:** Add if missing (for typed languages)
# 5. **Examples:** Usage examples for public APIs

# Output format:
# - For Python: Google/NumPy style docstrings
# - For JS/TS: JSDoc comments
# - For C++: Doxygen style
# - For Go: Godoc style

# **CRITICAL: Return ONLY valid JSON, no extra text/markdown:**
# {{
#   "documentation": [
#     {{
#       "name": "get_user_data",
#       "description": "Retrieve user data from database",
#       "parameters": "user_input (str): User identifier",
#       "returns": "Query result or None",
#       "example": "result = get_user_data('alice')"
#     }}
#   ],
#   "summary": "Generated documentation for 2 functions"
# }}"""
#         return prompt

# # Test
# async def test():
#     analyzer = CodeAnalyzer()
#     result = await analyzer.analyze_code(
#         code="def auth(u, p):\n    sql = f\"SELECT * FROM users WHERE name='{u}'\"\n    db.execute(sql)\n\napi_key = 'sk-123'",
#         language="python",
#         filename="auth.py"
#     )
#     print(f"Summary: {result.summary}")
#     print(f"Issues: {len(result.issues)}")
#     for issue in result.issues[:2]:
#         print(f"  - {issue.severity.value}: {issue.message} (Line {issue.line})")

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(test())


# app/core/analyzer.py (COMPLETE FIXED - Production Ready)
import uuid
from typing import List
import structlog
from app.models import CodeIssue, Severity, IssueCategory, CodeReviewResult
from app.agents.multi_agent_orchestrator import MultiAgentOrchestrator
from app.core.parsers.ast_parser import parser as ast_parser

logger = structlog.get_logger()

class CodeAnalyzer:
    """Code analyzer using Multi-Agent Orchestration with advanced detection"""
    
    def __init__(self):
        self.orchestrator = MultiAgentOrchestrator()
    
    async def analyze_code(
        self,
        code: str,
        language: str,
        filename: str = None,
        ltm_context: str = ""
    ) -> CodeReviewResult:
        """Complete code analysis with multi-agent system + advanced detection"""
        logger.info("analyzing_code_with_multi_agents", language=language, has_ltm_context=bool(ltm_context))
        print(f"🔍 Analyzing {language} code with LTM context: {bool(ltm_context)}")
        
        # AST parsing for Python/C++
        ast_info = {}
        func_context = var_context = ""
        if language in ['python', 'cpp']:
            ast_info = ast_parser.parse_file_content(code, language)
            functions = ast_info.get('functions', [])
            secrets = [v for v in ast_info.get('variables', []) if v.get('type') == 'potential_secret']
            
            if functions:
                func_parts = [f"{f['name']} (lines {f['start_line']}-{f['end_line']})" for f in functions]
                func_context = f"Functions: {', '.join(func_parts)}"
            else:
                func_context = "No functions detected"
            
            if secrets:
                secret_parts = [f"{v['name']} at line {v['line']}" for v in secrets]
                var_context = f"Potential secrets: {', '.join(secret_parts)}"
            else:
                var_context = "No hardcoded secrets detected"
            
            logger.info("ast_enhanced_analysis", functions=len(functions), secrets=len(secrets))
            print(f"🌳 AST Parsed ({language}): {len(functions)} functions, {len(secrets)} secrets")
        
        # Build ENHANCED prompts with advanced detection rules
        code_review_prompt = self._build_enhanced_code_review_prompt(code, language, filename, ltm_context, func_context, var_context)
        testing_prompt = self._build_testing_prompt(code, language, filename, ltm_context, func_context)
        docs_prompt = self._build_docs_prompt(code, language, filename, ltm_context, func_context)
        
        # Get multi-agent analysis
        result = await self.orchestrator.analyze_code(
            code=code,
            language=language,
            filename=filename,
            code_review_prompt=code_review_prompt,
            testing_prompt=testing_prompt,
            docs_prompt=docs_prompt
        )
        
        if not result['success']:
            logger.error("analysis_failed", error=result.get('error'))
            return CodeReviewResult(
                summary="Analysis failed: Unable to complete multi-agent analysis",
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
                    description = issue_data.get('description', '')
                    if ltm_context and 'similar' not in description.lower():
                        description += f" [Pattern detected from LTM: Check past fixes in this repo]"
                    
                    issues.append(CodeIssue(
                        id=f"issue-{uuid.uuid4().hex[:8]}",
                        severity=Severity(issue_data.get('severity', 'MEDIUM')),
                        category=IssueCategory(issue_data.get('category', 'security')),
                        type=issue_data.get('type', 'unknown'),
                        message=issue_data.get('message', ''),
                        description=description,
                        line=issue_data.get('line'),
                        suggestion=issue_data.get('suggestion', ''),
                        fixed_code=issue_data.get('fixed_code')
                    ))
                except Exception as e:
                    logger.warning("failed_to_parse_issue", error=str(e))
        
        # Refine issue lines with AST
        if issues and language in ['python', 'cpp']:
            for issue in issues:
                approx = issue.line or 1
                exact = ast_parser.get_exact_line_for_issue(code, issue.type or 'general', approx, language)
                if exact != approx:
                    issue.line = exact
                    logger.info("ast_line_refined", old=approx, new=exact, issue_type=issue.type)
        
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
            'documentation_generated': bool(docs.get('documentation')),
            'ltm_context_used': bool(ltm_context),
            'ast_enhanced': bool(ast_info)
        }
        
        summary = f"Multi-agent analysis: Found {len(issues)} issues"
        if metrics['tests_generated'] > 0:
            summary += f", generated {metrics['tests_generated']} tests"
        if metrics['documentation_generated']:
            summary += ", created documentation"
        if ltm_context:
            summary += " (with LTM pattern matching)"
        if ast_info:
            summary += " (AST-enhanced)"
        
        logger.info("analysis_complete", issues_count=len(issues), metrics=metrics)
        print(f"✅ Analysis complete: {len(issues)} issues, {metrics['tests_generated']} tests, LTM: {bool(ltm_context)}, AST: {bool(ast_info)}")
        
        return CodeReviewResult(
            summary=summary,
            issues=issues,
            metrics=metrics,
            positive_feedback=code_review.get('positive_feedback', [])
        )
    
    def _build_enhanced_code_review_prompt(self, code: str, language: str, filename: str, ltm_context: str, func_context: str = "", var_context: str = "") -> str:
        """Enhanced code review prompt with ALL detection categories"""
        ltm_section = f"**LTM Context:** {ltm_context[:200]}..." if ltm_context else ""
        ast_section = f"**AST:** {func_context}. {var_context}." if func_context or var_context else ""
        
        prompt = f"""You are a senior security architect and code quality expert with expertise in {language}.

{ltm_section}
{ast_section}

**File:** {filename or 'unknown.py'}
**Language:** {language}

**Code to Review:**
{code}

**Task:** Perform a COMPREHENSIVE security and quality analysis covering ALL categories below.

**CRITICAL: Scan for these vulnerability categories (report ALL found):**

### 1. SECURITY VULNERABILITIES
**SQL Injection:**
- String concatenation in SQL queries
- f-strings with user input in queries
- Unparameterized database operations
- Dynamic query construction

**Hardcoded Secrets:**
- API keys (patterns: sk_, api_key, apikey, key=)
- Passwords (patterns: password, pwd, pass=)
- Tokens (patterns: token, bearer, auth=)
- Database credentials in code
- AWS keys (AKIA...), GCP keys, Azure keys

**Authentication/Authorization Issues:**
- Missing authentication checks before sensitive operations
- Weak password validation (no length/complexity requirements)
- Session management issues (no expiration, predictable tokens)
- Authorization bypass (direct object reference without permission check)
- Missing CSRF protection in forms/endpoints
- JWT without expiration or signature validation
- Hard-coded admin credentials
- Example: `if user: do_sensitive_action()` without role check

**XSS (Cross-Site Scripting):**
- Unescaped user input in HTML output
- Direct DOM manipulation with user data
- Unsafe eval() or innerHTML usage

**Path Traversal:**
- User-controlled file paths without validation
- Missing path sanitization (../ sequences)
- Direct file access with user input

**Command Injection:**
- User input in os.system(), subprocess without validation
- Shell=True with untrusted input

### 2. CONCURRENCY & RACE CONDITIONS
**Race Conditions:**
- Shared mutable state without locks (global variables modified by threads)
- Time-of-check to time-of-use (TOCTOU) bugs
- Missing synchronization primitives (threading.Lock, asyncio.Lock)
- Non-atomic operations on shared data
- Example: `if file_exists(path): delete(path)` without lock

**Deadlocks:**
- Multiple locks acquired in different order
- Recursive lock usage without proper release

### 3. RESOURCE LEAKS & PERFORMANCE
**Memory Leaks:**
- File handles not closed (missing with statement or try/finally)
- Database connections not closed
- Network sockets left open
- Large objects in global scope
- Circular references without cleanup
- Unbounded caches/lists that grow indefinitely

**Performance Bottlenecks:**
- N+1 query problems (loop with database query per iteration)
- Inefficient algorithms (O(n²) when O(n log n) possible)
- Repeated calculations in loops (move invariants outside)
- Blocking I/O in async code
- Large data structures copied instead of referenced
- Missing indexes in queries

### 4. CODE QUALITY & COMPLEXITY
**Code Duplication:**
- Identical or near-identical code blocks (>5 lines)
- Repeated logic that should be extracted to function
- Copy-pasted code with minor variations

**Complexity Issues:**
- Cyclomatic complexity >10 (too many branches/loops)
- Function length >50 lines (should be split)
- Nesting depth >4 levels (refactor to early returns)
- Too many parameters (>5 should use object/dict)

### 5. ERROR HANDLING
**Missing Error Handling:**
- No try/except around risky operations
- Division by zero without validation
- Array access without bounds check
- Network calls without timeout/retry

**Improper Error Handling:**
- Bare except: clauses (catch Exception instead)
- Swallowing exceptions (empty except blocks)
- Not logging errors before raising

### 6. BEST PRACTICES
**Code Style:**
- Inconsistent naming conventions
- Missing type hints (Python 3.5+)
- Missing docstrings for public functions
- Magic numbers (use named constants)

**Design Patterns:**
- God objects (classes with too many responsibilities)
- Tight coupling (hard dependencies instead of interfaces)
- Missing separation of concerns

**For each issue found, provide (RETURN ONLY VALID JSON):**

{{
"issues": [
{{
"severity": "CRITICAL|HIGH|MEDIUM|LOW",
"category": "security|performance|maintainability|error_handling|best_practice",
"type": "Specific type (e.g., SQL Injection, Race Condition, Memory Leak)",
"line": <line_number>,
"message": "Brief description",
"description": "Detailed explanation of the vulnerability/issue",
"suggestion": "Actionable fix with code example",
"fixed_code": "Corrected code snippet (if applicable)"
}}
],
"positive_feedback": ["List good practices found"],
"complexity_score": <1-10>,
"security_score": <1-10>
}}


**CRITICAL RULES:**
1. Return ONLY valid JSON, no extra text/markdown
2. Report ALL issues found (no filtering)
3. Be specific with line numbers and examples
4. Provide actionable fixes for every issue
5. Check for race conditions in multi-threaded/async code
6. Detect memory leaks from unclosed resources
7. Flag performance bottlenecks (N+1 queries, O(n²) algorithms)
8. Identify code duplication (>5 similar lines)
9. Calculate complexity score (1=simple, 10=very complex)
10. Mark auth/authz issues as CRITICAL"""
        
        return prompt
    
    # def _build_testing_prompt(self, code: str, language: str, filename: str, ltm_context: str, func_context: str = "") -> str:
    #     """Enhanced testing prompt with better JSON formatting"""
    #     ltm_patterns = f"**LTM:** {ltm_context[:150]}... (Follow repo testing patterns.)" if ltm_context else ""
    #     ast_section = f"**AST:** Test functions: {func_context}" if func_context else ""
        
    #     prompt = f"""You are an expert in {language} testing and QA.

    #         {ltm_patterns}
    #         {ast_section}

    #         **File:** {filename or 'unknown.py'}
    #         **Language:** {language}

    #         **Code to Test:**{code}


    #         **Task:** Generate comprehensive test cases for this code:
    #         1. **Happy Path:** Valid inputs, expected behavior
    #         2. **Edge Cases:** Empty inputs, null values, boundary conditions
    #         3. **Error Cases:** Invalid inputs, type mismatches, exceptions
    #         4. **Security Cases:** If applicable, test injection attacks, boundary exploits
    #         5. **Concurrency Cases:** If async/threaded, test race conditions

    #         **CRITICAL JSON FORMATTING RULES:**
    #         1. Return ONLY valid JSON, no extra text/markdown
    #         2. Escape all backslashes in test code: Use \\n for newlines, \\t for tabs, \\\\ for literal backslashes
    #         3. DO NOT include actual newlines in "test_code" strings - use \\n instead
    #         4. Example: {{"test_code": "def test():\\n    assert True"}}

    #         Output format: 
    #         {{
    #         "test_cases": [
    #         {{
    #         "name": "test_function_name_valid_input",
    #         "description": "Test with valid input",
    #         "test_code": "def test_function_name_valid_input():\n result = function_name('valid')\n assert result is not None"
    #         }}
    #         ],
    #         "estimated_coverage": 0.95,
    #         "summary": "Generated X test cases covering 95% of code"
    #         }}"""
    #     return prompt

    def _build_testing_prompt(self, code: str, language: str, filename: str, ltm_context: str, func_context: str = "") -> str:
        """Enhanced testing prompt with FIXED JSON escaping"""
        ltm_patterns = f"**LTM:** {ltm_context[:150]}..." if ltm_context else ""
        ast_section = f"**AST:** Test functions: {func_context}" if func_context else ""
        
        # Use raw string for example to avoid escape issues
        prompt = f"""You are an expert in {language} testing and QA.

            {ltm_patterns}
            {ast_section}

            **File:** {filename or 'unknown.py'}
            **Language:** {language}

            **Code to Test:**{code}

            **Task:** Generate comprehensive test cases for this code:
            1. **Happy Path:** Valid inputs, expected behavior
            2. **Edge Cases:** Empty inputs, null values, boundary conditions
            3. **Error Cases:** Invalid inputs, type mismatches, exceptions
            4. **Security Cases:** If applicable, test injection attacks
            5. **Concurrency Cases:** If async/threaded, test race conditions

            **CRITICAL JSON FORMATTING:**
            1. Return ONLY valid JSON
            2. In test_code strings: newline = literal characters "\\n" (two chars: backslash + n)
            3. DO NOT include actual newlines in strings
            4. Example valid JSON:
            {{"test_cases": [{{"name": "test_add", "test_code": "def test_add():\\n    assert add(1, 2) == 3"}}]}}

            **Return valid JSON only:**
            {{
            "test_cases": [
                {{
                "name": "test_case_name",
                "description": "What it tests",
                "test_code": "def test_case_name():\\n    result = func()\\n    assert result"
                }}
            ],
            "estimated_coverage": 0.95,
            "summary": "Generated X test cases"
            }}"""
                
        return prompt




    def _build_docs_prompt(self, code: str, language: str, filename: str, ltm_context: str, func_context: str = "") -> str:
        """Documentation generation prompt"""
        doc_style = f"**LTM:** {ltm_context[:150]}... (Match repo documentation style.)" if ltm_context else ""
        ast_section = f"**AST:** Document functions: {func_context}" if func_context else ""
        
        prompt = f"""You are a technical writer specializing in {language} documentation.

        {doc_style}
        {ast_section}

        **File:** {filename or 'unknown.py'}
        **Language:** {language}

        **Code to Document:**{code}

            **Task:** Generate comprehensive documentation:
            1. **Module/Class Docstring:** Overview, purpose, usage
            2. **Function Docstrings:** Parameters, return values, exceptions, examples
            3. **Inline Comments:** Clarify complex logic, non-obvious decisions
            4. **Type Hints:** Add if missing (for typed languages)
            5. **Examples:** Usage examples for public APIs

            **CRITICAL: Return ONLY valid JSON, no extra text/markdown:**
            {{
                "documentation": [
                {{
                    "name": "function_name",
                    "description": "What the function does",
                    "parameters": "param1 (type): description",
                    "returns": "Return type and description",
                    "example": "result = function_name('example')"
                }}
                ],
                "summary": "Generated documentation for X functions"
            }}"""
        return prompt
    
# Test
async def test():
    analyzer = CodeAnalyzer()
    
    # Test code with multiple issue types
    test_code = '''
        import threading

        # 1. Race condition - global without lock
        user_count = 0

        def add_user():
            global user_count
            user_count += 1  # Race condition

        # 2. Memory leak - file not closed
        def process_log(filename):
            log = open(filename)
            data = log.read()
            return data

        # 3. Auth issue - no permission check
        def admin_delete(user_id):
            db.execute(f"DELETE FROM users WHERE id={user_id}")

        # 4. N+1 query problem
        def list_with_details():
            items = db.query("SELECT * FROM items")
            for item in items:
                details = db.query(f"SELECT * FROM details WHERE item_id={item.id}")

        # 5. High complexity
        def validate(x, y, z, a, b):
            if x > 0:
                if y < 10:
                    if z == "test":
                        if a and b:
                            if x + y > z:
                                return True
            return False

        # 6. Code duplication
        def save_user(name):
            user = User()
            user.name = name
            user.created = datetime.now()
            db.save(user)
            return user

        def save_post(title):
            post = Post()
            post.title = title
            post.created = datetime.now()
            db.save(post)
            return post
        '''
    
    result = await analyzer.analyze_code(
        code=test_code,
        language="python",
        filename="test.py"
    )
    
    print(f"\nSummary: {result.summary}")
    print(f"Issues: {len(result.issues)}")
    for issue in result.issues:
        print(f"  - [{issue.severity.value}] {issue.type}: {issue.message} (Line {issue.line})")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test())