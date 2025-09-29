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
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            min-height: 100vh;
        }
        
        /* Header Styles */
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
        
        /* Force Streamlit elements to dark theme */
        .stMarkdown, .stText, .stMetric {
            color: #ffffff !important;
        }
        
        /* Button styling */
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
        
        /* File uploader */
        .stFileUploader {
            background: rgba(30, 30, 30, 0.8) !important;
            border-radius: 10px !important;
            border: 2px dashed #3498db !important;
        }
        
        /* Progress bar */
        .stProgress > div > div {
            background: linear-gradient(90deg, #3498db, #2980b9) !important;
        }
        
        /* Text color override */
        div[data-testid="stMarkdownContainer"] p {
            color: #ffffff !important;
        }
        
        /* Info boxes */
        .stInfo {
            background: rgba(52, 152, 219, 0.2) !important;
            border: 1px solid #3498db !important;
            color: #ffffff !important;
        }
        
        /* Success boxes */
        .stSuccess {
            background: rgba(46, 204, 113, 0.2) !important;
            border: 1px solid #2ecc71 !important;
            color: #ffffff !important;
        }
        
        /* Error boxes */
        .stError {
            background: rgba(231, 76, 60, 0.2) !important;
            border: 1px solid #e74c3c !important;
            color: #ffffff !important;
        }
        
        /* Override any white backgrounds */
        [data-testid="stSidebar"] {
            background: rgba(30, 30, 30, 0.95) !important;
        }
        
        /* Main content area */
        .main > div {
            padding-top: 2rem;
            background: transparent !important;
        }
        
        /* Force metric values to be visible */
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
        # System statistics
        display_stats_cards()
        
        # Video upload section
        display_video_upload()
        
        # Active processing status (if any)
        display_processing_status()
    
    with col2:
        # Refresh button - separate from upload section
        st.markdown("### 🔄 Data Controls")
        display_refresh_button()
        
        st.markdown("---")
        
        # Recent detections
        display_recent_detections()
    
    # Custom CSS for better spacing
    st.markdown("""
    <style>
    .main > div {
        padding-top: 1rem;
    }
    .header-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px 30px;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .header-title {
        color: #2c3e50;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0;
    }
    .header-title i {
        color: #e74c3c;
        margin-right: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
