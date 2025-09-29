import streamlit as st
import time
from components.stats_cards import display_stats_cards
from components.video_upload import display_video_upload, display_processing_status, display_refresh_button
from components.recent_detections import display_recent_detections
from utils.helpers import format_time_ago

def show_dashboard():
    """Main dashboard page"""
    st.markdown("""
    <style>
    .header-container {
        background: rgba(30, 30, 30, 0.95) !important;
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px 30px;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
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
        background: rgba(30, 30, 30, 0.9) !important;
        color: #ffffff !important;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4) !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #3498db, #2980b9) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: bold !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(52, 152, 219, 0.3) !important;
    }
    
    .stFileUploader {
        background: rgba(30, 30, 30, 0.8) !important;
        border-radius: 10px !important;
        border: 2px dashed #3498db !important;
    }
    
    .stProgress > div > div {
        background: linear-gradient(90deg, #3498db, #2980b9) !important;
    }
    
    div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
    }
    
    .stInfo {
        background: rgba(52, 152, 219, 0.2) !important;
        border: 1px solid #3498db !important;
        color: #ffffff !important;
    }
    
    .stSuccess {
        background: rgba(46, 204, 113, 0.2) !important;
        border: 1px solid #2ecc71 !important;
        color: #ffffff !important;
    }
    
    .stError {
        background: rgba(231, 76, 60, 0.2) !important;
        border: 1px solid #e74c3c !important;
        color: #ffffff !important;
    }
    
    [data-testid="metric-container"] {
        background: rgba(30, 30, 30, 0.8) !important;
        border-radius: 10px !important;
        padding: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    [data-testid="metric-container"] > div {
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">
            <i class="fas fa-pizza-slice"></i>
            Pizza Detection Dashboard
        </h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content layout
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
