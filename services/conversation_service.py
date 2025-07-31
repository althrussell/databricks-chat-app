# services/conversation_service.py - Conversation management service
import os
from typing import List, Dict, Any, Optional
import db
from conversations import default_title_from_prompt, generate_auto_title
from analytics_utils import build_analytics_frames
from auth_utils import get_user_identity

class ConversationService:
    """Handles conversation operations and database interactions"""
    
    def log_conversation(self, conv_id: str, messages: List[Dict[str, Any]], 
                        endpoint: str, tokens_in: int, tokens_out: int):
        """Log conversation messages and usage to database"""
        if not os.getenv("DATABRICKS_WAREHOUSE_ID"):
            return
        
        try:
            user_identity = get_user_identity()
            user_id = user_identity.get("user_id", "unknown_user")
            
            # Ensure conversation exists
            db.ensure_conversation(
                conv_id,
                user_id,
                endpoint,
                title="New Conversation",  # Will be updated later
                email=user_identity.get("email"),
                sql_user=user_identity.get("sql_user"),
            )
            
            # Update conversation model
            db.update_conversation_model(conv_id, endpoint)
            
            # Log the last two messages (user and assistant)
            if len(messages) >= 2:
                user_msg = messages[-2]
                assistant_msg = messages[-1]
                
                db.log_message(conv_id, user_msg["role"], user_msg["content"], 
                              tokens_in=0, tokens_out=0, status="ok")
                db.log_message(conv_id, assistant_msg["role"], assistant_msg["content"], 
                              tokens_in=tokens_in, tokens_out=tokens_out, status="ok")
                
                # Log usage
                db.log_usage(
                    conv_id,
                    user_id,
                    endpoint,
                    tokens_in,
                    tokens_out,
                    email=user_identity.get("email"),
                    sql_user=user_identity.get("sql_user"),
                )
        except Exception as e:
            raise Exception(f"Failed to log conversation: {e}")
    
    def generate_title(self, endpoint: str, messages: List[Dict[str, Any]]) -> str:
        """Generate an automatic title for the conversation"""
        try:
            fallback_title = default_title_from_prompt(messages[0].get("content", ""))
            auto_title = generate_auto_title(endpoint, messages, fallback=fallback_title)
            return auto_title
        except Exception:
            # Fallback to simple title generation
            if messages:
                content = messages[0].get("content", "")
                words = content.split()[:6]
                return " ".join(words) + ("..." if len(content.split()) > 6 else "")
            return "New Conversation"
    
    def get_conversations(self, search: str = "", include_content: bool = False, 
                         limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of conversations for current user"""
        if not os.getenv("DATABRICKS_WAREHOUSE_ID"):
            return []
        
        user_identity = get_user_identity()
        user_id = user_identity.get("user_id", "unknown_user")
        
        return db.list_conversations(
            user_id=user_id,
            search=search,
            limit=limit,
            include_content=include_content
        )
    
    def load_conversation_messages(self, conv_id: str) -> List[Dict[str, Any]]:
        """Load messages for a specific conversation"""
        messages = db.fetch_conversation_messages(conv_id)
        return [{"role": m["role"], "content": m["content"]} for m in messages]
    
    def delete_conversation(self, conv_id: str):
        """Delete a conversation and all related data"""
        db.delete_conversation(conv_id)
    
    def get_analytics_data(self) -> Dict[str, Any]:
        """Get analytics data for current user"""
        if not os.getenv("DATABRICKS_WAREHOUSE_ID"):
            return {"totals": {}, "by_day": None, "by_model": None}
        
        user_identity = get_user_identity()
        user_id = user_identity.get("user_id", "unknown_user")
        
        totals, by_day, by_model = build_analytics_frames(user_id)
        
        return {
            "totals": totals,
            "by_day": by_day,
            "by_model": by_model
        }