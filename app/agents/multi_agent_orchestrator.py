
# app/agents/multi_agent_orchestrator.py (FULL: LTM-Enhanced Prompts + Nova Integration)
import boto3
import json
from typing import Dict, Any, Optional
import structlog
import asyncio
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

class MultiAgentOrchestrator:
    """Multi-Agent Orchestration using Bedrock Runtime (Nova) with LTM Support"""
    
    def __init__(self):
        self.client = boto3.client(
            'bedrock-runtime',
            region_name=settings.aws_region
        )
        self.model_id = "us.amazon.nova-pro-v1:0"  # ✅ CORRECT: Add "us." prefix
        logger.info("orchestrator_initialized", model=self.model_id)
    
    async def analyze_code(
        self,
        code: str,
        language: str,
        filename: Optional[str] = None,
        code_review_prompt: Optional[str] = None,
        testing_prompt: Optional[str] = None,
        docs_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete multi-agent analysis of code with optional LTM-enhanced prompts
        
        Args:
            code: Source code to analyze
            language: Programming language (e.g., 'python')
            filename: Optional filename for context
            code_review_prompt: Custom LTM-aware prompt for code review agent
            testing_prompt: Custom LTM-aware prompt for testing agent
            docs_prompt: Custom LTM-aware prompt for documentation agent
        """
        
        enhanced_prompts = bool(code_review_prompt or testing_prompt or docs_prompt)
        logger.info(
            "multi_agent_orchestration_started",
            language=language,
            filename=filename,
            enhanced_prompts=enhanced_prompts
        )
        print(f"🤖 Multi-Agent Analysis Starting... (LTM Enhanced: {enhanced_prompts})")
        
        # Run all agents in parallel
        results = await asyncio.gather(
            self._code_review_agent(code, language, code_review_prompt),
            self._testing_agent(code, language, testing_prompt),
            self._documentation_agent(code, language, docs_prompt),
            return_exceptions=False
        )
        
        code_review_result, testing_result, docs_result = results
        
        consolidated = {
            'code_review': code_review_result,
            'testing': testing_result,
            'documentation': docs_result
        }
        
        logger.info("multi_agent_analysis_complete", enhanced=enhanced_prompts)
        print("✅ Multi-Agent Analysis Complete!")
        
        return {
            'success': True,
            'results': consolidated
        }
    
    async def _code_review_agent(
        self,
        code: str,
        language: str,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Code Review Agent - Security & Quality Analysis (LTM-Enhanced)"""
        
        logger.info("invoking_code_review_agent", custom_prompt=bool(custom_prompt))
        
        if custom_prompt:
            prompt = custom_prompt
            print("📚 Using LTM-enhanced code review prompt")
        else:
            # Default prompt (original hardcoded)
            prompt = f"""You are a senior security engineer. Analyze this {language} code for vulnerabilities and quality issues: {code}


Identify:
1. Security vulnerabilities (CRITICAL, HIGH, MEDIUM, LOW)
2. Code quality issues
3. Performance problems
4. Best practice violations


For EACH issue, provide:
- severity level
- type (e.g., sql_injection, hardcoded_secret)
- line number
- description
- suggestion for fix


Return ONLY valid JSON (no markdown):
{{
  "issues": [
    {{
      "severity": "CRITICAL",
      "type": "sql_injection",
      "line": 47,
      "message": "SQL injection vulnerability",
      "description": "User input directly concatenated into SQL query",
      "suggestion": "Use parameterized queries"
    }}
  ],
  "summary": "Found N critical issues",
  "positive_feedback": ["What went well"]
}}"""
        
        return await self._invoke_nova(prompt)
    
    async def _testing_agent(
        self,
        code: str,
        language: str,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Testing Agent - Test Case Generation (LTM-Enhanced)"""
        
        logger.info("invoking_testing_agent", custom_prompt=bool(custom_prompt))
        
        if custom_prompt:
            prompt = custom_prompt
            print("🧪 Using LTM-enhanced testing prompt")
        else:
            # Default prompt (original hardcoded)
            prompt = f"""You are a test automation expert. Generate comprehensive pytest tests for this {language} code: {code}


Create tests for:
1. Happy path (valid inputs)
2. Edge cases (boundary conditions, empty values)
3. Error scenarios (exceptions, invalid inputs)
4. All code branches


Return ONLY valid JSON:
{{
  "test_cases": [
    {{
      "name": "test_authenticate_valid_credentials",
      "description": "Test authentication with valid credentials",
      "test_code": "def test_...(): ..."
    }}
  ],
  "estimated_coverage": 0.95,
  "summary": "Generated N test cases covering X% of code"
}}"""
        
        return await self._invoke_nova(prompt)
    
    async def _documentation_agent(
        self,
        code: str,
        language: str,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Documentation Agent - API & Code Documentation (LTM-Enhanced)"""
        
        logger.info("invoking_documentation_agent", custom_prompt=bool(custom_prompt))
        
        if custom_prompt:
            prompt = custom_prompt
            print("📖 Using LTM-enhanced documentation prompt")
        else:
            # Default prompt (original hardcoded)
            prompt = f"""You are a technical writer. Generate documentation for this {language} code: {code}


Create documentation for:
1. Function/class descriptions
2. Parameters and return values
3. Usage examples
4. Error handling notes


Return ONLY valid JSON:
{{
  "documentation": [
    {{
      "name": "function_name",
      "description": "What this function does",
      "parameters": "Parameter descriptions",
      "returns": "Return value description",
      "example": "Usage example"
    }}
  ],
  "summary": "Generated documentation for N functions"
}}"""
        
        return await self._invoke_nova(prompt)
    
    async def _invoke_nova(self, prompt: str) -> Dict[str, Any]:
        """Invoke Amazon Nova with CORRECT native format [web:216][web:218]"""
        
        try:
            # ✅ NOVA NATIVE FORMAT (invoke_model)
            request_body = {
                "schemaVersion": "messages-v1",  # ✅ Required for Nova [web:216]
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"text": prompt}
                        ]
                    }
                ],
                "inferenceConfig": {  # ✅ Nova-specific params
                    "max_new_tokens": 2048,  # ✅ Use max_new_tokens (not maxTokens) [web:218]
                    "temperature": 0.7,
                    "top_p": 0.9,  # ✅ top_p (not topP)
                    "top_k": 50
                }
            }
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            # ✅ CORRECT RESPONSE PARSING for Nova invoke_model [web:218][web:222]
            response_body = json.loads(response['body'].read())
            text = response_body["output"]["message"]["content"][0]["text"]  # ✅ Path: output > message > content[0] > text
            
            # Try to parse JSON safely
            try:
                result = json.loads(text)
            except json.JSONDecodeError:
                # Try to extract JSON portion even if wrapped with markdown
                start = text.find('{')
                end = text.rfind('}') + 1
                if start >= 0 and end > start:
                    json_text = text[start:end]
                    result = json.loads(json_text)
                else:
                    logger.warning("json_extraction_failed", preview=text[:100])
                    result = {"raw_response": text, "parsed": False}
            
            logger.info("nova_invocation_success")
            return result
        
        except Exception as e:
            logger.error("nova_invocation_failed", error=str(e))
            return {'error': str(e)}


# Test function (Updated: Test with LTM prompts)
async def test_orchestrator():
    """Test multi-agent orchestrator with and without LTM prompts"""
    
    orchestrator = MultiAgentOrchestrator()
    
    test_code = """
def authenticate(username, password):
    query = f"SELECT * FROM users WHERE username='{username}'"
    cursor.execute(query)
    user = cursor.fetchone()
    
    if user and user['password'] == password:
        return True
    return False


def get_config():
    api_key = "sk-1234567890abcdef"
    return api_key
"""
    
    # Test 1: Basic (no LTM)
    print("\n=== Test 1: Basic Analysis (No LTM) ===")
    result = await orchestrator.analyze_code(
        code=test_code,
        language="python",
        filename="auth.py"
    )
    
    if result['success']:
        print("✅ Basic Analysis Complete!")
        print(json.dumps(result['results'], indent=2))
    else:
        print(f"❌ Basic Failed: {result}")
    
    # Test 2: LTM-Enhanced
    print("\n=== Test 2: LTM-Enhanced Analysis ===")
    ltm_context = """
- Previous PR #5: SQL injection in login() fixed using parameterized queries
- Repo pattern: Uses db.execute(query, params) for all database operations
- Security rule: Never use f-strings for SQL queries
- Testing pattern: pytest with @pytest.mark.parametrize for multiple cases
"""
    
    # Sample enhanced prompts (from analyzer)
    code_review_prompt = f"""You are a senior code reviewer with expertise in python security, performance, and best practices.

**Context from Past Reviews (Learning from Memory - LTM):**
{ltm_context}

**File:** auth.py
**Language:** python

**Code to Review:** {test_code}

**Task:** Perform a comprehensive code review focusing on:
1. **Security Issues** (SQL injection, hardcoded secrets, input validation, XSS, CSRF, etc.)
2. **Code Quality** (readability, maintainability, performance, type safety)
3. **Best Practices** (error handling, logging, documentation, design patterns)
4. **Consistency** (align with past patterns found in this repository if applicable)

For each issue, provide:
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Category:** security / performance / maintainability / best_practice / error_handling
- **Type:** Specific issue type (e.g., SQL Injection, Hardcoded Secret)
- **Message:** Brief, clear description
- **Description:** Detailed explanation of why this is an issue
- **Line:** Line number where issue occurs
- **Suggestion:** Actionable fix with code example if applicable
- **Fixed Code:** Corrected code snippet (if applicable)

Output as JSON array of issues (or empty array if no issues).
Also include 'positive_feedback' array with 2-3 things done well.
"""
    
    result = await orchestrator.analyze_code(
        code=test_code,
        language="python",
        filename="auth.py",
        code_review_prompt=code_review_prompt  # Pass LTM-enhanced prompt
        # Add testing_prompt, docs_prompt similarly if needed
    )
    
    if result['success']:
        print("✅ LTM-Enhanced Analysis Complete!")
        print(f"LTM Issues Found: {len(result['results']['code_review'].get('issues', []))}")
    else:
        print(f"❌ LTM Failed: {result}")


if __name__ == "__main__":
    asyncio.run(test_orchestrator())
