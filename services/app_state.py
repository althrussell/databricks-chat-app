# services/app_state.py - Centralized application state management
import uuid
from typing import Dict, Any, List, Optional
import streamlit as st

class AppStateManager:
    """Manages all application state in Streamlit session"""
    
    def __init__(self):
        """Initialize state manager"""
        self.state = st.session_state
    
    def initialize(self):
        """Initialize all session state variables"""
        self._init_conversation_state()
        self._init_navigation_state()
        self._init_model_endpoints()
    
    def _init_conversation_state(self):
        """Initialize conversation-related state"""
        if "messages" not in self.state:
            self.state.messages = []
        if "conv_id" not in self.state:
            self.state.conv_id = str(uuid.uuid4())
        if "chat_title" not in self.state:
            self.state.chat_title = "New Conversation"
    
    def _init_navigation_state(self):
        """Initialize navigation state"""
        if "current_page" not in self.state:
            self.state.current_page = "chat"
    
    def _init_model_endpoints(self):
        """Initialize model endpoint configuration"""
        if "selected_endpoint" not in self.state:
            from services.model_service import ModelService
            model_service = ModelService()
            endpoints, default_idx = model_service.get_available_endpoints()
            self.state.selected_endpoint = endpoints[default_idx]["id"] if endpoints else ""
    
    # Navigation methods
    def get_current_page(self) -> str:
        """Get current active page"""
        return self.state.current_page
    
    def set_current_page(self, page: str):
        """Set current active page"""
        self.state.current_page = page
    
    def navigate_to(self, page: str):
        """Navigate to a specific page"""
        self.set_current_page(page)
        st.rerun()
    
    # Conversation methods
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get conversation messages"""
        return self.state.messages
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation"""
        self.state.messages.append({"role": role, "content": content})
    
    def clear_conversation(self):
        """Clear current conversation"""
        self.state.messages = []
        self.state.conv_id = str(uuid.uuid4())
        self.state.chat_title = "New Conversation"
    
    def get_conversation_id(self) -> str:
        """Get current conversation ID"""
        return self.state.conv_id
    
    def set_conversation_id(self, conv_id: str):
        """Set conversation ID"""
        self.state.conv_id = conv_id
    
    def get_chat_title(self) -> str:
        """Get current chat title"""
        return self.state.chat_title
    
    def set_chat_title(self, title: str):
        """Set chat title"""
        self.state.chat_title = title
    
    def load_conversation(self, conv_id: str, title: str, messages: List[Dict[str, Any]]):
        """Load a conversation from history"""
        self.state.conv_id = conv_id
        self.state.chat_title = title
        self.state.messages = messages
        self.navigate_to("chat")
    
    # Model endpoint methods
    def get_selected_endpoint(self) -> str:
        """Get currently selected model endpoint"""
        return self.state.selected_endpoint
    
    def set_selected_endpoint(self, endpoint: str):
        """Set model endpoint"""
        self.state.selected_endpoint = endpoint
    
    # Utility methods
    def should_generate_response(self) -> bool:
        """Check if assistant should generate a response"""
        return (
            bool(self.state.messages) and
            self.state.messages[-1]["role"] == "user" and
            len(self.state.messages) % 2 == 1
        )
    
    def is_new_conversation(self) -> bool:
        """Check if this is a new conversation"""
        return self.state.chat_title == "New Conversation" and len(self.state.messages) >= 2