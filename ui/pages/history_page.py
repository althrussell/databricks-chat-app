# ui/pages/history_page.py - Conversation history page
import streamlit as st
import os
from typing import Dict, Any
from conversations import export_conversation_json
from .base_page import BasePage

class HistoryPage(BasePage):
    """History page renderer - Conversation management"""
    
    def render(self):
        """Render the conversation history page"""
        if not self._is_logging_enabled():
            self._render_logging_disabled_message()
            return
        
        search_params = self._render_search_controls()
        st.markdown("---")
        self._render_conversations_list(search_params)
    
    def _is_logging_enabled(self) -> bool:
        """Check if SQL logging is enabled"""
        return bool(os.getenv("DATABRICKS_WAREHOUSE_ID"))
    
    def _render_logging_disabled_message(self):
        """Render message when logging is disabled"""
        st.info("📊 Data logging is disabled. Enable SQL logging to view conversation history.")
        
        with st.expander("How to Enable Conversation History"):
            st.markdown("""
            **Configuration Steps:**
            1. Set `DATABRICKS_WAREHOUSE_ID` environment variable
            2. Configure `CATALOG` and `SCHEMA` (defaults: shared.app)
            3. Ensure proper database permissions are granted
            4. Restart the application
            """)
    
    def _render_search_controls(self) -> Dict[str, Any]:
        """Render search and filter controls"""
        st.subheader("Search & Filter")
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            search = st.text_input("Search conversations", placeholder="Filter by title, model, or content...")
        
        with col2:
            include_content = st.toggle("Search Content", value=False)
        
        with col3:
            limit = st.number_input("Max Results", min_value=10, max_value=500, value=50)
        
        return {"search": search, "include_content": include_content, "limit": limit}
    
    def _render_conversations_list(self, search_params: Dict[str, Any]):
        """Render the list of conversations"""
        try:
            conversations = self.conversation_service.get_conversations(
                search=search_params["search"],
                include_content=search_params["include_content"],
                limit=search_params["limit"]
            )
            
            if not conversations:
                self._render_no_conversations_message()
                return
            
            st.subheader(f"Found {len(conversations)} conversation(s)")
            
            for i, conv in enumerate(conversations):
                self._render_conversation_card(i, conv)
                
        except Exception as e:
            st.error(f"❌ Unable to load conversation history: {e}")
    
    def _render_no_conversations_message(self):
        """Render message when no conversations are found"""
        st.info("📝 No conversations found.")
        
        if st.button("🚀 Start New Conversation", use_container_width=True):
            self.state_manager.clear_conversation()
            self.state_manager.navigate_to("chat")
    
    def _render_conversation_card(self, index: int, conversation: Dict[str, Any]):
        """Render a single conversation card"""
        with st.container():
            col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
            
            with col1:
                title = conversation.get('title', 'Untitled Conversation')
                st.markdown(f"**{title}**")
                st.caption(f"📅 Created: {conversation.get('created_at', 'Unknown')}")
            
            with col2:
                st.metric("Model", conversation.get('model', 'Unknown')[:25])
            
            with col3:
                st.metric("Messages", int(conversation.get('messages', 0)))
            
            with col4:
                cost = float(conversation.get("cost", 0.0) or 0.0)
                st.metric("Cost", f"${cost:.4f}")
            
            self._render_conversation_actions(index, conversation)
            st.markdown("---")
    
    def _render_conversation_actions(self, index: int, conversation: Dict[str, Any]):
        """Render action buttons for a conversation"""
        action_col1, action_col2, action_col3 = st.columns(3)
        
        conv_id = conversation["conversation_id"]
        title = conversation.get("title", "Conversation")
        
        with action_col1:
            if st.button("📂 Load", key=f"load_{index}", use_container_width=True):
                self._load_conversation(conv_id, title)
        
        with action_col2:
            if st.button("🗑️ Delete", key=f"del_{index}", use_container_width=True):
                self._delete_conversation(conv_id, title)
        
        with action_col3:
            export_data = export_conversation_json(conv_id)
            st.download_button(
                "⬇️ Export",
                data=export_data,
                file_name=f"conversation_{conv_id}.json",
                mime="application/json",
                key=f"exp_{index}",
                use_container_width=True
            )
    
    def _load_conversation(self, conv_id: str, title: str):
        """Load a conversation from history"""
        try:
            messages = self.conversation_service.load_conversation_messages(conv_id)
            self.state_manager.load_conversation(conv_id, title, messages)
            st.success(f"✅ Loaded conversation: **{title}**")
        except Exception as e:
            st.error(f"❌ Failed to load conversation: {e}")
    
    def _delete_conversation(self, conv_id: str, title: str):
        """Delete a conversation with confirmation"""
        confirm_key = f"confirm_delete_{conv_id}"
        
        if confirm_key not in st.session_state:
            st.session_state[confirm_key] = False
        
        if not st.session_state[confirm_key]:
            st.session_state[confirm_key] = True
            st.warning(f"⚠️ Click delete again to confirm removal of: **{title}**")
        else:
            try:
                self.conversation_service.delete_conversation(conv_id)
                st.success(f"🗑️ Deleted conversation: **{title}**")
                del st.session_state[confirm_key]
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to delete conversation: {e}")
                del st.session_state[confirm_key]