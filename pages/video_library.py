import streamlit as st
import os
from datetime import datetime
from components.video_card import display_video_card
from utils.helpers import allowed_file, format_file_size

def show_video_library():
    st.markdown("# 🎬 Video Library")
    
    # Filter options
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input("🔍 Search videos", placeholder="Enter filename...")
    
    with col2:
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "Completed", "Processing", "Error", "Pending"]
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            ["Upload Date", "File Size", "Pizza Count", "Filename"]
        )
    
    # Load and display videos
    videos = load_videos()
    
    # Apply filters
    if search_query:
        videos = [v for v in videos if search_query.lower() in v['filename'].lower()]
    
    if status_filter != "All":
        videos = [v for v in videos if v['status'].lower() == status_filter.lower()]
    
    # Safe sort videos
    videos = safe_sort_videos(videos, sort_by)
    
    # Display video grid
    if not videos:
        st.info("📁 No videos found matching your criteria.")
        return
    
    # Create grid layout
    cols = st.columns(3)
    for i, video in enumerate(videos):
        with cols[i % 3]:
            display_video_card_safe(video)
    
    # Video streaming modal - INLINE thay vì import
    if 'stream_video' in st.session_state and st.session_state.stream_video:
        display_video_stream_inline(st.session_state.stream_video)

def load_videos():
    """Load video list from the system với error handling tốt hơn"""
    try:
        counter = st.session_state.pizza_counter
    except:
        st.error("Pizza counter not initialized")
        return []
    
    upload_folder = './videos'
    videos = []
    
    try:
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            return videos
        
        for filename in os.listdir(upload_folder):
            if allowed_file(filename):
                try:
                    file_path = os.path.join(upload_folder, filename)
                    
                    if not os.path.exists(file_path):
                        continue
                        
                    file_size = os.path.getsize(file_path)
                    
                    # Safe database access
                    try:
                        video_info = counter.get_video_info(filename)
                        if isinstance(video_info, dict) and 'error' in video_info:
                            video_info = {'status': 'pending', 'pizza_count': 0}
                    except Exception:
                        video_info = {'status': 'pending', 'pizza_count': 0}
                    
                    # Create safe video data
                    video_data = {
                        'filename': filename,
                        'path': file_path,
                        'size': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2),
                        'status': video_info.get('status', 'pending'),
                        'pizza_count': video_info.get('pizza_count', 0),
                        'processed_at': video_info.get('processed_at'),
                        'uploaded_at': video_info.get('uploaded_at'),
                        'error_message': video_info.get('error_message')
                    }
                    
                    videos.append(video_data)
                    
                except Exception as file_error:
                    # Log error nhưng tiếp tục
                    print(f"Error processing file {filename}: {str(file_error)}")
                    continue
    
    except Exception as e:
        st.error(f"Error accessing video directory: {str(e)}")
        return []
    
    return videos

def safe_sort_videos(videos, sort_by):
    """Safely sort videos với comprehensive error handling"""
    if not videos:
        return videos
        
    try:
        if sort_by == "File Size":
            return sorted(videos, key=lambda x: x.get('size', 0), reverse=True)
        
        elif sort_by == "Pizza Count":
            return sorted(videos, key=lambda x: x.get('pizza_count', 0), reverse=True)
        
        elif sort_by == "Filename":
            return sorted(videos, key=lambda x: x.get('filename', '').lower())
        
        else:  # Upload Date
            def safe_date_key(video):
                date_val = video.get('processed_at') or video.get('uploaded_at')
                
                if date_val is None:
                    return datetime.min
                
                if isinstance(date_val, str):
                    try:
                        return datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                    except:
                        return datetime.min
                
                if isinstance(date_val, datetime):
                    return date_val
                
                return datetime.min
            
            return sorted(videos, key=safe_date_key, reverse=True)
            
    except Exception as e:
        st.warning(f"Sort error: {str(e)}")
        # Return original list nếu sort fail
        return videos

def display_video_card_safe(video_data):
    """Display video card với error handling"""
    try:
        # Import chỉ khi cần thiết
        from components.video_card import display_video_card
        display_video_card(video_data)
    except ImportError:
        # Fallback: hiển thị card đơn giản
        display_simple_video_card(video_data)
    except Exception as e:
        st.error(f"Error displaying video card: {str(e)}")

def display_simple_video_card(video_data):
    """Fallback simple video card"""
    filename = video_data['filename']
    status = video_data['status']
    pizza_count = video_data.get('pizza_count', 0)
    size_mb = video_data.get('size_mb', 0)
    
    with st.container():
        st.markdown(f"### 📹 {filename}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Status:** {status}")
            st.write(f"**Size:** {size_mb:.1f} MB")
        
        with col2:
            st.write(f"**Pizzas Found:** {pizza_count}")
            
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👁️ View", key=f"view_{filename}"):
                st.info(f"Viewing {filename}")
        
        with col2:
            if status == 'completed' and st.button("🎥 Stream", key=f"stream_{filename}"):
                st.session_state.stream_video = filename
                st.rerun()
        
        with col3:
            if st.button("🗑️ Delete", key=f"delete_{filename}"):
                if st.button(f"⚠️ Confirm Delete {filename}?", key=f"confirm_{filename}"):
                    try:
                        os.remove(video_data['path'])
                        st.success(f"Deleted {filename}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete error: {str(e)}")

def display_video_stream_inline(video_filename):
    """Inline video stream modal thay vì import từ component riêng"""
    with st.container():
        st.markdown("### 🎥 Video Stream")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"🔴 Streaming: {video_filename}")
            st.write("Video streaming functionality would be implemented here")
            
            # Placeholder cho video stream
            st.image("https://via.placeholder.com/640x480/667eea/white?text=Video+Stream", 
                    caption=f"Stream: {video_filename}")
        
        with col2:
            if st.button("❌ Close Stream", key="close_stream"):
                if 'stream_video' in st.session_state:
                    del st.session_state.stream_video
                st.rerun()
            
            st.markdown("**Stream Controls:**")
            st.button("▶️ Play", key="play_stream")
            st.button("⏸️ Pause", key="pause_stream") 
            st.button("⏹️ Stop", key="stop_stream")
            
            st.markdown("**Detection Info:**")
            st.write("Real-time detection stats would appear here")
