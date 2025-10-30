
# # app/config.py
# from pydantic_settings import BaseSettings, SettingsConfigDict
# from functools import lru_cache
# from typing import Optional


# class Settings(BaseSettings):
#     """Application settings"""
    
#     # AWS
#     aws_region: str = "us-east-1"
#     aws_bedrock_model_id: str = "amazon.nova-pro-v1:0"
    
#     # Database
#     database_url: str = "sqlite:///./devagent.db"
    
#     # Redis
#     redis_url: str = "redis://localhost:6379/0"
    
#     # GitHub
#     github_token: Optional[str] = None
    
#     # JWT
#     jwt_secret: str = "your-secret-key-change-in-production"
#     jwt_algorithm: str = "HS256"
    
#     # Application
#     environment: str = "development"
#     debug: bool = True
#     log_level: str = "INFO"
    
#     # Bedrock Agents
#     bedrock_supervisor_agent_id: Optional[str] = None
#     bedrock_alias_id: Optional[str] = "TSTALIASID"
#     bedrock_role_arn: Optional[str] = None  # ADD THIS
#     bedrock_code_review_agent_id: Optional[str] = None  # ADD THIS
    
#     # Use model_config instead of nested Config class
#     model_config = SettingsConfigDict(
#         env_file=".env",
#         env_file_encoding="utf-8",
#         extra="allow",  # Allow extra fields from .env
#         case_sensitive=False
#     )


# @lru_cache()
# def get_settings() -> Settings:
#     """Get cached settings instance"""
#     return Settings()


# # Test it
# if __name__ == "__main__":
#     settings = get_settings()
#     print(f"Environment: {settings.environment}")
#     print(f"AWS Region: {settings.aws_region}")
#     print(f"Debug: {settings.debug}")
#     print(f"Bedrock Agent: {settings.bedrock_code_review_agent_id}")

# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # AWS
    aws_region: str = "us-east-1"
    aws_bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    # Database
    database_url: str = "sqlite:///./devagent.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # GitHub
    github_token: Optional[str] = None
    
    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    
    # Application
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # ===== BEDROCK AGENTS =====
    
    # IAM Role
    bedrock_role_arn: Optional[str] = None
    
    # Supervisor Agent
    bedrock_supervisor_agent_id: Optional[str] = None
    bedrock_supervisor_alias_id: str = "TSTALIASID"
    
    # Code Review Agent
    bedrock_code_review_agent_id: Optional[str] = None
    bedrock_code_review_alias_id: str = "TSTALIASID"
    
    # Testing Agent
    bedrock_testing_agent_id: Optional[str] = None
    bedrock_testing_alias_id: str = "TSTALIASID"
    
    # Documentation Agent
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
    print(f"Supervisor Agent: {settings.bedrock_supervisor_agent_id}")
    print(f"Supervisor Alias: {settings.bedrock_supervisor_alias_id}")
    print(f"CodeReview Agent: {settings.bedrock_code_review_agent_id}")
    print(f"CodeReview Alias: {settings.bedrock_code_review_alias_id}")
