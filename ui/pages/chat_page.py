# ui/pages/chat_page.py - Chat interface page
import streamlit as st
import os
import db
from .base_page import BasePage

class ChatPage(BasePage):
    """Chat page renderer - Main conversation interface"""
    
    def render(self):
        """Render the chat interface"""
        endpoint = self.state_manager.get_selected_endpoint()
        if not endpoint:
            self._render_endpoint_not_configured()
            return
        
        self._render_chat_history()
        self._handle_chat_input()
        
        if self.state_manager.should_generate_response():
            self._handle_assistant_response()
    
    def _render_endpoint_not_configured(self):
        """Render message when no endpoint is configured"""
        st.error("Model endpoint not configured. Please configure in Settings.")
        
        with st.expander("Configuration Help"):
            st.markdown("""
            **To configure model endpoints:**
            1. Go to **Settings** in the sidebar
            2. Select an available model endpoint
            3. Test the connection
            4. Return to Chat to start conversations
            """)
    
    def _render_chat_history(self):
        """Render the conversation history"""
        messages = self.state_manager.get_messages()
        
        if not messages:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; opacity: 0.7;">
                <h3>👋 Welcome to Databricks Intelligence</h3>
                <p>Start a conversation by typing your question below.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for message in messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
    
    def _handle_chat_input(self):
        """Handle user input from chat interface"""
        prompt = st.chat_input("Ask me anything...")
        
        if prompt and prompt.strip():
            self.state_manager.add_message("user", prompt)
            st.rerun()
    
    def _handle_assistant_response(self):
        """Handle assistant response generation"""
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            endpoint = self.state_manager.get_selected_endpoint()
            with message_placeholder:
                st.info(f"🤖 Processing with {endpoint}...")
            
            try:
                reply_text, tokens_in, tokens_out = self.model_service.generate_response(
                    endpoint, 
                    self.state_manager.get_messages()
                )
                
                message_placeholder.markdown(reply_text)
                self.state_manager.add_message("assistant", reply_text)
                
                self._log_conversation(tokens_in, tokens_out)
                
                if self.state_manager.is_new_conversation():
                    self._generate_conversation_title()
                
            except Exception as e:
                error_msg = f"Unable to process request: {str(e)}"
                message_placeholder.error(error_msg)
                self.state_manager.add_message("assistant", f"System error: {e}")
        
        st.rerun()
    
    def _log_conversation(self, tokens_in: int, tokens_out: int):
        """Log conversation to database"""
        try:
            self.conversation_service.log_conversation(
                self.state_manager.get_conversation_id(),
                self.state_manager.get_messages()[-2:],
                self.state_manager.get_selected_endpoint(),
                tokens_in,
                tokens_out
            )
        except Exception as e:
            st.error(f"Logging error: {e}")
    
    def _generate_conversation_title(self):
        """Generate an automatic title for the conversation"""
        try:
            messages = self.state_manager.get_messages()
            endpoint = self.state_manager.get_selected_endpoint()
            
            new_title = self.conversation_service.generate_title(endpoint, messages[:3])
            self.state_manager.set_chat_title(new_title)
            
            if os.getenv("DATABRICKS_WAREHOUSE_ID"):
                db.update_conversation_title(self.state_manager.get_conversation_id(), new_title)
                
        except Exception as e:
            st.error(f"Title generation failed: {e}")