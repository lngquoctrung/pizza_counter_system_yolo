import streamlit as st
import time
from utils.helpers import display_metric_card, format_time_ago

def display_stats_cards():
    """Display system statistics cards"""
    counter = st.session_state.pizza_counter
    
    # Get comprehensive stats
    stats = counter.get_comprehensive_stats()
    
    if 'error' in stats:
        st.error(f"Error loading statistics: {stats['error']}")
        return
    
    # Create columns for stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(display_metric_card(
            "Total Videos",
            stats.get('total_videos', 0),
            color="#3498db"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(display_metric_card(
            "Pizza Detections",
            stats.get('total_detections', 0),
            delta=stats.get('recent_detections', 0),
            color="#e74c3c"
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(display_metric_card(
            "Model Accuracy",
            f"{stats.get('accuracy_percentage', 0):.1f}%",
            color="#2ecc71"
        ), unsafe_allow_html=True)
    
    with col4:
        processing_count = stats.get('currently_processing', 0)
        status_text = f"Processing ({processing_count})" if processing_count > 0 else "Ready"
        st.markdown(display_metric_card(
            "System Status",
            status_text,
            color="#f39c12" if processing_count > 0 else "#2ecc71"
        ), unsafe_allow_html=True)
    
    # Additional stats row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        completed_videos = stats.get('completed_videos', 0)
        st.metric(
            label="Completed Videos",
            value=completed_videos,
            delta=stats.get('recent_videos', 0)
        )
    
    with col2:
        avg_confidence = stats.get('avg_confidence', 0)
        st.metric(
            label="Avg Confidence",
            value=f"{avg_confidence:.3f}",
            delta=None
        )
    
    with col3:
        feedback_count = stats.get('feedback_count', 0)
        st.metric(
            label="User Feedback",
            value=feedback_count,
            delta=None
        )
    
    with col4:
        model_settings = stats.get('model_settings', {})
        confidence_threshold = model_settings.get('confidence_threshold', 0.5)
        st.metric(
            label="Confidence Threshold",
            value=f"{confidence_threshold:.2f}",
            delta=None
        )

def display_real_time_stats():
    """Display real-time updating statistics"""
    # Create a placeholder for dynamic updates
    stats_placeholder = st.empty()
    
    while True:
        with stats_placeholder.container():
            display_stats_cards()
        
        # Update every 5 seconds
        time.sleep(5)
