# ui/pages/chat_page.py - Chat interface page
import streamlit as st
import os
import db
from .base_page import BasePage
from services.file_parser_service import parse_file  # ⬅️ New import
from services.token_truncation import truncate_to_model_context


class ChatPage(BasePage):
    """Chat page renderer - Main conversation interface"""
    
    def render(self):
        endpoint = self.state_manager.get_selected_endpoint()
        if not endpoint:
            self._render_endpoint_not_configured()
            return

        self._render_file_uploader()  # ⬅️ New
        self._render_chat_history()
        self._handle_chat_input()

        if self.state_manager.should_generate_response():
            self._handle_assistant_response()

    def _render_endpoint_not_configured(self):
        st.error("Model endpoint not configured. Please configure in Settings.")
        with st.expander("Configuration Help"):
            st.markdown("""
            **To configure model endpoints:**
            1. Go to **Settings** in the sidebar
            2. Select an available model endpoint
            3. Test the connection
            4. Return to Chat to start conversations
            """)

    # def _render_file_uploader(self):
    #     file = st.file_uploader("Upload a document",    type=["pdf", "csv", "xlsx", "txt", "py", "md"])

    #     if file:
    #         file_key = f"uploaded_{file.name}"
    #         if not st.session_state.get(file_key):
    #             with st.spinner("Parsing document..."):
    #                 extracted_text = parse_file(file)

    #                 if extracted_text:
    #                     st.session_state["file_context"] = extracted_text  # ⬅️ Store only, don't inject
    #                     st.session_state[file_key] = True
    #                     st.success("File uploaded successfully.")
    #                     st.rerun()
    #         elif "file_context" in st.session_state:
    #             st.success("File uploaded.")
    #             with st.expander("Preview file content"):
    #                 st.text_area("Document Content", st.session_state["file_context"], height=200)
    def _render_file_uploader(self):
        file = st.file_uploader("Upload a document", type=["pdf", "csv", "xlsx", "txt", "py", "md"])

        if file:
            file_key = f"uploaded_{file.name}"
            if not st.session_state.get(file_key):
                with st.spinner("Parsing document..."):
                    model_key = self.state_manager.get_model_key().lower()
                    extracted_text, was_truncated = parse_file(file, model_key)

                    if extracted_text:
                        st.session_state["file_context"] = extracted_text
                        st.session_state[file_key] = True
                        st.success("File uploaded successfully.")

                        if was_truncated:
                            st.warning("⚠️ The file content was truncated to fit the model’s input limit.")

                        st.rerun()

            elif "file_context" in st.session_state:
                st.success("File uploaded.")
                with st.expander("Preview file content"):
                    st.text_area("Document Content", st.session_state["file_context"], height=200)


    def _render_chat_history(self):
        messages = self.state_manager.get_messages()
        if not messages:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; opacity: 0.7;">
                <h3>Welcome to Databricks Intelligence</h3>
                <p>Start a conversation by typing your question below.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for message in messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        # st.markdown(
        #     """
        #     <div style="text-align: center; margin-top: 3rem; opacity: 0.6;">
        #         <img src="https://www.databricks.com/sites/default/files/2023-08/databricks-default.png"
        #             alt="Databricks Logo"
        #             style="height: 30px; margin-bottom: 0.5rem;" />
        #         <div style="font-size: 0.9rem;">Powered by Databricks</div>
        #     </div>
        #     """,
        #     unsafe_allow_html=True
        # )


    def _handle_chat_input(self):
        prompt = st.chat_input("Ask me anything...")
        if prompt and prompt.strip():
            if "file_context" in st.session_state:
                full_prompt = f"{st.session_state['file_context']}\n\nUser: {prompt}"
            else:
                full_prompt = prompt

            self.state_manager.add_message("user", full_prompt)
            st.rerun()


    def _handle_assistant_response(self):
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            endpoint = self.state_manager.get_selected_endpoint()
            with message_placeholder:
                st.info(f"Processing with {endpoint}...")

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
                message_placeholder.error(f"Unable to process request: {e}")
                self.state_manager.add_message("assistant", f"System error: {e}")

        st.rerun()

    def _log_conversation(self, tokens_in: int, tokens_out: int):
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
        try:
            messages = self.state_manager.get_messages()
            endpoint = self.state_manager.get_selected_endpoint()
            new_title = self.conversation_service.generate_title(endpoint, messages[:3])
            self.state_manager.set_chat_title(new_title)
            if os.getenv("DATABRICKS_WAREHOUSE_ID"):
                db.update_conversation_title(self.state_manager.get_conversation_id(), new_title)
        except Exception as e:
            st.error(f"Title generation failed: {e}")
