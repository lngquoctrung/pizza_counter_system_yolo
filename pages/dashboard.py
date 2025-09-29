import streamlit as st
import time
from components.stats_cards import display_stats_cards
from components.video_upload import display_video_upload, display_processing_status, display_refresh_button
from components.recent_detections import display_recent_detections
from utils.helpers import format_time_ago

def show_dashboard():
    """Main dashboard page"""
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
        background: rgba(0, 0, 0, 0.95);
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
