# ui/pages/analytics_page.py - Usage analytics page
import streamlit as st
import os
from typing import Dict, Any
from .base_page import BasePage

class AnalyticsPage(BasePage):
    """Analytics page renderer - Usage insights and metrics"""
    
    def render(self):
        """Render the analytics page"""
        if not self._is_logging_enabled():
            self._render_logging_disabled_message()
            return
        
        try:
            analytics_data = self.conversation_service.get_analytics_data()
            
            self._render_metrics_dashboard(analytics_data)
            st.markdown("---")
            self._render_usage_trends(analytics_data)
            self._render_model_breakdown(analytics_data)
            
        except Exception as e:
            st.error(f" Analytics service temporarily unavailable: {e}")
    
    def _is_logging_enabled(self) -> bool:
        """Check if SQL logging is enabled"""
        return bool(os.getenv("DATABRICKS_WAREHOUSE_ID"))
    
    def _render_logging_disabled_message(self):
        """Render message when logging is disabled"""
        st.info(" Data logging is disabled. Enable SQL logging to view usage analytics.")
        
        with st.expander("Analytics Benefits"):
            st.markdown("""
            **What You'll Get:**
            - Usage metrics and cost analysis
            - Trend analysis over time
            - Model performance comparison
            - User insights and recommendations
            """)
    
    def _render_metrics_dashboard(self, analytics_data: Dict[str, Any]):
        """Render the main metrics dashboard"""
        st.subheader("Platform Utilization Overview")
        
        totals = analytics_data.get("totals", {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            conversations = int(totals.get("conversations", 0) or 0)
            st.metric("Total Conversations", f"{conversations:,}")
        
        with col2:
            events = int(totals.get("events", 0) or 0)
            st.metric("API Requests", f"{events:,}")
        
        with col3:
            tokens_in = int(totals.get("tokens_in", 0) or 0)
            tokens_out = int(totals.get("tokens_out", 0) or 0)
            total_tokens = tokens_in + tokens_out
            st.metric("Tokens Processed", f"{total_tokens:,}")
        
        with col4:
            cost = float(totals.get('cost', 0.0) or 0.0)
            st.metric("Total Cost", f"${cost:.2f}")
    
    def _render_usage_trends(self, analytics_data: Dict[str, Any]):
        """Render usage trend visualizations"""
        by_day = analytics_data.get("by_day")
        
        if by_day is not None and not by_day.empty:
            st.subheader("Usage Trends Over Time")
            
            tab1, tab2 = st.tabs(["Cost Analysis", "Token Utilization"])
            
            with tab1:
                st.bar_chart(
                    by_day.set_index("day")["cost"], 
                    use_container_width=True,
                    height=400
                )
                st.caption("Daily cost breakdown showing platform utilization patterns")
            
            with tab2:
                st.line_chart(
                    by_day.set_index("day")["tokens"], 
                    use_container_width=True,
                    height=400
                )
                st.caption("Token consumption trends over time")
        else:
            st.info(" Insufficient data for trend analysis. Continue using the platform to generate insights.")
    
    def _render_model_breakdown(self, analytics_data: Dict[str, Any]):
        """Render model performance breakdown"""
        by_model = analytics_data.get("by_model")
        
        if by_model is not None and not by_model.empty:
            st.subheader("Model Performance Comparison")
            
            st.dataframe(
                by_model.rename(columns={
                    "model": "Model Endpoint", 
                    "tokens": "Total Tokens", 
                    "cost": "Cost (USD)", 
                    "events": "Requests"
                }),
                use_container_width=True,
                hide_index=True,
            )
            st.caption("Breakdown of usage and costs by model endpoint")
        else:
            st.info(" No model usage data available yet.")
