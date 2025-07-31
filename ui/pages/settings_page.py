# ui/pages/settings_page.py - Configuration settings page
import streamlit as st
import os
import json
from conversations import export_conversation_json
from auth_utils import get_user_identity
import db
from .base_page import BasePage

class SettingsPage(BasePage):
    """Settings page renderer - Configuration and preferences"""
    
    def render(self):
        """Render the settings page"""
        self._render_model_configuration()
        st.markdown("---")
        self._render_user_authentication()
        st.markdown("---")
        self._render_conversation_management()
        st.markdown("---")
        self._render_system_configuration()
    
    def _render_model_configuration(self):
        """Render model configuration section"""
        st.subheader("🤖 Model Configuration")
        
        endpoints, _ = self.model_service.get_available_endpoints()
        
        if not endpoints or (len(endpoints) == 1 and not endpoints[0]["id"]):
            self._render_no_endpoints_configured()
            return
        
        names = [m["name"] for m in endpoints]
        display_to_id = {m["name"]: m["id"] for m in endpoints}
        
        current_endpoint = self.state_manager.get_selected_endpoint()
        try:
            current_idx = [m["id"] for m in endpoints].index(current_endpoint)
        except ValueError:
            current_idx = 0
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            picked_name = st.selectbox(
                "Active Model Endpoint", 
                names, 
                index=current_idx,
                help="Select the AI model endpoint for conversation processing"
            )
            
            picked_endpoint = display_to_id[picked_name]
            
            if picked_endpoint != current_endpoint:
                self.state_manager.set_selected_endpoint(picked_endpoint)
                st.success(f"✅ Model endpoint updated to: **{picked_endpoint}**")
                
                if os.getenv("DATABRICKS_WAREHOUSE_ID"):
                    db.update_conversation_model(
                        self.state_manager.get_conversation_id(), 
                        picked_endpoint
                    )
                st.rerun()
        
        with col2:
            if st.button("🧪 Test Connection", use_container_width=True):
                self._test_selected_endpoint()
    
    def _render_no_endpoints_configured(self):
        """Render message when no endpoints are configured"""
        st.error("❌ No model endpoints configured")
        
        with st.expander("Configuration Help"):
            st.markdown("""
            **To configure model endpoints:**
            
            Set environment variables:
            ```bash
            export SERVING_ENDPOINT="your-primary-endpoint"
            export SERVING_ENDPOINTS_CSV="endpoint1|Name 1,endpoint2|Name 2"
            ```
            
            Contact your administrator for available endpoints.
            """)
    
    def _test_selected_endpoint(self):
        """Test the currently selected endpoint"""
        endpoint = self.state_manager.get_selected_endpoint()
        if not endpoint:
            st.error("No endpoint selected")
            return
        
        try:
            with st.spinner("Testing connection..."):
                success, message = self.model_service.test_endpoint(endpoint)
            
            if success:
                st.success(f"✅ Connection successful: {message}")
            else:
                st.error(f"❌ Connection failed: {message}")
        except Exception as e:
            st.error(f"Test failed: {e}")
    
    def _render_user_authentication(self):
        """Render user authentication section"""
        st.subheader("👤 User Authentication")
        user_identity = get_user_identity()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Email:** {user_identity.get('email', 'System Account')}")
            st.info(f"**Database User:** {user_identity.get('sql_user', 'Not Available')}")
        
        with col2:
            st.info(f"**Auth Mode:** {user_identity.get('auth_mode', 'Service Principal')}")
            st.info(f"**User ID:** {user_identity.get('user_id', 'System')}")
    
    def _render_conversation_management(self):
        """Render conversation management section"""
        st.subheader("💬 Conversation Management")
        
        current_title = self.state_manager.get_chat_title()
        new_title = st.text_input(
            "Current Conversation Title",
            value=current_title,
            help="Customize the title for your current conversation"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Update Title", use_container_width=True):
                self.state_manager.set_chat_title(new_title or "Untitled Conversation")
                if os.getenv("DATABRICKS_WAREHOUSE_ID"):
                    db.update_conversation_title(self.state_manager.get_conversation_id(), new_title)
                st.success("✅ Conversation title updated successfully")
        
        with col2:
            # Export current conversation
            if os.getenv("DATABRICKS_WAREHOUSE_ID"):
                export_data = export_conversation_json(self.state_manager.get_conversation_id())
            else:
                export_data = json.dumps({"messages": self.state_manager.get_messages()}, indent=2, default=str)
            
            st.download_button(
                "⬇️ Export Conversation",
                data=export_data,
                file_name=f"conversation_{self.state_manager.get_conversation_id()}.json",
                mime="application/json",
                use_container_width=True
            )
    
    def _render_system_configuration(self):
        """Render system configuration section"""
        st.subheader("🔧 System Configuration")
        
        config_data = {
            "SQL Warehouse": os.getenv("DATABRICKS_WAREHOUSE_ID", "Not configured"),
            "Data Catalog": os.getenv("CATALOG", "shared"),
            "Schema": os.getenv("SCHEMA", "app"),
            "Context Window": f"{os.getenv('MAX_TURNS', '12')} turns",
            "Data Logging": "Enabled" if os.getenv("ENABLE_LOGGING", "1") == "1" else "Disabled",
            "User SQL Execution": "Enabled" if os.getenv("RUN_SQL_AS_USER", "0") == "1" else "Disabled"
        }
        
        for key, value in config_data.items():
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write(f"**{key}:**")
            with col2:
                st.code(value)