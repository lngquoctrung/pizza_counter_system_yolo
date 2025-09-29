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
        # Create detection card
        st.markdown(f"""
        <div style="
            background: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            padding: 15px;
            margin: 8px 0;
            border-left: 3px solid #e74c3c;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        ">
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**🍕 Pizza Detection**")
            st.write(f"📹 {detection.get('filename', 'Unknown')}")
            st.write(f"🎯 Confidence: {detection.get('confidence', 0):.3f}")
            
        with col2:
            timestamp = detection.get('timestamp', datetime.now())
            st.write(f"🕒 {format_time_ago(timestamp)}")
            
            # Feedback buttons
            if st.button("👍", key=f"correct_{detection.get('_id')}"):
                submit_feedback(detection['_id'], 'correct')
            
            if st.button("👎", key=f"incorrect_{detection.get('_id')}"):
                submit_feedback(detection['_id'], 'incorrect')
        
        st.markdown("</div>", unsafe_allow_html=True)

def submit_feedback(detection_id, feedback_type):
    """Submit feedback for a detection"""
    counter = st.session_state.pizza_counter
    
    try:
        result = counter.submit_feedback(
            detection_id=str(detection_id),
            feedback_type=feedback_type
        )
        
        if result['success']:
            if feedback_type == 'correct':
                st.success("✅ Thank you! Feedback recorded as correct.")
            else:
                st.success("✅ Thank you! Feedback recorded as incorrect.")
            
            # Refresh the display
            st.rerun()
        else:
            st.error(f"Failed to submit feedback: {result.get('error')}")
            
    except Exception as e:
        st.error(f"Error submitting feedback: {str(e)}")

def display_detection_statistics():
    """Display detection statistics summary"""
    counter = st.session_state.pizza_counter
    
    try:
        # Get statistics for different time periods
        now = datetime.now()
        
        # Last hour
        last_hour = now - timedelta(hours=1)
        hour_count = counter.detections_collection.count_documents(
            {'timestamp': {'$gte': last_hour}}
        )
        
        # Last 24 hours
        last_day = now - timedelta(days=1)
        day_count = counter.detections_collection.count_documents(
            {'timestamp': {'$gte': last_day}}
        )
        
        # Last week
        last_week = now - timedelta(days=7)
        week_count = counter.detections_collection.count_documents(
            {'timestamp': {'$gte': last_week}}
        )
        
        # Display stats
        st.markdown("**📊 Detection Summary:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Last Hour", hour_count)
        
        with col2:
            st.metric("Last 24h", day_count)
        
        with col3:
            st.metric("Last Week", week_count)
            
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")

def display_confidence_trend():
    """Display confidence trend chart"""
    counter = st.session_state.pizza_counter
    
    try:
        # Get recent detections with confidence scores
        recent_detections = list(counter.detections_collection.find(
            {},
            {'confidence': 1, 'timestamp': 1}
        ).sort('timestamp', -1).limit(50))
        
        if len(recent_detections) < 2:
            st.info("Need more detections to show confidence trend")
            return
        
        # Prepare data
        timestamps = [d['timestamp'] for d in recent_detections]
        confidences = [d['confidence'] for d in recent_detections]
        
        # Create simple line chart
        import pandas as pd
        df = pd.DataFrame({
            'Time': timestamps,
            'Confidence': confidences
        })
        
        st.line_chart(df.set_index('Time'))
        
    except Exception as e:
        st.error(f"Error creating confidence trend: {str(e)}")

def display_feedback_summary():
    """Display feedback summary"""
    counter = st.session_state.pizza_counter
    
    try:
        # Get feedback counts
        total_feedback = counter.feedback_collection.count_documents({})
        positive_feedback = counter.feedback_collection.count_documents({'feedback_type': 'correct'})
        negative_feedback = counter.feedback_collection.count_documents({'feedback_type': 'incorrect'})
        
        if total_feedback == 0:
            st.info("No user feedback yet")
            return
        
        st.markdown("**👥 User Feedback:**")
        
        # Calculate percentages
        positive_pct = (positive_feedback / total_feedback) * 100
        negative_pct = (negative_feedback / total_feedback) * 100
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("👍 Positive", f"{positive_feedback} ({positive_pct:.1f}%)")
        
        with col2:
            st.metric("👎 Negative", f"{negative_feedback} ({negative_pct:.1f}%)")
            
    except Exception as e:
        st.error(f"Error loading feedback: {str(e)}")
