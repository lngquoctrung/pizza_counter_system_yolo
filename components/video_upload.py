import streamlit as st
import os
import threading
import time
from utils.helpers import validate_video_file, save_uploaded_file
from utils.helpers import format_file_size, create_progress_bar_html

def display_video_upload():
    """Display video upload interface with improved UX"""
    
    # Check if currently processing any video
    counter = st.session_state.pizza_counter
    is_processing = any(
        status.get("status") == "processing" 
        for status in counter.processing_videos.values()
    )
    
    # Also check session state for active processing
    active_processing = any(
        key.startswith("processing_") and st.session_state[key].get("active", False)
        for key in st.session_state.keys()
        if key.startswith("processing_")
    )
    
    # If processing, show only progress bar and processing status
    if is_processing or active_processing:
        st.markdown("## 🔄 Video Processing in Progress")
        
        # Display processing status
        display_active_processing_status()
        
        # Show completion message if processing is done
        check_and_display_completion()
        
        return
    
    # Normal upload interface when not processing
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
        
        # File info display
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"📄 **Filename:** {uploaded_file.name}")
        with col2:
            st.write(f"📊 **Size:** {format_file_size(uploaded_file.size)}")
        with col3:
            st.write(f"📋 **Type:** {uploaded_file.type}")
        
        # Upload and Process button
        if st.button("🚀 Upload and Process", key="upload_process_btn", type="primary"):
            process_uploaded_video_enhanced(uploaded_file)

def display_active_processing_status():
    """Display current processing status"""
    counter = st.session_state.pizza_counter
    
    # Check session state for active processing
    for key in st.session_state.keys():
        if key.startswith("processing_") and st.session_state[key].get("active", False):
            status = st.session_state[key]
            filename = status.get("filename", "Unknown")
            progress = status.get("progress", 0)
            message = status.get("message", "Processing...")
            
            st.markdown(f"### 📹 {filename}")
            
            # Progress bar
            progress_bar = st.progress(progress / 100)
            
            # Progress text
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"🔄 {message}")
            with col2:
                st.write(f"**{progress:.1f}%**")
            
            # Auto refresh every 2 seconds
            time.sleep(2)
            st.rerun()
            return
    
    # Fallback: check counter processing videos
    for filename, status in counter.processing_videos.items():
        if status.get("status") == "processing":
            progress = status.get("progress", 0)
            
            st.markdown(f"### 📹 {filename}")
            st.progress(progress / 100)
            st.info(f"🔄 Processing... {progress:.1f}%")
            
            # Auto refresh
            time.sleep(2)
            st.rerun()
            return

def check_and_display_completion():
    """Check and display completion status"""
    counter = st.session_state.pizza_counter
    
    # Check for completed processing in session state
    for key in list(st.session_state.keys()):
        if key.startswith("processing_") and not st.session_state[key].get("active", True):
            status = st.session_state[key]
            
            if status.get("status") == "completed":
                filename = status.get("filename", "Unknown")
                result = status.get("result", {})
                
                # Show completion message
                st.success(f"✅ Processing completed for **{filename}**!")
                
                # Show results
                if result:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("🍕 Pizza Count", result.get('pizza_count', 0))
                    with col2:
                        st.metric("🎞️ Total Frames", result.get('total_frames', 0))
                    with col3:
                        st.metric("🔍 Detections", len(result.get('detections', [])))
                
                # Show reset button
                if st.button("🔄 Process Another Video", key="reset_upload"):
                    # Clear processing state
                    del st.session_state[key]
                    st.rerun()
                
                return True
            
            elif status.get("status") == "error":
                filename = status.get("filename", "Unknown")
                error_msg = status.get("message", "Processing failed")
                
                st.error(f"❌ Processing failed for **{filename}**: {error_msg}")
                
                # Show retry button
                if st.button("🔄 Try Again", key="retry_upload"):
                    # Clear error state
                    del st.session_state[key]
                    st.rerun()
                
                return True
    
    return False

def process_uploaded_video_enhanced(uploaded_file):
    """Enhanced video processing with proper state management"""
    counter = st.session_state.pizza_counter
    
    try:
        # Save uploaded file
        with st.spinner("💾 Saving uploaded file..."):
            file_path, filename = save_uploaded_file(uploaded_file)
        
        st.success(f"✅ File saved: {filename}")
        
        # Initialize processing state
        processing_key = f"processing_{filename}"
        st.session_state[processing_key] = {
            "active": True,
            "progress": 0,
            "filename": filename,
            "status": "processing",
            "message": "Starting video processing...",
            "start_time": time.time()
        }
        
        # Add to processing videos in counter
        counter.processing_videos[filename] = {
            "status": "processing",
            "progress": 0,
            "start_time": time.time()
        }
        
        # Save video record to database immediately
        video_record = {
            "filename": filename,
            "path": file_path,
            "status": "processing",
            "uploaded_at": time.time(),
            "size": os.path.getsize(file_path),
            "pizza_count": 0
        }
        
        try:
            counter.videos_collection.insert_one(video_record)
        except Exception as e:
            st.warning(f"Database warning: {str(e)}")
        
        # Start background processing
        def background_process():
            try:
                def progress_callback(progress):
                    # Update both session state and counter
                    if processing_key in st.session_state:
                        st.session_state[processing_key]["progress"] = progress
                        st.session_state[processing_key]["message"] = f"Processing... {progress:.1f}%"
                    if filename in counter.processing_videos:
                        counter.processing_videos[filename]["progress"] = progress
                
                # Process video
                result = counter.process_video(file_path, filename, progress_callback=progress_callback)
                
                # Update final state
                final_status = "completed" if result['success'] else "error"
                final_message = f"Found {result['pizza_count']} pizzas" if result['success'] else result.get('error', 'Processing failed')
                
                # Update session state
                if processing_key in st.session_state:
                    st.session_state[processing_key].update({
                        "active": False,
                        "progress": 100,
                        "status": final_status,
                        "message": final_message,
                        "result": result
                    })
                
                # Update counter
                if filename in counter.processing_videos:
                    counter.processing_videos[filename].update({
                        "status": final_status,
                        "progress": 100,
                        "result": result
                    })
                
                # Update database
                try:
                    counter.videos_collection.update_one(
                        {"filename": filename},
                        {
                            "$set": {
                                "status": final_status,
                                "processed_at": time.time(),
                                "pizza_count": result.get('pizza_count', 0),
                                "error_message": result.get('error') if not result['success'] else None
                            }
                        }
                    )
                except Exception as e:
                    st.warning(f"Database update warning: {str(e)}")
                    
            except Exception as e:
                # Handle processing error
                error_message = f"Processing error: {str(e)}"
                if processing_key in st.session_state:
                    st.session_state[processing_key].update({
                        "active": False,
                        "status": "error",
                        "message": error_message
                    })
                if filename in counter.processing_videos:
                    counter.processing_videos[filename].update({
                        "status": "error",
                        "message": error_message
                    })
                
                # Update database
                try:
                    counter.videos_collection.update_one(
                        {"filename": filename},
                        {
                            "$set": {
                                "status": "error",
                                "error_message": error_message,
                                "processed_at": time.time()
                            }
                        }
                    )
                except Exception as db_e:
                    st.warning(f"Database error update warning: {str(db_e)}")
        
        # Start processing thread
        processing_thread = threading.Thread(target=background_process)
        processing_thread.daemon = True
        processing_thread.start()
        
        # Immediate rerun to show processing interface
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Upload error: {str(e)}")

def display_processing_status():
    """Display real-time processing status for all active processes - FOR DASHBOARD"""
    counter = st.session_state.pizza_counter
    
    # Check if any processing is active
    has_active_processing = False
    
    # Check session state first
    for key in st.session_state.keys():
        if key.startswith("processing_") and st.session_state[key].get("active", False):
            has_active_processing = True
            break
    
    # Check counter processing videos
    if not has_active_processing:
        for filename, status in counter.processing_videos.items():
            if status.get("status") == "processing":
                has_active_processing = True
                break
    
    if not has_active_processing:
        return
    
    st.markdown("### 🔄 Active Processing")
    
    # Display session state processing
    for key in st.session_state.keys():
        if key.startswith("processing_") and st.session_state[key].get("active", False):
            status = st.session_state[key]
            filename = status.get("filename", "Unknown")
            progress = status.get("progress", 0)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📹 {filename}")
                st.progress(progress / 100)
            with col2:
                st.write(f"{progress:.1f}%")
    
    # Display counter processing videos
    for filename, status in counter.processing_videos.items():
        if status.get("status") == "processing":
            progress = status.get("progress", 0)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📹 {filename}")
                st.progress(progress / 100)
            with col2:
                st.write(f"{progress:.1f}%")

# Refresh data button (separate from processing)
def display_refresh_button():
    """Display refresh button independent of processing status"""
    if st.button("🔄 Refresh Data", key="refresh_data_btn"):
        # Clear any cached data
        if 'stats_cache' in st.session_state:
            del st.session_state['stats_cache']
        
        # Force refresh by clearing cached stats
        counter = st.session_state.pizza_counter
        if hasattr(counter, '_cached_stats'):
            delattr(counter, '_cached_stats')
        
        st.success("✅ Data refreshed!")
        time.sleep(1)
        st.rerun()

def check_and_resume_processing():
    """Check for stuck processing videos and resume or mark as error"""
    counter = st.session_state.pizza_counter
    
    try:
        # Find videos stuck in processing status
        stuck_videos = counter.videos_collection.find({
            "status": "processing"
        })
        
        current_time = time.time()
        for video in stuck_videos:
            # If video has been processing for more than 30 minutes, mark as error
            upload_time = video.get('uploaded_at', current_time)
            if current_time - upload_time > 1800:  # 30 minutes
                counter.videos_collection.update_one(
                    {"filename": video['filename']},
                    {
                        "$set": {
                            "status": "error",
                            "error_message": "Processing timeout - please try again",
                            "processed_at": current_time
                        }
                    }
                )
                
                # Remove from processing_videos if exists
                if video['filename'] in counter.processing_videos:
                    del counter.processing_videos[video['filename']]
                    
    except Exception as e:
        st.warning(f"Error checking stuck videos: {str(e)}")

# Call this function when the app starts
if 'pizza_counter' in st.session_state:
    check_and_resume_processing()
