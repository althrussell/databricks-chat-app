# ui/sidebar.py - Sidebar navigation component
import streamlit as st
from auth_utils import get_user_identity
import os

class SidebarRenderer:
    """Handles sidebar rendering and navigation"""
    
    def __init__(self, state_manager, model_service, conversation_service):
        """Initialize sidebar renderer"""
        self.state_manager = state_manager
        self.model_service = model_service
        self.conversation_service = conversation_service
    
    def render(self):
        """Render the executive-grade sidebar"""
        with st.sidebar:
            self._render_header()
            self._render_navigation()
            self._render_quick_actions()
            self._render_status()
    
    def _render_header(self):
        """Render sidebar header"""
        st.markdown("### Databricks Intelligence")
        st.caption("Enterprise AI Platform")
        st.markdown("---")
    
    def _render_navigation(self):
        """Render navigation menu"""
        st.markdown("#### Navigation")
        
        nav_items = [
            {"key": "chat", "label": "Chat"},
            {"key": "history", "label": "History"},
            {"key": "analytics", "label": "Analytics"},
            {"key": "settings", "label": "Settings"}
        ]
        
        for item in nav_items:
            is_active = self.state_manager.get_current_page() == item["key"]
            button_type = "primary" if is_active else "secondary"
            
            if st.button(
                item["label"],
                key=f"nav_{item['key']}",
                type=button_type,
                use_container_width=True
            ):
                self.state_manager.navigate_to(item["key"])
        
        st.markdown("---")
    
    def _render_quick_actions(self):
        """Render quick action buttons"""
        st.markdown("#### Quick Actions")
        
        if st.button("New Conversation", use_container_width=True, key="new_conversation"):
            self.state_manager.clear_conversation()
            self.state_manager.navigate_to("chat")
        
        if st.button("Test Connection", use_container_width=True, key="test_connection"):
            self._test_model_endpoint()
        
        st.markdown("---")
    
    def _render_status(self):
        """Render system status information"""
        st.markdown("#### System Status")
        
        # Endpoint status
        endpoint = self.state_manager.get_selected_endpoint()
        if endpoint:
            st.markdown(f"""
            <div class="status-card status-success">
                <strong>Model Endpoint</strong><br>
                <small>{endpoint}</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-card status-error">
                <strong>Model Endpoint</strong><br>
                <small>Not configured</small>
            </div>
            """, unsafe_allow_html=True)
        
        # SQL Logging status
        sql_logging_ok = bool(os.getenv("DATABRICKS_WAREHOUSE_ID"))
        status_class = "status-success" if sql_logging_ok else "status-warning"
        status_text = "Active" if sql_logging_ok else "Disabled"
        
        st.markdown(f"""
        <div class="status-card {status_class}">
            <strong>Data Logging</strong><br>
            <small>{status_text}</small>
        </div>
        """, unsafe_allow_html=True)
        
        # User info
        user_identity = get_user_identity()
        auth_mode = user_identity.get("auth_mode", "Service Principal")
        email = user_identity.get('email', 'System Account')
        
        st.markdown(f"""
        <div class="status-card status-success">
            <strong>Authentication</strong><br>
            <small>{auth_mode}</small>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="status-card">
            <strong>Current User</strong><br>
            <small>{email}</small>
        </div>
        """, unsafe_allow_html=True)
    
    def _test_model_endpoint(self):
        """Test the currently selected model endpoint"""
        endpoint = self.state_manager.get_selected_endpoint()
        if not endpoint:
            st.error("No endpoint configured")
            return
        
        try:
            with st.spinner("Testing connection..."):
                success, message = self.model_service.test_endpoint(endpoint)
            
            if success:
                st.success(f"Connection successful: {message}")
            else:
                st.error(f"Connection failed: {message}")
        except Exception as e:
            st.error(f"Test failed: {e}")