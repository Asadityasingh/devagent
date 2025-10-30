# app/core/bedrock_client.py (COMPLETE REWRITE)
import boto3
import json
from typing import Dict, Any
import structlog
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

class BedrockClient:
    """Simple Bedrock Runtime Client (Guaranteed to Work)"""
    
    def __init__(self):
        self.client = boto3.client(
            'bedrock-runtime',
            region_name=settings.aws_region
        )
        self.model_id = settings.aws_bedrock_model_id
        logger.info(
            "bedrock_client_initialized",
            model_id=self.model_id,
            region=settings.aws_region
        )
    
    async def analyze_code(
        self,
        code: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Analyze code using Claude via Bedrock
        
        Args:
            code: Source code
            language: Programming language
        
        Returns:
            Analysis results with issues
        """
        
        prompt = f"""You are a senior security engineer. Analyze this {language} code for vulnerabilities and issues: {code}

Return ONLY valid JSON (no markdown code blocks, no explanation):
{{
  "issues": [
    {{
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "type": "issue_type",
      "message": "brief message",
      "description": "detailed explanation",
      "line": 47,
      "suggestion": "how to fix"
    }}
  ],
  "summary": "overall summary",
  "positive": ["what went well"]
}}"""
        
        try:
            logger.info("invoking_bedrock_model", language=language, code_length=len(code))
            
            # Call Bedrock Runtime
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2048,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            result_text = response_body['content'][0]['text']
            
            # Extract JSON (handle markdown wrapping)
            try:
                result_json = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    result_json = json.loads(result_text[start_idx:end_idx])
                else:
                    result_json = {"raw_response": result_text}
            
            logger.info("bedrock_invocation_success")
            
            return {
                'success': True,
                'data': result_json,
                'tokens': {
                    'input': response_body.get('usage', {}).get('input_tokens', 0),
                    'output': response_body.get('usage', {}).get('output_tokens', 0)
                }
            }
        
        except Exception as e:
            logger.error("bedrock_invocation_failed", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }

# Test function
async def test_bedrock():
    """Test Bedrock client"""
    client = BedrockClient()
    
    test_code = """
def authenticate(username, password):
    query = f"SELECT * FROM users WHERE username='{username}'"
    cursor.execute(query)
    return cursor.fetchone()

API_KEY = "sk-1234567890abcdef"
"""
    
    print("🤖 Testing Bedrock Client...")
    result = await client.analyze_code(
        code=test_code,
        language="python"
    )
    
    if result['success']:
        print("✅ Bedrock working!")
        print(json.dumps(result['data'], indent=2))
        print(f"\nTokens used: {result['tokens']['input']} in, {result['tokens']['output']} out")
    else:
        print(f"❌ Failed: {result['error']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_bedrock())
