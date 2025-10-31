# from pydantic_settings import BaseSettings
# from functools import lru_cache
# from typing import Optional

# class Settings(BaseSettings):
#     """Application settings"""
    
#     # AWS
#     aws_region: str = "us-east-1"
#     aws_bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    
#     # Database
#     database_url: str = "sqlite:///./devagent.db"
    
#     # Redis
#     redis_url: str = "redis://localhost:6379/0"
    
#     # GitHub
#     github_token: Optional[str] = None
    
#     # JWT
#     jwt_secret: str
#     jwt_algorithm: str = "HS256"
    
#     # Application
#     environment: str = "development"
#     debug: bool = True
#     log_level: str = "INFO"

#         # New: AgentCore Memory
#     # agentcore_memory_id: str  # From AWS Console (mem-abc123)
#     # memory_actor_id_prefix: str = "repo"  # Prefix for actor IDs (e.g., repo/user/repo-name)
#     # memory_stm_retention_days: int = 7
#     # memory_ltm_retention_days: int = 365

#     agentcore_memory_id: str = ""
#     memory_actor_id_prefix: str = "repo"
#     memory_stm_retention_days: int = 7
#     memory_ltm_retention_days: int = 365
#     github_webhook_secret: str = None
    
#     # ===== BEDROCK AGENTS =====
    
#     # IAM Role
#     bedrock_role_arn: Optional[str] = None
    
#     # Supervisor Agent
#     bedrock_supervisor_agent_id: Optional[str] = None
#     bedrock_supervisor_alias_id: str = "TSTALIASID"
    
#     # Code Review Agent
#     bedrock_code_review_agent_id: Optional[str] = None
#     bedrock_code_review_alias_id: str = "TSTALIASID"
    
#     # Testing Agent
#     bedrock_testing_agent_id: Optional[str] = None
#     bedrock_testing_alias_id: str = "TSTALIASID"
    
#     # Documentation Agent
#     bedrock_docs_agent_id: Optional[str] = None
#     bedrock_docs_alias_id: str = "TSTALIASID"
    
#     class Config:
#         env_file = ".env"
#         case_sensitive = False

# @lru_cache()
# def get_settings() -> Settings:
#     """Get cached settings instance"""
#     return Settings()

# # Test it
# if __name__ == "__main__":
#     settings = get_settings()
#     print(f"✅ Configuration loaded!")
#     print(f"Supervisor Agent: {settings.bedrock_supervisor_agent_id}")
#     print(f"Supervisor Alias: {settings.bedrock_supervisor_alias_id}")
#     print(f"CodeReview Agent: {settings.bedrock_code_review_agent_id}")
#     print(f"CodeReview Alias: {settings.bedrock_code_review_alias_id}")

# app/config.py (Full: Fixed Optional Fields + Memory Integration)
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings with AgentCore Memory support"""
    
    # ===== AWS CONFIGURATION =====
    aws_region: str = "us-east-1"
    aws_bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    # ===== DATABASE =====
    database_url: str = "sqlite:///./devagent.db"
    
    # ===== REDIS =====
    redis_url: str = "redis://localhost:6379/0"
    
    # ===== GITHUB =====
    github_token: Optional[str] = None
    github_webhook_secret: Optional[str] = None  # FIXED: Optional, not required
    
    # ===== JWT =====
    jwt_secret: str = "dev-secret-key-change-in-prod"  # Default for dev, override in .env
    jwt_algorithm: str = "HS256"
    
    # ===== APPLICATION =====
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # ===== AGENTCORE MEMORY (STM/LTM) =====
    agentcore_memory_id: Optional[str] = None  # FIXED: Optional, from AWS Console (mem-abc123)
    memory_actor_id_prefix: str = "repo"  # Prefix for actor IDs (e.g., repo/user/repo-name)
    memory_stm_retention_days: int = 7  # Short-term memory retention (days)
    memory_ltm_retention_days: int = 365  # Long-term memory retention (days)
    
    # ===== BEDROCK IAM ROLE =====
    bedrock_role_arn: Optional[str] = None
    
    # ===== BEDROCK SUPERVISOR AGENT =====
    bedrock_supervisor_agent_id: Optional[str] = None
    bedrock_supervisor_alias_id: str = "TSTALIASID"
    
    # ===== BEDROCK CODE REVIEW AGENT =====
    bedrock_code_review_agent_id: Optional[str] = None
    bedrock_code_review_alias_id: str = "TSTALIASID"
    
    # ===== BEDROCK TESTING AGENT =====
    bedrock_testing_agent_id: Optional[str] = None
    bedrock_testing_alias_id: str = "TSTALIASID"
    
    # ===== BEDROCK DOCUMENTATION AGENT =====
    bedrock_docs_agent_id: Optional[str] = None
    bedrock_docs_alias_id: str = "TSTALIASID"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Test it
if __name__ == "__main__":
    settings = get_settings()
    print(f"✅ Configuration loaded!")
    print(f"\n=== AWS & Bedrock ===")
    print(f"AWS Region: {settings.aws_region}")
    print(f"Bedrock Model: {settings.aws_bedrock_model_id}")
    print(f"Supervisor Agent: {settings.bedrock_supervisor_agent_id}")
    print(f"Code Review Agent: {settings.bedrock_code_review_agent_id}")
    
    print(f"\n=== Memory (AgentCore) ===")
    print(f"Memory ID: {settings.agentcore_memory_id}")
    print(f"Memory Prefix: {settings.memory_actor_id_prefix}")
    print(f"STM Retention: {settings.memory_stm_retention_days} days")
    print(f"LTM Retention: {settings.memory_ltm_retention_days} days")
    
    print(f"\n=== GitHub ===")
    print(f"GitHub Token: {'✅ Set' if settings.github_token else '❌ Not set'}")
    print(f"Webhook Secret: {'✅ Set' if settings.github_webhook_secret else '⚠️  Optional (not set)'}")
    
    print(f"\n=== Application ===")
    print(f"Environment: {settings.environment}")
    print(f"Debug: {settings.debug}")
    print(f"Log Level: {settings.log_level}")
