# app/memory/manager.py (FIXED: Correct AWS Service + Graceful Fallback)
import boto3
from typing import List, Dict, Any
from app.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()

class MemoryManager:
    """Manages short-term (STM) and long-term (LTM) memory for agents"""
    
    def __init__(self, actor_id: str, session_id: str):
        """
        actor_id: Unique per repo (e.g., 'Asadityasingh/devagent-test')
        session_id: Per PR/webhook event (e.g., 'pr-1-sync-abc123')
        """
        self.actor_id = f"{settings.memory_actor_id_prefix}/{actor_id}"
        self.session_id = session_id
        self.memory_id = settings.agentcore_memory_id
        
        try:
            # FIXED: Use 'bedrock-agentcore' (valid service per boto3)
            self.client = boto3.client('bedrock-agentcore', region_name=settings.aws_region)
            logger.info("memory_manager_initialized", actor_id=self.actor_id, session_id=session_id, service="bedrock-agentcore")
        except Exception as e:
            logger.error("memory_client_init_failed", error=str(e), actor_id=self.actor_id)
            self.client = None  # Graceful fallback: No memory if client fails
    
    def get_long_term_memory(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve relevant LTM for query (e.g., 'SQLi patterns in this repo')"""
        if not self.client or not self.memory_id:
            logger.warning("ltm_skip_no_client", reason="No client or memory ID")
            return []
        
        try:
            response = self.client.retrieve_memory(
                memoryId=self.memory_id,
                actorId=self.actor_id,
                query=query,
                maxResults=top_k
            )
            results = response.get('retrievalResults', [])
            logger.info("ltm_retrieval_success", query=query, results_count=len(results))
            return results
        except Exception as e:
            logger.error("ltm_retrieval_failed", error=str(e), query=query)
            return []
    
    def save_session_memory(self, content: str, memory_type: str = "session"):
        """Save STM (current PR context) to session"""
        if not self.client or not self.memory_id:
            logger.warning("stm_skip_no_client", reason="No client or memory ID")
            return
        
        try:
            self.client.put_memory(
                memoryId=self.memory_id,
                actorId=self.actor_id,
                sessionId=self.session_id,
                memoryType=memory_type,
                content=content
            )
            logger.info("stm_saved", memory_type=memory_type, content_len=len(content))
        except Exception as e:
            logger.error("stm_save_failed", error=str(e))
    
    def consolidate_to_ltm(self, summary: str):
        """Extract key insights from session → LTM"""
        if not self.client or not self.memory_id:
            logger.warning("ltm_consolidation_skip", reason="No client or memory ID")
            return
        
        try:
            self.client.put_memory(
                memoryId=self.memory_id,
                actorId=self.actor_id,
                sessionId=self.session_id,
                memoryType="long-term",
                content=f"[PR Analysis] {summary}"
            )
            logger.info("ltm_consolidation_success", summary_len=len(summary))
        except Exception as e:
            logger.error("ltm_consolidation_failed", error=str(e))
