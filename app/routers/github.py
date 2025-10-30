
# import json
# import requests
# from typing import Dict, Any
# from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
# from pydantic import BaseModel
# from app.config import get_settings
# from app.core.analyzer import CodeAnalyzer
# import asyncio
# import hashlib
# import hmac
# from datetime import datetime

# router = APIRouter(tags=["github"])
# settings = get_settings()

# class GitHubPayload(BaseModel):
#     action: str
#     pull_request: dict
#     repository: dict
#     sender: dict

# async def analyze_pr_diff(pr_url: str, github_token: str) -> Dict[str, Any]:
#     """Background task: Fetch PR diff and analyze with Nova agents"""
#     headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3.diff"}
    
#     # Fetch PR files/diff
#     diff_url = f"{pr_url}/files"
#     try:
#         response = requests.get(diff_url, headers=headers, timeout=10)
#         response.raise_for_status()
#         files = response.json()
        
#         # Extract code changes (combine added/removed lines)
#         diff_content = ""
#         for file in files[:3]:  # Limit to first 3 files for demo (avoid timeout)
#             if file.get("patch"):
#                 diff_content += file["patch"] + "\n\n"
        
#         if not diff_content:
#             return {"summary": "No code changes to analyze", "issues": []}
        
#         # Analyze with multi-agents
#         analyzer = CodeAnalyzer()
#         result = await analyzer.analyze_code(
#             code=diff_content,
#             language="python",  # Assume Python; enhance to detect
#             filename="pr_diff.py"
#         )
        
#         return {
#             "summary": result.summary,
#             "issues": [issue.dict() for issue in result.issues],
#             "tests_generated": len(result.metrics.get("tests_generated", 0)),
#             "docs_generated": result.metrics.get("documentation_generated", False)
#         }
    
#     except Exception as e:
#         return {"error": f"Analysis failed: {str(e)}"}

# @router.post("/webhook")
# async def github_webhook(request: Request, background_tasks: BackgroundTasks):
#     """GitHub webhook: Auto-analyze PRs and comment results"""
    
#     # Verify webhook signature (optional for hackathon; enable for prod)
#     body = await request.body()
#     signature = request.headers.get("X-Hub-Signature-256")
#     if signature and settings.github_webhook_secret:  # Add GITHUB_WEBHOOK_SECRET to .env if needed
#         expected_sig = "sha256=" + hmac.new(
#             settings.github_webhook_secret.encode(),
#             body,
#             hashlib.sha256
#         ).hexdigest()
#         if not hmac.compare_digest(signature, expected_sig):
#             raise HTTPException(status_code=403, detail="Invalid signature")
    
#     # Parse payload
#     try:
#         payload = json.loads(body)
#     except json.JSONDecodeError:
#         raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
#     event = request.headers.get("X-GitHub-Event", "unknown")
    
#     if event != "pull_request" or payload.get("action") not in ["opened", "synchronize"]:
#         return {"status": "ignored", "event": event, "action": payload.get("action")}
    
#     pr = payload["pull_request"]
#     repo = payload["repository"]
#     github_token = settings.github_token
    
#     if not github_token:
#         raise HTTPException(status_code=500, detail="GitHub token not configured")
    
#     # Queue analysis in background (non-blocking)
#     background_tasks.add_task(
#         post_analysis_comment,
#         pr["url"],
#         repo["full_name"],
#         github_token,
#         event
#     )
    
#     return {
#         "status": "accepted",
#         "event": event,
#         "pr_number": pr["number"],
#         "repo": repo["full_name"],
#         "timestamp": datetime.utcnow().isoformat()
#     }

# async def post_analysis_comment(pr_url: str, repo_name: str, github_token: str, event: str):
#     """Post analysis results as PR comment"""
#     # Run analysis
#     analysis = await analyze_pr_diff(pr_url, github_token)
    
#     if "error" in analysis:
#         comment = f"## DevAgent Swarm Analysis Failed\n{analysis['error']}"
#     else:
#         issues_list = "\n".join([f"- **{issue['severity']}**: {issue['message']} (Line {issue.get('line', 'N/A')})\n  *Suggestion*: {issue['suggestion']}" for issue in analysis["issues"]])
#         comment = f"""## 🔍 DevAgent Swarm Multi-Agent Analysis
# ### Summary
# {analysis['summary']}

# ### 🚨 Security & Quality Issues ({len(analysis['issues'])} found)
# {issues_list if analysis['issues'] else 'No issues detected! 🎉'}

# ### 🧪 Generated Tests
# Generated {analysis['tests_generated']} pytest test cases for new code.

# ### 📚 Auto-Documentation
# Documentation created for {len(analysis['issues'])} functions/classes.

# ### Powered by
# Amazon Nova multi-agents (Code Review, Testing, Documentation)"""
    
#     # Post comment to PR
#     headers = {"Authorization": f"token {github_token}", "Content-Type": "application/json"}
#     comment_url = f"{pr_url}/comments"
    
#     try:
#         requests.post(comment_url, headers=headers, json={"body": comment}, timeout=10)
#         print(f"✅ Commented on PR #{repo_name} for event {event}")
#     except Exception as e:
#         print(f"❌ Failed to comment: {e}")

# # Test endpoint (for manual triggering)
# @router.post("/test-pr-analysis")
# async def test_pr_analysis(payload: Dict[str, Any]):
#     """Manual test: Simulate PR payload (use for local debugging)"""
#     if not payload.get("pr_url"):
#         return {"error": "Provide 'pr_url' in payload (e.g., https://api.github.com/repos/user/repo/pulls/1)"}
    
#     github_token = settings.github_token
#     if not github_token:
#         return {"error": "GitHub token required"}
    
#     analysis = await analyze_pr_diff(payload["pr_url"], github_token)
#     return {"status": "test_complete", "analysis": analysis}
# app/routers/github.py (Fixed: Direct Access to CodeReviewResult Attributes)
import json
import requests
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.config import get_settings
from app.core.analyzer import CodeAnalyzer
import asyncio
import hashlib
import hmac
from datetime import datetime
import structlog  # For structured logging

router = APIRouter(tags=["github"])
settings = get_settings()
logger = structlog.get_logger()  # Get logger instance

class GitHubPayload(BaseModel):
    action: str
    pull_request: dict
    repository: dict
    sender: dict

async def analyze_pr_diff(pr_number: int, repo_full_name: str, github_token: str) -> Dict[str, Any]:
    """Background task: Fetch PR diff and analyze with Nova agents"""
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
    
    # Fetch PR files/diff
    files_url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/files"
    try:
        response = requests.get(files_url, headers=headers, timeout=10)
        response.raise_for_status()
        files = response.json()
        
        # Extract code changes
        diff_content = ""
        language = "python"  # Default
        for file in files[:3]:  # Limit for demo
            filename = file.get("filename", "unknown.py")
            if file.get("patch") and not filename.endswith((".png", ".jpg", ".gif")):
                diff_content += f"# File: {filename}\n{file['patch']}\n\n"
                if filename.endswith(".py"):
                    language = "python"
                elif filename.endswith(".js"):
                    language = "javascript"
                elif filename.endswith(".ts"):
                    language = "typescript"
        
        if not diff_content:
            return {"summary": "No code changes to analyze", "issues": [], "language": "unknown", "tests_generated": 0, "docs_generated": False}
        
        logger.info("pr_diff_extracted", file_count=len(files), content_length=len(diff_content), language=language)
        
        # Analyze
        analyzer = CodeAnalyzer()
        result = await analyzer.analyze_code(code=diff_content, language=language, filename="pr_diff.py")
        
        # Fixed: Direct access to CodeReviewResult attributes (no .code_review nesting)
        if hasattr(result, 'summary') and result.summary:
            summary = result.summary
        else:
            summary = "Analysis complete – no summary generated"
        
        issues = []
        if hasattr(result, 'issues') and result.issues:
            issues = [issue.dict() for issue in result.issues]
        
        tests_generated = 0
        docs_generated = False
        if hasattr(result, 'metrics') and result.metrics:
            tests_generated = getattr(result.metrics, 'tests_generated', 0)
            docs_generated = getattr(result.metrics, 'documentation_generated', False)
        
        logger.info("analysis_parsed_success", pr_number=pr_number, issues_count=len(issues), summary_len=len(summary))
        
        return {
            "summary": summary,
            "issues": issues,
            "tests_generated": tests_generated,
            "docs_generated": docs_generated,
            "language": language
        }
    
    except requests.RequestException as e:
        error_msg = f"Failed to fetch PR diff: {str(e)}"
        logger.error("pr_diff_fetch_failed", error=str(e), url=files_url)
        return {"error": error_msg, "issues": [], "language": "unknown", "tests_generated": 0, "docs_generated": False}
    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        logger.error("analysis_failed", error=str(e))
        return {"error": error_msg, "issues": [], "language": "unknown", "tests_generated": 0, "docs_generated": False}

async def post_analysis_comment(pr_number: int, repo_full_name: str, github_token: str, event: str, analysis: Dict[str, Any]):
    """Post analysis as PR comment using issues endpoint"""
    if "error" in analysis:
        comment = f"## DevAgent Swarm Analysis Failed\n{analysis['error']}\n\n### Powered by Amazon Nova multi-agents"
    else:
        issues_list = ""
        if analysis["issues"]:
            for issue in analysis["issues"]:
                issues_list += f"- **{issue['severity']}**: {issue['message']} (Line {issue.get('line', 'N/A')})\n  *Suggestion*: {issue['suggestion']}\n\n"
        else:
            issues_list = "No issues detected! 🎉\n\n"
        
        # Severity table
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for issue in analysis["issues"]:
            severity = issue['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        table = "| Severity | Count |\n|----------|-------|\n"
        has_issues = any(severity_counts.values())
        for sev, count in severity_counts.items():
            if count > 0:
                table += f"| {sev} | {count} |\n"
        
        tests_text = f"Generated {analysis['tests_generated']} pytest test cases for new code." if analysis['tests_generated'] > 0 else "No tests generated (consider adding unit tests)."
        docs_text = "Documentation created for functions/classes." if analysis['docs_generated'] else "Consider adding docstrings for better maintainability."
        
        comment = f"""## 🔍 DevAgent Swarm Multi-Agent Analysis ({analysis['language'].title()})
### Summary
{analysis['summary']}

### 🚨 Security & Quality Issues ({len(analysis['issues'])} found)
{issues_list}

{table if has_issues else ""}

### 🧪 Generated Tests
{tests_text}

### 📚 Auto-Documentation
{docs_text}

### Powered by
Amazon Nova multi-agents (Code Review, Testing, Documentation)
### Build with ❤️ by Aditya & Sarthak
"""
    
    # Correct endpoint
    comment_url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {github_token}", "Content-Type": "application/json"}
    
    payload = {"body": comment}
    
    try:
        response = requests.post(comment_url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        issues_count = len(analysis.get("issues", [])) if "error" not in analysis else 0
        logger.info("pr_comment_posted_success", pr_number=pr_number, repo=repo_full_name, github_event=event, issues_count=issues_count)
        print(f"✅ Successfully commented on PR #{pr_number} in {repo_full_name} for event {event}")
        print(f"Posted {issues_count} issues: {analysis.get('summary', 'N/A')[:50]}...")
    except requests.RequestException as e:
        error_detail = f"Status: {getattr(e.response, 'status_code', 'N/A')}, Response: {getattr(e.response, 'text', 'N/A')[:200]}"
        logger.error("pr_comment_post_failed", error=str(e), url=comment_url, response_detail=error_detail)
        print(f"❌ Failed to post comment on PR #{pr_number}: {str(e)}")
        print(f"Check: Token scopes (issues:write), Repo access. Response: {error_detail}")

@router.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """GitHub webhook: Auto-analyze PRs on open/synchronize"""
    
    # Signature verification (if secret set)
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if signature and settings.github_webhook_secret:
        expected_sig = "sha256=" + hmac.new(
            settings.github_webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            raise HTTPException(status_code=403, detail="Invalid webhook signature")
    
    # Parse payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in webhook payload")
    
    github_event = request.headers.get("X-GitHub-Event", "unknown")
    action = payload.get("action")
    
    if github_event != "pull_request" or action not in ["opened", "synchronize"]:
        return {"status": "ignored", "github_event": github_event, "action": action}
    
    pr = payload["pull_request"]
    repo = payload["repository"]
    pr_number = pr["number"]
    repo_full_name = repo["full_name"]
    github_token = settings.github_token
    
    if not github_token:
        raise HTTPException(status_code=500, detail="GitHub token not configured in settings")
    
    # Log webhook receipt (fixed kwarg)
    logger.info("webhook_received", message="PR webhook processed", github_event=github_event, action=action, pr_number=pr_number, repo=repo_full_name)
    print(f"📥 Webhook received: Event={github_event}, Action={action}, PR #{pr_number} in {repo_full_name}")
    
    # Queue background analysis
    background_tasks.add_task(process_pr_analysis, pr_number, repo_full_name, github_token, action)
    
    return {
        "status": "accepted",
        "github_event": github_event,
        "pr_number": pr_number,
        "repo": repo_full_name,
        "timestamp": datetime.utcnow().isoformat()
    }

async def process_pr_analysis(pr_number: int, repo_full_name: str, github_token: str, event: str):
    """Process: Analyze diff then post comment"""
    try:
        analysis = await analyze_pr_diff(pr_number, repo_full_name, github_token)
        issues_count = len(analysis.get("issues", [])) if "error" not in analysis else 0
        logger.info("analysis_completed", pr_number=pr_number, issues_count=issues_count, github_event=event)
        print(f"🔍 Analysis done for PR #{pr_number}: {issues_count} issues, {analysis.get('summary', 'N/A')[:50]}")
        
        await post_analysis_comment(pr_number, repo_full_name, github_token, event, analysis)
    except Exception as e:
        logger.error("pr_processing_failed", error=str(e), pr_number=pr_number, repo=repo_full_name)
        print(f"❌ PR processing failed for #{pr_number}: {str(e)}")

# Manual test endpoint
@router.post("/test-pr-analysis")
async def test_pr_analysis(payload: Dict[str, Any]):
    """Test analysis without commenting (provide pr_url)"""
    pr_url = payload.get("pr_url")
    if not pr_url:
        return {"error": "Missing 'pr_url' in payload"}
    
    # Parse from URL
    from urllib.parse import urlparse
    parsed = urlparse(pr_url)
    path_parts = [p for p in parsed.path.strip("/").split("/") if p]
    pulls_idx = path_parts.index("pulls") if "pulls" in path_parts else -1
    if pulls_idx == -1 or pulls_idx < 2:
        return {"error": "Invalid pr_url (expected /repos/owner/repo/pulls/NUMBER)"}
    
    repo_full_name = "/".join(path_parts[pulls_idx-2:pulls_idx])
    pr_number = int(path_parts[pulls_idx+1])
    
    github_token = settings.github_token
    if not github_token:
        return {"error": "GitHub token not set"}
    
    analysis = await analyze_pr_diff(pr_number, repo_full_name, github_token)
    return {"status": "test_complete", "repo": repo_full_name, "pr_number": pr_number, "analysis": analysis}
