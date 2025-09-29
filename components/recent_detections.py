import streamlit as st
from datetime import datetime, timedelta
from utils.helpers import format_time_ago

def display_recent_detections(limit=10):
    """Display recent pizza detections"""
    counter = st.session_state.pizza_counter
    
    try:
        # Get recent detections (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent_detections = list(counter.detections_collection.find(
            {'timestamp': {'$gte': yesterday}}
        ).sort('timestamp', -1).limit(limit))
        
        if not recent_detections:
            st.info("No recent detections in the last 24 hours")
            return
        
        st.markdown(f"**Latest {len(recent_detections)} Detections:**")
        
        for detection in recent_detections:
            display_detection_item(detection)
            
    except Exception as e:
        st.error(f"Error loading detections: {str(e)}")

def display_detection_item(detection):
    """Display individual detection item"""
    with st.container():
        detection_id = str(detection.get('_id', ''))
        
        # Check if feedback already exists in database
        counter = st.session_state.pizza_counter
        existing_feedback = None
        if counter.db_available:
            existing_feedback = counter.feedback_collection.find_one({'detection_id': detection_id})
        
        # Create columns for layout
        col1, col2 = st.columns([4, 1])
        
        with col1:
            # Detection info
            st.markdown(f"""
            🍕 **Pizza Detection** - File: {detection.get('filename', 'Unknown')} | 
            Confidence: {detection.get('confidence', 0):.2f} | 
            Frame: {detection.get('frame_count', 0)} | 
            {format_time_ago(detection.get('timestamp', datetime.now()))}
            """)
        
        with col2:
            # Feedback buttons or status
            if not existing_feedback:
                # Show feedback buttons inline
                col_correct, col_incorrect = st.columns(2)
                with col_correct:
                    if st.button("✅", key=f"correct_{detection_id}", help="Correct detection"):
                        submit_feedback(detection_id, "correct")
                        st.rerun()
                with col_incorrect:
                    if st.button("❌", key=f"incorrect_{detection_id}", help="Incorrect detection"):
                        submit_feedback(detection_id, "incorrect")
                        st.rerun()
            else:
                # Show feedback status
                feedback_type = existing_feedback.get('feedback_type', 'unknown')
                if feedback_type == "correct":
                    st.markdown("✅ **Correct**")
                else:
                    st.markdown("❌ **Incorrect**")
        
        # Divider
        st.markdown("---")

def submit_feedback(detection_id, feedback_type):
    """Submit feedback for detection - NO SUCCESS MESSAGE"""
    try:
        counter = st.session_state.pizza_counter
        result = counter.submit_feedback(detection_id, feedback_type)
        
        if not result.get('success', False):
            st.error(f"Failed to submit feedback: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        st.error(f"Error submitting feedback: {str(e)}")
