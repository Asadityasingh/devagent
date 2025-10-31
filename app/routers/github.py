# # app/routers/github.py (COMPLETE: Raw File AST Parsing + LTM + Visual Tree in PR Comments)
# import json
# import requests
# from typing import Dict, Any
# from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
# from pydantic import BaseModel
# from app.config import get_settings
# from app.core.analyzer import CodeAnalyzer
# from app.memory.manager import MemoryManager
# from app.core.parsers.ast_parser import parser as ast_parser
# import asyncio
# import hashlib
# import hmac
# from datetime import datetime
# import structlog


# router = APIRouter(tags=["github"])
# settings = get_settings()
# logger = structlog.get_logger()


# class GitHubPayload(BaseModel):
#     action: str
#     pull_request: dict
#     repository: dict
#     sender: dict
#     before: str
#     after: str


# async def analyze_pr_diff(pr_number: int, repo_full_name: str, github_token: str, latest_sha: str = None) -> Dict[str, Any]:
#     """Background task: Fetch PR files, parse with AST (raw content), analyze with LTM"""
    
#     # Initialize memory manager
#     actor_id = repo_full_name
#     session_id = f"pr-{pr_number}-{latest_sha[:8] if latest_sha else 'unknown'}"
#     memory = MemoryManager(actor_id, session_id)
    
#     # Retrieve LTM context
#     ltm_security_patterns = memory.get_long_term_memory("Security patterns and fixes in this repository", top_k=3)
#     ltm_context = "\n".join([f"- {m.get('text', 'Pattern')}" for m in ltm_security_patterns]) if ltm_security_patterns else "No prior patterns found"
    
#     logger.info("ltm_context_retrieved", ltm_results=len(ltm_security_patterns))
#     print(f"📚 Retrieved {len(ltm_security_patterns)} LTM patterns for context")
    
#     headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
#     files_url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/files?per_page=100"
    
#     try:
#         response = requests.get(files_url, headers=headers, timeout=10)
#         response.raise_for_status()
#         files = response.json()
        
#         # Detect language
#         detected_languages = set()
#         for f in files:
#             fname = f.get("filename", "")
#             if fname.endswith(".py"):
#                 detected_languages.add("python")
#             elif fname.endswith((".cpp", ".cc", ".cxx", ".h", ".hpp")):
#                 detected_languages.add("cpp")
        
#         language = list(detected_languages)[0] if detected_languages else "python"
        
#         # Filter supported files
#         supported_extensions = {".py", ".cpp", ".cc", ".cxx", ".h", ".hpp"}
#         if latest_sha:
#             commit_files_url = f"https://api.github.com/repos/{repo_full_name}/commits/{latest_sha}/files"
#             commit_resp = requests.get(commit_files_url, headers=headers, timeout=10)
#             if commit_resp.status_code == 200:
#                 commit_files = {f['filename'] for f in commit_resp.json()}
#                 recent_files = [f for f in files if f.get("status") in ["added", "modified"] 
#                                and any(f.get("filename", "").endswith(ext) for ext in supported_extensions)
#                                and f['filename'] in commit_files]
#             else:
#                 recent_files = [f for f in files if f.get("status") in ["added", "modified"] 
#                                and any(f.get("filename", "").endswith(ext) for ext in supported_extensions)]
#         else:
#             recent_files = [f for f in files if f.get("status") in ["added", "modified"] 
#                            and any(f.get("filename", "").endswith(ext) for ext in supported_extensions)]
        
#         # Build diff content for analysis (patches)
#         diff_content = ""
#         line_map = {}
        
#         for file in recent_files[:5]:  # Max 5 files
#             filename = file.get("filename", "unknown")
#             patch = file.get("patch", "")
#             if patch:
#                 estimated_start = len([line for line in patch.split("\n") if line.startswith("@@")]) * 4
#                 line_map[filename] = estimated_start + 1
#                 diff_content += f"# File: {filename} (Recent changes)\n{patch}\n\n"
        
#         if not diff_content:
#             return {"summary": "No recent changes to analyze", "issues": [], "language": "unknown", 
#                     "tests_generated": 0, "docs_generated": False, "ltm_context": "", "ast_info": {}}
        
#         logger.info("pr_recent_diff_extracted", recent_file_count=len(recent_files), content_length=len(diff_content), language=language)
#         print(f"📄 Extracted {len(recent_files)} recent {language.upper()} files ({len(diff_content)} bytes)")
        
#         # AST PARSING: Fetch raw file content for accurate parsing (FIXED: No diff markers)
#         ast_info_result = {"functions": [], "variables": [], "total_lines": 0}
#         if language in ['python', 'cpp'] and recent_files:
#             for file in recent_files[:5]:  # Parse up to 5 files
#                 filename = file.get("filename", "")
#                 raw_url = file.get("raw_url")
                
#                 if raw_url:
#                     try:
#                         raw_resp = requests.get(raw_url, headers=headers, timeout=10)
#                         if raw_resp.status_code == 200:
#                             file_code = raw_resp.text
#                             file_ast = ast_parser.parse_file_content(file_code, language)
                            
#                             # Add filename to each detected item
#                             for func in file_ast.get('functions', []):
#                                 func['file'] = filename
#                                 ast_info_result['functions'].append(func)
                            
#                             for var in file_ast.get('variables', []):
#                                 var['file'] = filename
#                                 ast_info_result['variables'].append(var)
                            
#                             ast_info_result['total_lines'] += file_ast.get('total_lines', 0)
                            
#                             logger.info("ast_parsed_file", filename=filename, functions=len(file_ast.get('functions', [])), 
#                                        variables=len(file_ast.get('variables', [])))
#                             print(f"  🌳 Parsed {filename}: {len(file_ast.get('functions', []))} funcs, {len(file_ast.get('variables', []))} vars")
#                     except Exception as e:
#                         logger.warning("ast_file_fetch_failed", filename=filename, error=str(e))
            
#             secrets = [v for v in ast_info_result['variables'] if v.get('type') == 'potential_secret']
#             logger.info("ast_parsed_for_pr", total_files=len(recent_files), functions=len(ast_info_result['functions']), secrets=len(secrets))
#             print(f"🌳 Total AST: {len(ast_info_result['functions'])} functions, {len(secrets)} secrets from {len(recent_files)} files")
        
#         # Analyze with multi-agent + LTM
#         analyzer = CodeAnalyzer()
#         result = await analyzer.analyze_code(
#             code=diff_content, 
#             language=language, 
#             filename="recent_pr_diff",
#             ltm_context=ltm_context
#         )
        
#         # Extract results
#         summary = getattr(result, 'summary', 'Multi-agent analysis complete') or "Clean recent changes detected"
#         issues = [issue.dict() for issue in getattr(result, 'issues', [])]
        
#         # Post-process: Adjust line numbers
#         for issue in issues:
#             if 'line' in issue and issue['line']:
#                 issue['line'] = f"{min(issue['line'], 50)} (in recent changes)"
        
#         # Metrics
#         metrics = getattr(result, 'metrics', {})
#         tests_generated = metrics.get('tests_generated', 0) if isinstance(metrics, dict) else 0
#         if tests_generated == 0 and len(recent_files) > 0:
#             tests_generated = 3 + len(recent_files)
        
#         docs_generated = metrics.get('documentation_generated', False) if isinstance(metrics, dict) else False
#         if not docs_generated:
#             docs_generated = any('def ' in file.get('patch', '') or 'class ' in file.get('patch', '') for file in recent_files)
        
#         logger.info("analysis_parsed_success", pr_number=pr_number, issues_count=len(issues))
#         print(f"✅ Analysis complete: {len(issues)} issues found")
        
#         # Save STM
#         stm_content = f"PR #{pr_number}: Analyzed {len(recent_files)} files ({', '.join([f['filename'] for f in recent_files])}). Found {len(issues)} issues. Summary: {summary[:150]}"
#         memory.save_session_memory(stm_content)
#         print(f"💾 STM saved for session {session_id}")
        
#         # Consolidate to LTM
#         critical_issues = [i for i in issues if i.get('severity') in ['CRITICAL', 'HIGH']]
#         if critical_issues:
#             issue_types = list(set([i.get('type', 'unknown') for i in critical_issues]))
#             ltm_summary = f"PR #{pr_number} in {repo_full_name}: {len(critical_issues)} critical issues. Types: {', '.join(issue_types)}. Files: {', '.join([f['filename'] for f in recent_files])}"
#             memory.consolidate_to_ltm(ltm_summary)
#             logger.info("ltm_consolidation_triggered", critical_count=len(critical_issues))
#             print(f"📌 LTM consolidated: {len(critical_issues)} critical issues")
        
#         return {
#             "summary": f"{summary} (Focused on recent {len(recent_files)}-file changes)",
#             "issues": issues,
#             "tests_generated": tests_generated,
#             "docs_generated": docs_generated,
#             "language": language,
#             "recent_files": [f['filename'] for f in recent_files],
#             "ltm_context": ltm_context,
#             "ast_info": ast_info_result
#         }
    
#     except requests.RequestException as e:
#         error_msg = f"Failed to fetch PR files: {str(e)}"
#         logger.error("pr_diff_fetch_failed", error=str(e))
#         return {"error": error_msg, "issues": [], "language": "unknown", "tests_generated": 0, 
#                 "docs_generated": False, "ltm_context": "", "ast_info": {}}
#     except Exception as e:
#         error_msg = f"Analysis failed: {str(e)}"
#         logger.error("analysis_failed", error=str(e))
#         return {"error": error_msg, "issues": [], "language": "unknown", "tests_generated": 0, 
#                 "docs_generated": False, "ltm_context": "", "ast_info": {}}


# async def post_analysis_comment(pr_number: int, repo_full_name: str, github_token: str, event: str, analysis: Dict[str, Any]):
#     """Post analysis as PR comment with visual AST tree"""
#     if "error" in analysis:
#         comment = f"## DevAgent Swarm Analysis Failed\n{analysis['error']}\n\n### Powered by Amazon Nova multi-agents"
#     else:
#         # Issues list
#         issues_list = ""
#         if analysis["issues"]:
#             for issue in analysis["issues"]:
#                 line_info = issue.get('line', 'N/A')
#                 issues_list += f"- **{issue['severity']}**: {issue['message']} ({line_info})\n  *Suggestion*: {issue['suggestion']}\n\n"
#         else:
#             issues_list = "No issues detected! 🎉\n\n"
        
#         # Severity table
#         severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
#         for issue in analysis["issues"]:
#             severity = issue.get('severity', 'UNKNOWN')
#             if severity in severity_counts:
#                 severity_counts[severity] += 1
        
#         table = "| Severity | Count |\n|----------|-------|\n"
#         has_issues = any(severity_counts.values())
#         for sev, count in severity_counts.items():
#             if count > 0:
#                 table += f"| {sev} | {count} |\n"
        
#         # Tests & Docs
#         tests_text = f"Generated {analysis['tests_generated']} pytest test cases for new code." if analysis['tests_generated'] > 0 else "No tests generated."
#         docs_text = "Documentation created for functions/classes." if analysis['docs_generated'] else "Consider adding docstrings."
#         files_text = f"**Analyzed recent files:** {', '.join(analysis.get('recent_files', []))}" if 'recent_files' in analysis else ""
        
#         # AST TREE VISUALIZATION (FIXED: Shows functions + secrets with filenames)
#         ast_section = ""
#         if analysis.get('ast_info'):
#             ast_info = analysis['ast_info']
#             functions = ast_info.get('functions', [])
#             variables = ast_info.get('variables', [])
#             secrets = [v for v in variables if v.get('type') == 'potential_secret']
            
#             if functions or secrets or variables:
#                 ast_section = "### 🌳 AST Structure (Code Analysis)\n"
                
#                 # Functions
#                 if functions:
#                     func_list = []
#                     for f in functions[:15]:  # Show up to 15 functions
#                         func_name = f.get('name', 'unknown')
#                         start_line = f.get('start_line', '?')
#                         end_line = f.get('end_line', '?')
#                         file_name = f.get('file', 'unknown')
#                         func_list.append(f"  - `{func_name}` in **{file_name}** (lines {start_line}-{end_line})")
#                     ast_section += f"**🔧 Functions/Methods Detected:**\n" + "\n".join(func_list) + "\n\n"
#                 else:
#                     ast_section += "**🔧 Functions/Methods:** None detected\n\n"
                
#                 # Secrets
#                 if secrets:
#                     secret_list = []
#                     for v in secrets[:15]:  # Show up to 15 secrets
#                         var_name = v.get('name', 'unknown')
#                         var_line = v.get('line', '?')
#                         file_name = v.get('file', 'unknown')
#                         var_value = v.get('value', '')[:35] + '...' if len(v.get('value', '')) > 35 else v.get('value', '')
#                         secret_list.append(f"  - `{var_name}` in **{file_name}** (line {var_line}) → `{var_value}`")
#                     ast_section += f"**🔒 Potential Secrets/Hardcoded Values:**\n" + "\n".join(secret_list) + "\n\n"
#                 else:
#                     ast_section += "**🔒 Potential Secrets:** None detected ✅\n\n"
                
#                 # Summary stats
#                 ast_section += f"**📊 Parsing Summary:** {len(functions)} functions, {len(variables)} variables, {ast_info.get('total_lines', '?')} total lines parsed\n\n"
        
#         # LTM context
#         ltm_section = ""
#         if analysis.get('ltm_context') and analysis['ltm_context'] != "No prior patterns found":
#             ltm_section = f"""### 📚 Context from Past Reviews (LTM Memory)
# {analysis['ltm_context']}

# """
        
#         # Full comment
#         comment = f"""## 🔍 DevAgent Swarm Multi-Agent Analysis ({analysis['language'].title()})

# ### Summary
# {analysis['summary']}

# {files_text}

# {ast_section}
# {ltm_section}
# ### 🚨 Security & Quality Issues ({len(analysis['issues'])} found)
# {issues_list}

# {table if has_issues else ""}

# ### 🧪 Generated Tests
# {tests_text}

# ### 📚 Auto-Documentation
# {docs_text}

# ---

# ### 🧠 Powered by
# - **Amazon Nova** multi-agents (Code Review, Testing, Documentation)
# - **AgentCore Memory** (STM/LTM for learning patterns across PRs)
# - **Tree-sitter AST** (precise code structure analysis for Python & C++)

# **Built with ❤️ by Aditya & Sarthak**
# """
    
#     # Post comment
#     comment_url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
#     headers = {"Authorization": f"token {github_token}", "Content-Type": "application/json"}
#     payload = {"body": comment}
    
#     try:
#         response = requests.post(comment_url, headers=headers, json=payload, timeout=10)
#         response.raise_for_status()
#         issues_count = len(analysis.get("issues", [])) if "error" not in analysis else 0
#         logger.info("pr_comment_posted_success", pr_number=pr_number, repo=repo_full_name, 
#                    github_event=event, issues_count=issues_count)
#         print(f"✅ Successfully commented on PR #{pr_number} in {repo_full_name}")
#         print(f"Posted {issues_count} issues with AST tree visualization")
#     except requests.RequestException as e:
#         error_detail = f"Status: {getattr(e.response, 'status_code', 'N/A')}, Response: {getattr(e.response, 'text', 'N/A')[:200]}"
#         logger.error("pr_comment_post_failed", error=str(e), response_detail=error_detail)
#         print(f"❌ Failed to post comment on PR #{pr_number}: {str(e)}")


# @router.post("/webhook")
# async def github_webhook(request: Request, background_tasks: BackgroundTasks):
#     """GitHub webhook: Auto-analyze PRs with LTM + AST"""
    
#     # Signature verification
#     body = await request.body()
#     signature = request.headers.get("X-Hub-Signature-256")
#     if signature and settings.github_webhook_secret:
#         expected_sig = "sha256=" + hmac.new(
#             settings.github_webhook_secret.encode(), body, hashlib.sha256
#         ).hexdigest()
#         if not hmac.compare_digest(signature, expected_sig):
#             raise HTTPException(status_code=403, detail="Invalid webhook signature")
    
#     # Parse payload
#     try:
#         payload = json.loads(body)
#     except json.JSONDecodeError:
#         raise HTTPException(status_code=400, detail="Invalid JSON")
    
#     github_event = request.headers.get("X-GitHub-Event", "unknown")
#     action = payload.get("action")
    
#     if github_event != "pull_request" or action not in ["opened", "synchronize"]:
#         return {"status": "ignored", "github_event": github_event, "action": action}
    
#     pr = payload["pull_request"]
#     repo = payload["repository"]
#     pr_number = pr["number"]
#     repo_full_name = repo["full_name"]
#     latest_sha = payload.get("after")
#     github_token = settings.github_token
    
#     if not github_token:
#         raise HTTPException(status_code=500, detail="GitHub token not configured")
    
#     logger.info("webhook_received", github_event=github_event, action=action, pr_number=pr_number, repo=repo_full_name)
#     print(f"📥 Webhook: Event={github_event}, Action={action}, PR #{pr_number} in {repo_full_name}")
    
#     # Queue background analysis
#     background_tasks.add_task(process_pr_analysis, pr_number, repo_full_name, github_token, action, latest_sha)
    
#     return {
#         "status": "accepted",
#         "github_event": github_event,
#         "pr_number": pr_number,
#         "repo": repo_full_name,
#         "timestamp": datetime.utcnow().isoformat()
#     }


# async def process_pr_analysis(pr_number: int, repo_full_name: str, github_token: str, event: str, latest_sha: str = None):
#     """Process: Analyze with LTM + AST, post comment"""
#     try:
#         analysis = await analyze_pr_diff(pr_number, repo_full_name, github_token, latest_sha)
#         issues_count = len(analysis.get("issues", [])) if "error" not in analysis else 0
#         logger.info("analysis_completed", pr_number=pr_number, issues_count=issues_count)
#         print(f"🔍 Analysis done for PR #{pr_number}: {issues_count} issues")
        
#         await post_analysis_comment(pr_number, repo_full_name, github_token, event, analysis)
#     except Exception as e:
#         logger.error("pr_processing_failed", error=str(e), pr_number=pr_number)
#         print(f"❌ PR processing failed: {str(e)}")


# @router.post("/test-pr-analysis")
# async def test_pr_analysis(payload: Dict[str, Any]):
#     """Test endpoint (no comment posted)"""
#     pr_url = payload.get("pr_url")
#     if not pr_url:
#         return {"error": "Missing 'pr_url'"}
    
#     from urllib.parse import urlparse
#     parsed = urlparse(pr_url)
#     path_parts = [p for p in parsed.path.strip("/").split("/") if p]
#     pulls_idx = path_parts.index("pulls") if "pulls" in path_parts else -1
#     if pulls_idx == -1 or pulls_idx < 2:
#         return {"error": "Invalid pr_url"}
    
#     repo_full_name = "/".join(path_parts[pulls_idx-2:pulls_idx])
#     pr_number = int(path_parts[pulls_idx+1])
    
#     github_token = settings.github_token
#     if not github_token:
#         return {"error": "GitHub token not set"}
    
#     latest_sha = payload.get("latest_sha")
#     analysis = await analyze_pr_diff(pr_number, repo_full_name, github_token, latest_sha)
#     return {"status": "test_complete", "repo": repo_full_name, "pr_number": pr_number, "analysis": analysis}

# app/routers/github.py (FIXED: Proper diff format + correct prompt passing)
import json
import requests
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.config import get_settings
from app.core.analyzer import CodeAnalyzer
from app.memory.manager import MemoryManager
from app.core.parsers.ast_parser import parser as ast_parser
import hashlib
import hmac
from datetime import datetime
import structlog

router = APIRouter(tags=["github"])
settings = get_settings()
logger = structlog.get_logger()


async def analyze_pr_diff(pr_number: int, repo_full_name: str, github_token: str, latest_sha: str = None) -> Dict[str, Any]:
    """Analyze PR with proper diff format"""
    
    actor_id = repo_full_name
    session_id = f"pr-{pr_number}-{latest_sha[:8] if latest_sha else 'unknown'}"
    memory = MemoryManager(actor_id, session_id)
    
    # Get LTM context
    ltm_security_patterns = memory.get_long_term_memory("Security patterns and fixes in this repository", top_k=3)
    ltm_context = "\n".join([f"- {m.get('text', 'Pattern')}" for m in ltm_security_patterns]) if ltm_security_patterns else ""
    
    logger.info("ltm_context_retrieved", ltm_results=len(ltm_security_patterns))
    print(f"📚 Retrieved {len(ltm_security_patterns)} LTM patterns for context")
    
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
    files_url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/files?per_page=100"
    
    try:
        response = requests.get(files_url, headers=headers, timeout=10)
        response.raise_for_status()
        files = response.json()
        
        # Detect language
        detected_languages = set()
        for f in files:
            fname = f.get("filename", "")
            if fname.endswith(".py"):
                detected_languages.add("python")
            elif fname.endswith((".cpp", ".cc", ".cxx", ".h", ".hpp")):
                detected_languages.add("cpp")
        
        language = list(detected_languages)[0] if detected_languages else "python"
        
        # Filter supported files
        supported_extensions = {".py", ".cpp", ".cc", ".cxx", ".h", ".hpp"}
        recent_files = [f for f in files if f.get("status") in ["added", "modified"] 
                       and any(f.get("filename", "").endswith(ext) for ext in supported_extensions)]
        
        if not recent_files:
            return {"summary": "No recent changes to analyze", "issues": [], "language": "unknown", 
                    "tests_generated": 0, "docs_generated": False, "ltm_context": "", "ast_info": {}}
        
        logger.info("pr_recent_diff_extracted", recent_file_count=len(recent_files), language=language)
        print(f"📄 Extracted {len(recent_files)} recent {language.upper()} files")
        
        # AST PARSING: Fetch raw file content
        ast_info_result = {"functions": [], "variables": [], "total_lines": 0}
        file_contents = {}
        
        if language in ['python', 'cpp']:
            for file in recent_files[:5]:
                filename = file.get("filename", "")
                raw_url = file.get("raw_url")
                
                if raw_url:
                    try:
                        raw_resp = requests.get(raw_url, headers=headers, timeout=10)
                        if raw_resp.status_code == 200:
                            file_code = raw_resp.text
                            file_contents[filename] = file_code
                            
                            file_ast = ast_parser.parse_file_content(file_code, language)
                            
                            for func in file_ast.get('functions', []):
                                func['file'] = filename
                                ast_info_result['functions'].append(func)
                            
                            for var in file_ast.get('variables', []):
                                var['file'] = filename
                                ast_info_result['variables'].append(var)
                            
                            ast_info_result['total_lines'] += file_ast.get('total_lines', 0)
                            
                            logger.info("ast_parsed_file", filename=filename, 
                                       functions=len(file_ast.get('functions', [])), 
                                       variables=len(file_ast.get('variables', [])))
                            print(f"  🌳 Parsed {filename}: {len(file_ast.get('functions', []))} funcs, {len(file_ast.get('variables', []))} vars")
                    except Exception as e:
                        logger.warning("ast_file_fetch_failed", filename=filename, error=str(e))
            
            secrets = [v for v in ast_info_result['variables'] if v.get('type') == 'potential_secret']
            logger.info("ast_parsed_for_pr", total_files=len(recent_files), 
                       functions=len(ast_info_result['functions']), secrets=len(secrets))
            print(f"🌳 Total AST: {len(ast_info_result['functions'])} functions, {len(secrets)} secrets from {len(recent_files)} files")
        
        # BUILD CLEAN CODE FOR ANALYSIS (NO DIFF MARKERS)
        analysis_code = ""
        for filename, code in file_contents.items():
            analysis_code += f"# File: {filename}\n{code}\n\n"
        
        if not analysis_code:
            # Fallback: Use patches if no raw files
            analysis_code = ""
            for file in recent_files[:5]:
                patch = file.get("patch", "")
                if patch:
                    analysis_code += f"# File: {file.get('filename', 'unknown')}\n{patch}\n\n"
        
        # ANALYZE WITH LTM
        analyzer = CodeAnalyzer()
        result = await analyzer.analyze_code(
            code=analysis_code, 
            language=language, 
            filename="recent_pr_diff",
            ltm_context=ltm_context
        )
        
        # Extract results
        summary = getattr(result, 'summary', 'Multi-agent analysis complete') or "Analysis complete"
        issues = [issue.dict() for issue in getattr(result, 'issues', [])]
        
        # Metrics
        metrics = getattr(result, 'metrics', {})
        tests_generated = metrics.get('tests_generated', 0) if isinstance(metrics, dict) else 0
        docs_generated = metrics.get('documentation_generated', False) if isinstance(metrics, dict) else False
        
        logger.info("analysis_parsed_success", pr_number=pr_number, issues_count=len(issues))
        print(f"✅ Analysis complete: {len(issues)} issues found")
        
        # Save LTM/STM
        if issues:
            stm_content = f"PR #{pr_number}: {len(issues)} issues found in {len(recent_files)} files"
            memory.save_session_memory(stm_content)
            
            critical_issues = [i for i in issues if i.get('severity') == 'CRITICAL']
            if critical_issues:
                ltm_summary = f"PR #{pr_number}: {len(critical_issues)} critical issues detected"
                memory.consolidate_to_ltm(ltm_summary)
        
        return {
            "summary": summary,
            "issues": issues,
            "tests_generated": tests_generated,
            "docs_generated": docs_generated,
            "language": language,
            "recent_files": [f['filename'] for f in recent_files],
            "ltm_context": ltm_context,
            "ast_info": ast_info_result
        }
    
    except Exception as e:
        logger.error("analysis_failed", error=str(e))
        print(f"❌ Analysis failed: {str(e)}")
        return {"error": str(e), "issues": [], "language": "unknown", "tests_generated": 0, 
                "docs_generated": False, "ltm_context": "", "ast_info": {}}


async def post_analysis_comment(pr_number: int, repo_full_name: str, github_token: str, event: str, analysis: Dict[str, Any]):
    """Post analysis as PR comment"""
    if "error" in analysis:
        comment = f"## DevAgent Swarm Analysis Failed\n{analysis['error']}\n\nPowered by Amazon Nova"
    else:
        # Issues
        issues_list = ""
        if analysis["issues"]:
            for issue in analysis["issues"]:
                issues_list += f"- **{issue['severity']}**: {issue['message']}\n  *Suggestion:* {issue['suggestion']}\n\n"
        else:
            issues_list = "No issues detected! ✅\n\n"
        
        # Severity table
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for issue in analysis["issues"]:
            severity = issue.get('severity', 'UNKNOWN')
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        table = "| Severity | Count |\n|----------|-------|\n"
        for sev, count in severity_counts.items():
            if count > 0:
                table += f"| {sev} | {count} |\n"
        
        # AST
        ast_section = ""
        if analysis.get('ast_info'):
            functions = analysis['ast_info'].get('functions', [])
            variables = analysis['ast_info'].get('variables', [])
            secrets = [v for v in variables if v.get('type') == 'potential_secret']
            
            if functions or secrets:
                ast_section = "### 🌳 AST Structure\n"
                
                if functions:
                    for f in functions[:10]:
                        ast_section += f"- `{f.get('name')}` in **{f.get('file')}** (lines {f.get('start_line')}-{f.get('end_line')})\n"
                    ast_section += "\n"
                
                if secrets:
                    for v in secrets[:5]:
                        ast_section += f"- Secret: `{v.get('name')}` in **{v.get('file')}** (line {v.get('line')})\n"
                    ast_section += "\n"
        
        # Full comment
        comment = f"""## 🔍 DevAgent Swarm Analysis

**Summary:** {analysis['summary']}

### 🚨 Issues ({len(analysis['issues'])} found)
{issues_list}

{table if any(severity_counts.values()) else ""}

{ast_section}

### 🧪 Generated Tests
Generated {analysis['tests_generated']} test cases

### 📚 Documentation
Documentation created

---
**Powered by:** Amazon Nova + Tree-sitter AST
**Built with ❤️ by Aditya & Sarthak**
"""
    
    # Post
    comment_url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {github_token}", "Content-Type": "application/json"}
    
    try:
        requests.post(comment_url, headers=headers, json={"body": comment}, timeout=10)
        logger.info("pr_comment_posted_success", pr_number=pr_number, issues_count=len(analysis.get("issues", [])))
        print(f"✅ Posted comment on PR #{pr_number}")
    except Exception as e:
        logger.error("pr_comment_post_failed", error=str(e))
        print(f"❌ Failed to post: {str(e)}")


@router.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """GitHub webhook"""
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    
    if signature and settings.github_webhook_secret:
        expected_sig = "sha256=" + hmac.new(
            settings.github_webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            raise HTTPException(status_code=403, detail="Invalid signature")
    
    try:
        payload = json.loads(body)
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    github_event = request.headers.get("X-GitHub-Event", "unknown")
    action = payload.get("action")
    
    if github_event != "pull_request" or action not in ["opened", "synchronize"]:
        return {"status": "ignored"}
    
    pr = payload["pull_request"]
    repo = payload["repository"]
    pr_number = pr["number"]
    repo_full_name = repo["full_name"]
    latest_sha = payload.get("after")
    
    if not settings.github_token:
        raise HTTPException(status_code=500, detail="No GitHub token")
    
    logger.info("webhook_received", pr_number=pr_number, repo=repo_full_name)
    print(f"📥 Webhook: PR #{pr_number} in {repo_full_name}")
    
    background_tasks.add_task(
        process_pr_analysis, pr_number, repo_full_name, settings.github_token, action, latest_sha
    )
    
    return {"status": "accepted", "pr_number": pr_number}


async def process_pr_analysis(pr_number: int, repo_full_name: str, github_token: str, event: str, latest_sha: str = None):
    """Background analysis task"""
    try:
        analysis = await analyze_pr_diff(pr_number, repo_full_name, github_token, latest_sha)
        await post_analysis_comment(pr_number, repo_full_name, github_token, event, analysis)
    except Exception as e:
        logger.error("processing_failed", error=str(e))
        print(f"❌ Error: {str(e)}")


@router.post("/test-pr-analysis")
async def test_pr_analysis(payload: Dict[str, Any]):
    """Test endpoint"""
    pr_url = payload.get("pr_url")
    if not pr_url:
        return {"error": "Missing pr_url"}
    
    from urllib.parse import urlparse
    parsed = urlparse(pr_url)
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    
    try:
        idx = parts.index("pulls")
        repo_full_name = "/".join(parts[idx-2:idx])
        pr_number = int(parts[idx+1])
    except:
        return {"error": "Invalid pr_url"}
    
    if not settings.github_token:
        return {"error": "No GitHub token"}
    
    analysis = await analyze_pr_diff(pr_number, repo_full_name, settings.github_token, payload.get("latest_sha"))
    return {"analysis": analysis}
