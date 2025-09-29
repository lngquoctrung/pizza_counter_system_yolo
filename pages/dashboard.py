import streamlit as st
import time
from components.stats_cards import display_stats_cards
from components.video_upload import display_video_upload, display_processing_status, display_refresh_button
from components.recent_detections import display_recent_detections
from utils.helpers import format_time_ago

def show_dashboard():
    st.markdown("""
    <style>
    .header-container {
        background: #0e1117 !important;
        border-radius: 15px;
        padding: 20px 30px;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    .header-title {
        color: #ffffff !important;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0;
    }
    
    .header-title i {
        color: #e74c3c !important;
        margin-right: 10px;
    }
    
    .metric-card {
        background: #0e1117 !important;
        color: #ffffff !important;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    .stButton > button {
        background: #3498db !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
    }
    
    [data-testid="metric-container"] {
        background: #0e1117 !important;
        border-radius: 10px !important;
        padding: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    [data-testid="metric-container"] > div {
        color: #ffffff !important;
    }
    
    [data-testid="metric-container"] > div > div {
        color: #ffffff !important;
    }
    
    div[data-testid="stMarkdownContainer"] {
        color: #ffffff !important;
    }
    
    div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
    }
    
    .stInfo {
        background: rgba(52, 152, 219, 0.2) !important;
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">
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
