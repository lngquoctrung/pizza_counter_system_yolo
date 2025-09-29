import streamlit as st
import cv2
import numpy as np
from PIL import Image
import threading
import time
import os
from utils.helpers import convert_cv2_to_pil, convert_pil_to_bytes

def display_video_stream_modal(video_filename):
    """Display video streaming modal with real-time detection"""
    
    st.markdown(f"## 🎥 Live Detection Stream: {video_filename}")
    
    # Stream controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("▶️ Start Stream", key="start_stream"):
            start_video_stream(video_filename)
    
    with col2:
        if st.button("⏸️ Pause Stream", key="pause_stream"):
            pause_video_stream()
    
    with col3:
        if st.button("⏹️ Stop Stream", key="stop_stream"):
            stop_video_stream()
    
    with col4:
        if st.button("❌ Close", key="close_stream"):
            close_stream_modal()
    
    # Stream display area
    stream_container = st.container()
    
    with stream_container:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Video stream placeholder
            stream_placeholder = st.empty()
            
            # Check if stream is active
            if 'stream_active' in st.session_state and st.session_state.stream_active:
                display_stream_frame(stream_placeholder, video_filename)
            else:
                with stream_placeholder:
                    st.info("🎬 Click 'Start Stream' to begin real-time detection")
        
        with col2:
            display_stream_stats()
            display_detection_controls()

def start_video_stream(video_filename):
    """Start video streaming with detection"""
    try:
        video_path = f"./videos/{video_filename}"
        
        if not os.path.exists(video_path):
            st.error(f"Video file not found: {video_filename}")
            return
        
        # Initialize stream state
        st.session_state.stream_active = True
        st.session_state.stream_paused = False
        st.session_state.current_video = video_filename
        st.session_state.detection_count = 0
        st.session_state.current_frame = 0
        
        st.success("✅ Stream started!")
        
    except Exception as e:
        st.error(f"❌ Error starting stream: {str(e)}")

def pause_video_stream():
    """Pause video stream"""
    if 'stream_active' in st.session_state:
        st.session_state.stream_paused = not st.session_state.get('stream_paused', False)
        
        if st.session_state.stream_paused:
            st.info("⏸️ Stream paused")
        else:
            st.success("▶️ Stream resumed")

def stop_video_stream():
    """Stop video stream"""
    st.session_state.stream_active = False
    st.session_state.stream_paused = False
    st.info("⏹️ Stream stopped")

def close_stream_modal():
    """Close streaming modal"""
    stop_video_stream()
    
    # Clear stream-related session state
    keys_to_clear = ['stream_video', 'stream_active', 'stream_paused', 
                     'current_video', 'detection_count', 'current_frame']
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.rerun()

def display_stream_frame(placeholder, video_filename):
    """Display current stream frame with detections"""
    try:
        counter = st.session_state.pizza_counter
        video_path = f"./videos/{video_filename}"
        
        # Open video capture
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            st.error("Could not open video file")
            return
        
        # Set frame position if resuming
        if 'current_frame' in st.session_state:
            cap.set(cv2.CAP_PROP_POS_FRAMES, st.session_state.current_frame)
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            # Process frame for detection
            result = counter.process_frame_for_stream(frame)
            
            if 'error' in result:
                st.error(f"Detection error: {result['error']}")
                return
            
            # Get processed frame with annotations
            processed_frame = result['frame']
            detections = result['detections']
            
            # Convert to PIL and display
            pil_image = convert_cv2_to_pil(processed_frame)
            
            with placeholder:
                st.image(pil_image, caption=f"Frame: {st.session_state.get('current_frame', 0)}")
            
            # Update detection count
            if detections:
                st.session_state.detection_count = st.session_state.get('detection_count', 0) + len(detections)
            
            # Update frame counter
            st.session_state.current_frame = st.session_state.get('current_frame', 0) + 1
        
        else:
            st.info("End of video reached")
            stop_video_stream()
            
    except Exception as e:
        st.error(f"Stream error: {str(e)}")

def display_stream_stats():
    """Display real-time stream statistics"""
    st.markdown("### 📊 Stream Stats")
    
    current_frame = st.session_state.get('current_frame', 0)
    detection_count = st.session_state.get('detection_count', 0)
    
    st.metric("Current Frame", current_frame)
    st.metric("Pizzas Detected", detection_count)
    
    # Stream status
    if st.session_state.get('stream_active', False):
        if st.session_state.get('stream_paused', False):
            st.warning("⏸️ Paused")
        else:
            st.success("🔴 Live")
    else:
        st.info("⏹️ Stopped")

def display_detection_controls():
    """Display detection control settings"""
    st.markdown("### ⚙️ Detection Settings")
    
    counter = st.session_state.pizza_counter
    current_settings = counter.get_model_settings()
    
    # Confidence threshold slider
    confidence_threshold = st.slider(
        "Confidence Threshold",
        min_value=0.1,
        max_value=1.0,
        value=current_settings.get('confidence_threshold', 0.5),
        step=0.05,
        key="stream_confidence"
    )
    
    # Update threshold if changed
    if confidence_threshold != current_settings.get('confidence_threshold', 0.5):
        counter.update_confidence_threshold(confidence_threshold)
    
    # Frame skip setting
    frame_skip = st.selectbox(
        "Frame Skip",
        [1, 2, 3, 5, 10],
        index=2,
        help="Process every Nth frame for better performance"
    )
    
    # Detection visualization options
    st.checkbox("Show Bounding Boxes", value=True, key="show_boxes")
    st.checkbox("Show Confidence Scores", value=True, key="show_confidence")
    st.checkbox("Show Detection Count", value=True, key="show_count")

@st.cache_data
def get_stream_thumbnail(video_path):
    """Get thumbnail for stream preview"""
    try:
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            return convert_cv2_to_pil(frame)
        return None
    except:
        return None

def display_stream_history():
    """Display streaming session history"""
    st.markdown("### 📚 Stream History")
