import streamlit as st
import os
import threading
import time
from utils.helpers import validate_video_file, save_uploaded_file, show_toast
from utils.helpers import format_file_size, create_progress_bar_html

def display_video_upload():
    """Display video upload interface"""
    
    st.markdown("#### 📤 Upload Video for Pizza Detection")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv'],
        help="Supported formats: MP4, AVI, MOV, MKV, WEBM, FLV"
    )
    
    if uploaded_file is not None:
        # Validate file
        is_valid, message = validate_video_file(uploaded_file)
        
        if not is_valid:
            st.error(message)
            return
        
        # Display file info
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**Filename:** {uploaded_file.name}")
        with col2:
            st.write(f"**Size:** {format_file_size(uploaded_file.size)}")
        with col3:
            st.write(f"**Type:** {uploaded_file.type}")
        
        # Upload and process button
        if st.button("🚀 Upload and Process", key="upload_process_btn"):
            process_uploaded_video_sync(uploaded_file)

def process_uploaded_video_sync(uploaded_file):
    """Process uploaded video ĐỒNG BỘ (không dùng thread)"""
    counter = st.session_state.pizza_counter
    
    try:
        # Save uploaded file
        with st.spinner("Saving uploaded file..."):
            file_path, filename = save_uploaded_file(uploaded_file)
        
        st.success(f"✅ File saved: {filename}")
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Progress callback function
        def progress_callback(progress):
            progress_bar.progress(progress / 100)
            status_text.text(f"Processing: {progress:.1f}%")
        
        # Process video ĐỒNG BỘ
        with st.spinner("🔄 Processing video..."):
            status_text.info("🔄 Starting video processing...")
            
            result = counter.process_video(
                file_path, 
                filename, 
                progress_callback=progress_callback
            )
        
        # Clear progress elements
        progress_bar.empty()
        status_text.empty()
        
        if result['success']:
            st.success(f"✅ Processing complete! Found {result['pizza_count']} pizzas")
            
            # Update session state
            if 'last_upload' not in st.session_state:
                st.session_state.last_upload = {}
            
            st.session_state.last_upload = {
                'filename': filename,
                'pizza_count': result['pizza_count'],
                'status': 'completed'
            }
            
            # Show results
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Pizza Count", result['pizza_count'])
            with col2:
                st.metric("Total Frames", result['total_frames'])
            with col3:
                st.metric("Detections", len(result['detections']))
                
        else:
            st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        st.error(f"❌ Upload error: {str(e)}")

def process_uploaded_video_async(uploaded_file):
    counter = st.session_state.pizza_counter
    
    try:
        # Save uploaded file
        with st.spinner("Saving uploaded file..."):
            file_path, filename = save_uploaded_file(uploaded_file)
        
        st.success(f"✅ File saved: {filename}")
        
        # Initialize processing state
        st.session_state.processing_status = {
            'active': True,
            'progress': 0,
            'filename': filename,
            'status': 'processing',
            'message': 'Starting...'
        }
        
        # Start background processing
        def background_process():
            try:
                def progress_callback(progress):
                    # Update session state instead of UI directly
                    st.session_state.processing_status['progress'] = progress
                    st.session_state.processing_status['message'] = f"Processing: {progress:.1f}%"
                
                result = counter.process_video(
                    file_path, 
                    filename, 
                    progress_callback=progress_callback
                )
                
                # Update final result
                st.session_state.processing_status.update({
                    'active': False,
                    'progress': 100,
                    'result': result,
                    'status': 'completed' if result['success'] else 'error',
                    'message': f"Found {result['pizza_count']} pizzas" if result['success'] else result.get('error', 'Unknown error')
                })
                
            except Exception as e:
                st.session_state.processing_status.update({
                    'active': False,
                    'status': 'error',
                    'message': f"Processing error: {str(e)}"
                })
        
        # Start thread
        processing_thread = threading.Thread(target=background_process)
        processing_thread.daemon = True
        processing_thread.start()
        
        st.info("🔄 Processing started in background. The page will refresh automatically when done.")
        
    except Exception as e:
        st.error(f"❌ Upload error: {str(e)}")

def display_processing_status():
    """Display real-time processing status"""
    if 'processing_status' not in st.session_state:
        return
    
    status = st.session_state.processing_status
    
    if status['active']:
        # Show progress
        progress = status.get('progress', 0)
        st.progress(progress / 100)
        st.info(status.get('message', 'Processing...'))
        
        # Auto refresh every 2 seconds
        time.sleep(2)
        st.rerun()
        
    else:
        # Show final result
        if status['status'] == 'completed':
            result = status.get('result', {})
            st.success(status.get('message', 'Processing completed!'))
            
            # Show metrics
            if 'result' in status and status['result']['success']:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Pizza Count", result['pizza_count'])
                with col2:
                    st.metric("Total Frames", result['total_frames'])
                with col3:
                    st.metric("Detections", len(result['detections']))
        
        elif status['status'] == 'error':
            st.error(status.get('message', 'Processing failed'))
        
        # Clear processing status
        del st.session_state.processing_status