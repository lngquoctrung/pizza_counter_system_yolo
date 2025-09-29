import streamlit as st
import time
from components.stats_cards import display_stats_cards
from components.video_upload import display_video_upload, display_processing_status
from components.recent_detections import display_recent_detections
from utils.helpers import format_time_ago

def show_dashboard():
    st.markdown("""
    <div class="header">
        <h1><i class="fas fa-pizza-slice"></i> Pizza Detection Dashboard</h1>
        <div class="header-stats" id="header-stats"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh placeholder
    refresh_placeholder = st.empty()
    
    # Main layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📊 System Statistics")
        display_stats_cards()
        
        st.markdown("### 📤 Upload Video")
        display_video_upload()
        
        # Hiển thị trạng thái processing nếu có
        display_processing_status()
        
    with col2:
        st.markdown("### 🔍 Recent Detections")
        display_recent_detections()
        
        st.markdown("### ⚙️ Quick Settings")
        display_quick_settings()
    
    # Auto-refresh mechanism
    if st.button("🔄 Refresh Data", key="refresh_dashboard"):
        st.rerun()
    
    # Periodic auto-refresh (every 30 seconds)
    time.sleep(30)
    st.rerun()

def display_quick_settings():
    counter = st.session_state.pizza_counter
    
    # Confidence threshold slider
    current_threshold = counter.get_model_settings().get('confidence_threshold', 0.5)
    
    new_threshold = st.slider(
        "Confidence Threshold",
        min_value=0.1,
        max_value=1.0,
        value=current_threshold,
        step=0.05,
        key="confidence_slider"
    )
    
    if new_threshold != current_threshold:
        counter.update_confidence_threshold(new_threshold)
        st.success(f"Threshold updated to {new_threshold}")
        
    # Model accuracy display
    stats = counter.get_comprehensive_stats()
    accuracy = stats.get('accuracy_percentage', 0)
    
    st.metric(
        label="Model Accuracy",
        value=f"{accuracy}%",
        delta=None
    )
    
    # Processing status
    processing_videos = stats.get('processing_videos', 0)
    if processing_videos > 0:
        st.info(f"⏳ {processing_videos} videos currently processing...")
