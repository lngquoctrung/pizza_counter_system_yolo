import streamlit as st
import time
from components.stats_cards import display_stats_cards
from components.video_upload import display_video_upload, display_processing_status, display_refresh_button
from components.recent_detections import display_recent_detections
from utils.helpers import format_time_ago

def show_dashboard():
    st.markdown("""
    <div style="background: #0e1117; border-radius: 15px; padding: 20px 30px; margin-bottom: 30px; border: 1px solid rgba(255, 255, 255, 0.1);">
        <h1 style="color: #ffffff; font-size: 2.2rem; font-weight: 700; margin-bottom: 0;">
            🍕 Pizza Detection Dashboard
        </h1>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        display_stats_cards()
        display_video_upload()
        display_processing_status()
    
    with col2:
        st.markdown("### 🔄 Data Controls")
        display_refresh_button()
        st.markdown("---")
        display_recent_detections()
