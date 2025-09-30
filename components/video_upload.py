import streamlit as st
import os
import threading
import time
from utils.helpers import validate_video_file, save_uploaded_file
from utils.helpers import format_file_size, create_progress_bar_html

def display_video_upload():
    counter = st.session_state.pizza_counter
    is_processing = any(
        status.get("status") == "processing" 
        for status in counter.processing_videos.values()
    )
    
    active_processing = any(
        key.startswith("processing_") and st.session_state[key].get("active", False)
        for key in st.session_state.keys()
        if key.startswith("processing_")
    )
    
    if is_processing or active_processing:
        st.markdown("## 🔄 Video Processing in Progress")
        display_active_processing_status()
        check_and_display_completion()
        return
    
    st.markdown("## 📤 Upload Video for Pizza Detection")
    
    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv'],
        help="Supported formats: MP4, AVI, MOV, MKV, WEBM, FLV",
        key="video_uploader"
    )
    
    if uploaded_file is not None:
        is_valid, message = validate_video_file(uploaded_file)
        if not is_valid:
            st.error(message)
            return
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"📄 **Filename:** {uploaded_file.name}")
        with col2:
            st.write(f"📊 **Size:** {format_file_size(uploaded_file.size)}")
        with col3:
            st.write(f"📋 **Type:** {uploaded_file.type}")
        
        if st.button("🚀 Upload and Process", key="upload_process_btn", type="primary"):
            process_uploaded_video(uploaded_file)

def display_active_processing_status():
    """Display processing status with auto-updating progress"""
    # Ensure current_processing exists
    if 'current_processing' not in st.session_state:
        st.session_state.current_processing = {}
    
    # Check current tab
    current_tab = st.session_state.get('current_tab', 'Dashboard')
    counter = st.session_state.pizza_counter
    
    for key in st.session_state.keys():
        if key.startswith("processing_") and st.session_state[key].get("active", False):
            status = st.session_state[key]
            filename = status.get("filename", "Unknown")
            
            # READ FROM SHARED_PROGRESS (thread-safe)
            shared_progress = status.get("shared_progress", {})
            progress_lock = status.get("lock")
            
            if progress_lock:
                try:
                    with progress_lock:
                        progress = shared_progress.get("value", 0)
                        message = shared_progress.get("message", "Processing...")
                        check_status = shared_progress.get("status")
                except:
                    # Fallback if lock fails
                    progress = counter.processing_videos.get(filename, {}).get("progress", 0)
                    message = "Processing..."
                    check_status = None
            else:
                # Fallback to counter's processing_videos
                progress = counter.processing_videos.get(filename, {}).get("progress", 0)
                message = status.get("message", "Processing...")
                check_status = None
            
            # Check if completed
            if check_status in ["completed", "error"]:
                st.session_state[key]["active"] = False
                st.session_state[key]["status"] = check_status
                st.session_state[key]["message"] = message
                if check_status == "completed":
                    st.session_state[key]["result"] = shared_progress.get("result", {})
                st.rerun()
                return
            
            st.markdown(f"### 📹 {filename}")
            
            # Create progress bar
            progress_value = min(max(progress, 0), 100) / 100.0
            st.progress(progress_value)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"🔄 {message}")
            with col2:
                st.write(f"**{progress:.1f}%**")
            
            # Only auto-refresh if on Dashboard
            if current_tab == "Dashboard":
                time.sleep(2)
                st.rerun()
            else:
                st.info("💡 Processing continues in background. Return to Dashboard to see live updates.")
            return


def check_and_display_completion():
    for key in list(st.session_state.keys()):
        if key.startswith("processing_") and not st.session_state[key].get("active", True):
            status = st.session_state[key]
            
            if status.get("status") == "completed":
                filename = status.get("filename", "Unknown")
                result = status.get("result", {})
                
                st.success(f"✅ Processing completed for **{filename}**!")
                
                if result:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("🍕 Pizza Count", result.get('pizza_count', 0))
                    with col2:
                        st.metric("🎞️ Total Frames", result.get('total_frames', 0))
                    with col3:
                        st.metric("🔍 Detections", len(result.get('detections', [])))
                
                if st.button("🔄 Process Another Video", key="reset_upload"):
                    del st.session_state[key]
                    if filename in st.session_state.current_processing:
                        del st.session_state.current_processing[filename]
                    st.rerun()
                
                return True
            
            elif status.get("status") == "error":
                filename = status.get("filename", "Unknown")
                error_msg = status.get("message", "Processing failed")
                
                st.error(f"❌ Processing failed for **{filename}**: {error_msg}")
                
                if st.button("🔄 Try Again", key="retry_upload"):
                    del st.session_state[key]
                    if filename in st.session_state.current_processing:
                        del st.session_state.current_processing[filename]
                    st.rerun()
                
                return True
    
    return False

def process_uploaded_video(uploaded_file):
    counter = st.session_state.pizza_counter
    
    try:
        with st.spinner("💾 Saving uploaded file..."):
            file_path, filename = save_uploaded_file(uploaded_file)
            st.success(f"✅ File saved: {filename}")
        
        processing_key = f"processing_{filename}"
        
        # Khởi tạo shared progress storage (thread-safe)
        import threading
        progress_lock = threading.Lock()
        shared_progress = {"value": 0, "message": "Starting..."}
        
        st.session_state[processing_key] = {
            "active": True,
            "progress": 0,
            "filename": filename,
            "status": "processing",
            "message": "Starting video processing...",
            "start_time": time.time(),
            "shared_progress": shared_progress,
            "lock": progress_lock
        }
        
        # Initialize current_processing
        st.session_state.current_processing[filename] = 0
        
        counter.processing_videos[filename] = {
            "status": "processing",
            "progress": 0,
            "start_time": time.time()
        }
        
        def background_process():
            try:
                def progress_callback(progress):
                    # Thread-safe update
                    with progress_lock:
                        shared_progress["value"] = progress
                        shared_progress["message"] = f"Processing: {progress:.1f}%"
                    
                    # Update counter's processing_videos (thread-safe)
                    if filename in counter.processing_videos:
                        counter.processing_videos[filename]["progress"] = progress
                    
                    print(f"Progress: {progress:.1f}%")
                
                result = counter.process_video(file_path, filename, progress_callback=progress_callback)
                
                final_status = "completed" if result['success'] else "error"
                final_message = f"Found {result['pizza_count']} pizzas" if result['success'] else result.get('error', 'Processing failed')
                
                # Update shared progress
                with progress_lock:
                    shared_progress["value"] = 100
                    shared_progress["message"] = final_message
                    shared_progress["status"] = final_status
                    shared_progress["result"] = result
                
                # Mark as completed
                counter.processing_videos[filename].update({
                    "status": final_status,
                    "progress": 100,
                    "result": result
                })
                
            except Exception as e:
                error_message = f"Processing error: {str(e)}"
                print(error_message)
                
                with progress_lock:
                    shared_progress["status"] = "error"
                    shared_progress["message"] = error_message
                
                if filename in counter.processing_videos:
                    counter.processing_videos[filename].update({
                        "status": "error",
                        "message": error_message
                    })
        
        processing_thread = threading.Thread(target=background_process)
        processing_thread.daemon = True
        processing_thread.start()
        
        time.sleep(0.5)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Upload error: {str(e)}")

def display_processing_status():
    """Display processing status for active videos"""
    # Ensure current_processing exists
    if 'current_processing' not in st.session_state:
        st.session_state.current_processing = {}
    
    counter = st.session_state.pizza_counter
    has_active_processing = False
    
    # Check for active processing
    for key in st.session_state.keys():
        if key.startswith("processing_") and st.session_state[key].get("active", False):
            has_active_processing = True
            break
    
    if not has_active_processing:
        for filename, status in counter.processing_videos.items():
            if status.get("status") == "processing":
                has_active_processing = True
                break
    
    if not has_active_processing:
        return
    
    st.markdown("### 🔄 Active Processing")
    
    for key in st.session_state.keys():
        if key.startswith("processing_") and st.session_state[key].get("active", False):
            status = st.session_state[key]
            filename = status.get("filename", "Unknown")
            
            # READ FROM SHARED_PROGRESS
            shared_progress = status.get("shared_progress", {})
            progress_lock = status.get("lock")
            
            if progress_lock:
                try:
                    with progress_lock:
                        progress = shared_progress.get("value", 0)
                except:
                    progress = counter.processing_videos.get(filename, {}).get("progress", 0)
            else:
                progress = counter.processing_videos.get(filename, {}).get("progress", 0)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📹 {filename}")
                progress_value = min(max(progress, 0), 100) / 100.0
                st.progress(progress_value)
            with col2:
                st.write(f"{progress:.1f}%")

def display_refresh_button():
    if st.button("🔄 Refresh Data", key="refresh_data_btn"):
        if 'stats_cache' in st.session_state:
            del st.session_state['stats_cache']
        
        counter = st.session_state.pizza_counter
        if hasattr(counter, '_cached_stats'):
            delattr(counter, '_cached_stats')
        
        st.success("✅ Data refreshed!")
        time.sleep(1)
        st.rerun()
