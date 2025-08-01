# ui/main_content.py - Main content area rendering (updated)
import streamlit as st
from .pages import ChatPage, HistoryPage, AnalyticsPage, SettingsPage

class MainContentRenderer:
    """Handles main content area rendering and page routing"""
    
    def __init__(self, state_manager, model_service, conversation_service):
        """Initialize main content renderer"""
        self.state_manager = state_manager
        self.model_service = model_service
        self.conversation_service = conversation_service
        
        # Initialize page renderers
        self.pages = {
            "chat": ChatPage(state_manager, model_service, conversation_service),
            "history": HistoryPage(state_manager, model_service, conversation_service),
            "analytics": AnalyticsPage(state_manager, model_service, conversation_service),
            "settings": SettingsPage(state_manager, model_service, conversation_service)
        }
    
    def render(self):
        """Render the main content area"""
        self._render_header()
        self._render_current_page()
    
    def _render_header(self):
        """Render the executive header with status indicator"""
        current_page = self.state_manager.get_current_page()
        
        # Page information
        page_info = {
            "chat": {
                "title": self.state_manager.get_chat_title(),
                "subtitle": ""
            },
            "history": {
                "title": "Conversation History",
                "subtitle": "Review and manage your previous interactions"
            },
            "analytics": {
                "title": "Usage Analytics",
                "subtitle": "Insights into platform utilization and performance"
            },
            "settings": {
                "title": "Platform Settings",
                "subtitle": "Configure your AI workspace and preferences"
            }
        }
        
        current_info = page_info.get(current_page, {
            "title": "Databricks Intelligence Platform",
            "subtitle": "Enterprise AI at scale"
        })
        
        # Status indicator
        endpoint = self.state_manager.get_selected_endpoint()
        endpoint_status = "Connected" if endpoint else "Disconnected"
        
        st.markdown(f"""
        <div class="executive-header">
            <h1>{current_info['title']}</h1>
            <p class="subtitle">{current_info['subtitle']}</p>
            <div class="status-indicator">
                <span>●</span> {endpoint_status}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_current_page(self):
        """Render the currently active page"""
        current_page = self.state_manager.get_current_page()
        
        if current_page in self.pages:
            self.pages[current_page].render()
        else:
            st.error(f"Unknown page: {current_page}")
            self.state_manager.navigate_to("chat")