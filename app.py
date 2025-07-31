# app.py - Main application entry point
import os
import uuid
from typing import Dict, Any, List

import streamlit as st

from ui.sidebar import SidebarRenderer
from ui.main_content import MainContentRenderer
from ui.styling import apply_executive_styling
from services.app_state import AppStateManager
from services.model_service import ModelService
from services.conversation_service import ConversationService
from auth_utils import setup_request_context

class DatabricksIntelligenceApp:
    """Main application class for Databricks Intelligence Platform"""
    
    def __init__(self):
        """Initialize the application"""
        self.setup_streamlit()
        self.state_manager = AppStateManager()
        self.model_service = ModelService()
        self.conversation_service = ConversationService()
        self.sidebar_renderer = SidebarRenderer(
            self.state_manager, 
            self.model_service, 
            self.conversation_service
        )
        self.main_content_renderer = MainContentRenderer(
            self.state_manager, 
            self.model_service, 
            self.conversation_service
        )
    
    def setup_streamlit(self):
        """Configure Streamlit for executive-grade experience"""
        st.set_page_config(
            page_title="Databricks Intelligence Platform", 
            layout="wide", 
            page_icon="🎯",
            initial_sidebar_state="expanded"
        )
        
        # Setup authentication and styling
        setup_request_context()
        apply_executive_styling()
    
    def run(self):
        """Main application entry point"""
        # Initialize application state
        self.state_manager.initialize()
        
        # Render UI components
        self.sidebar_renderer.render()
        self.main_content_renderer.render()

def main():
    """Application entry point"""
    app = DatabricksIntelligenceApp()
    app.run()

if __name__ == "__main__":
    main()