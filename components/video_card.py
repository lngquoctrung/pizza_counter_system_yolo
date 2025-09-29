import streamlit as st
import os
from utils.helpers import format_file_size, format_time_ago, get_status_color, get_status_icon
from utils.helpers import extract_video_thumbnail, get_video_info

def display_video_card(video_data):
    """Display individual video card"""
    filename = video_data['filename']
    status = video_data['status']
    pizza_count = video_data.get('pizza_count', 0)
    file_size = video_data.get('size_mb', 0)
    
    # Create card container
    with st.container():
        # Card styling
        status_color = get_status_color(status)
        status_icon = get_status_icon(status)
        
        st.markdown(f"""
        <div style="
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-left: 4px solid {status_color};
            transition: transform 0.3s ease;
        ">
        """, unsafe_allow_html=True)
        
        # Video thumbnail
        thumbnail = extract_video_thumbnail(video_data.get('path'))
        if thumbnail:
            st.image(thumbnail, width=200, caption=filename)
        else:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                height: 120px;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 2rem;
                margin-bottom: 10px;
            ">
                🎬
            </div>
            """, unsafe_allow_html=True)
        
        # Video info
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**{filename}**")
            st.write(f"Size: {format_file_size(video_data.get('size', 0))}")
            
            # Get additional video info
            video_info = get_video_info(video_data.get('path'))
            if video_info:
                st.write(f"Duration: {video_info.get('duration', 0):.1f}s")
                st.write(f"Resolution: {video_info.get('resolution', 'Unknown')}")
        
        with col2:
            st.markdown(f"**Status:** {status_icon} {status.title()}")
            st.write(f"🍕 Pizzas Found: {pizza_count}")
            
            if video_data.get('processed_at'):
                processed_time = format_time_ago(video_data['processed_at'])
                st.write(f"Processed: {processed_time}")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("👁️ View", key=f"view_{filename}"):
                st.session_state.selected_video = video_data
                st.rerun()
        
        with col2:
            if status == 'completed' and st.button("🎥 Stream", key=f"stream_{filename}"):
                st.session_state.stream_video = filename
                st.rerun()
        
        with col3:
            if st.button("📊 Details", key=f"details_{filename}"):
                show_video_details(video_data)
        
        with col4:
            if st.button("🗑️ Delete", key=f"delete_{filename}"):
                delete_video(video_data)
        
        st.markdown("</div>", unsafe_allow_html=True)

def show_video_details(video_data):
    """Show detailed video information in modal"""
    with st.expander(f"📋 Details: {video_data['filename']}", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**File Information:**")
            st.write(f"• Filename: {video_data['filename']}")
            st.write(f"• Size: {format_file_size(video_data.get('size', 0))}")
            st.write(f"• Status: {video_data['status']}")
            st.write(f"• Upload Time: {format_time_ago(video_data.get('uploaded_at'))}")
            
            # Get video technical details
            video_info = get_video_info(video_data.get('path'))
            if video_info:
                st.markdown("**Technical Details:**")
                st.write(f"• Resolution: {video_info.get('resolution', 'Unknown')}")
                st.write(f"• Duration: {video_info.get('duration', 0):.2f} seconds")
                st.write(f"• Frame Rate: {video_info.get('fps', 0):.2f} FPS")
                st.write(f"• Total Frames: {video_info.get('frame_count', 0)}")
        
        with col2:
            st.markdown("**Detection Results:**")
            st.write(f"• Pizza Count: {video_data.get('pizza_count', 0)}")
            st.write(f"• Processed At: {format_time_ago(video_data.get('processed_at'))}")
            
            if video_data['status'] == 'error':
                st.error(f"Error: {video_data.get('error_message', 'Unknown error')}")
            
            # Show detection confidence if available
            counter = st.session_state.pizza_counter
            detections = counter.detections_collection.find({'filename': video_data['filename']})
            
            confidences = [d['confidence'] for d in detections]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                max_confidence = max(confidences)
                min_confidence = min(confidences)
                
                st.write(f"• Avg Confidence: {avg_confidence:.3f}")
                st.write(f"• Max Confidence: {max_confidence:.3f}")
                st.write(f"• Min Confidence: {min_confidence:.3f}")

def delete_video(video_data):
    """Delete video with confirmation"""
    st.warning("⚠️ Are you sure you want to delete this video?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Yes, Delete", key=f"confirm_delete_{video_data['filename']}"):
            try:
                # Delete file from filesystem
                if os.path.exists(video_data.get('path')):
                    os.remove(video_data['path'])
                
                # Delete from database
                counter = st.session_state.pizza_counter
                counter.videos_collection.delete_one({'filename': video_data['filename']})
                counter.detections_collection.delete_many({'filename': video_data['filename']})
                
                st.success("✅ Video deleted successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error deleting video: {str(e)}")
    
    with col2:
        if st.button("❌ Cancel", key=f"cancel_delete_{video_data['filename']}"):
            st.info("Delete cancelled")

def display_video_grid(videos):
    """Display videos in a responsive grid"""
    if not videos:
        st.info("📁 No videos found")
        return
    
    # Create responsive grid
    cols_per_row = 3
    
    for i in range(0, len(videos), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, video in enumerate(videos[i:i+cols_per_row]):
            with cols[j]:
                display_video_card(video)

def display_video_filters():
    """Display video filtering options"""
    st.markdown("### 🔍 Filter Videos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Completed", "Processing", "Error", "Pending"],
            key="video_status_filter"
        )
    
    with col2:
        sort_option = st.selectbox(
            "Sort by",
            ["Upload Date", "File Size", "Pizza Count", "Filename"],
            key="video_sort_option"
        )
    
    with col3:
        sort_order = st.selectbox(
            "Order",
            ["Descending", "Ascending"],
            key="video_sort_order"
        )
    
    return {
        'status_filter': status_filter,
        'sort_option': sort_option,
        'sort_order': sort_order
    }
