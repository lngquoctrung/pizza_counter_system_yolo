import streamlit as st
import os
import time
from utils.helpers import format_file_size, format_time_ago, get_status_color, get_status_icon
from utils.helpers import extract_video_thumbnail, get_video_info

def display_video_card(video_data):
    """Display individual video card with original layout"""
    filename = video_data['filename']
    status = video_data['status']
    pizza_count = video_data.get('pizza_count', 0)
    file_size = video_data.get('size_mb', 0)
    
    with st.container():
        status_color = get_status_color(status)
        status_icon = get_status_icon(status)
        
        # Original video card layout
        col1, col2, col3 = st.columns([3, 2, 2])
        
        with col1:
            # Video thumbnail
            try:
                video_path = f"videos/{filename}"
                if os.path.exists(video_path):
                    thumbnail = extract_video_thumbnail(video_path)
                    if thumbnail:
                        st.image(thumbnail, width=150)
                    else:
                        st.markdown("📹 No thumbnail")
                else:
                    st.markdown("📹 Video not found")
            except Exception as e:
                st.markdown("📹 Thumbnail error")
        
        with col2:
            st.markdown(f"**{filename}**")
            st.markdown(f"{status_icon} **Status:** {status.title()}")
            st.markdown(f"🍕 **Pizza Count:** {pizza_count}")
            st.markdown(f"📊 **Size:** {format_file_size(file_size)}")
            st.markdown(f"⏰ **Uploaded:** {format_time_ago(video_data.get('upload_date', ''))}")
        
        with col3:
            # Action buttons (original layout)
            if st.button("👁️ View", key=f"view_{filename}"):
                st.session_state[f"show_viewer_{filename}"] = True
                st.rerun()
            
            if st.button("🎬 Stream", key=f"stream_{filename}"):
                st.session_state[f"show_stream_{filename}"] = True
                st.rerun()
                
            if st.button("📊 Details", key=f"details_{filename}"):
                st.session_state[f"show_details_{filename}"] = True
                st.rerun()
            
            if st.button("🗑️ Delete", key=f"delete_{filename}"):
                delete_video(filename)
                st.rerun()
        
        st.markdown("---")

        # Modal handlers
        if st.session_state.get(f"show_viewer_{filename}", False):
            display_video_viewer_modal(filename)
        
        if st.session_state.get(f"show_stream_{filename}", False):
            display_video_stream_modal(filename)
        
        if st.session_state.get(f"show_details_{filename}", False):
            display_video_details_modal(video_data)

def display_video_viewer_modal(filename):
    """Display simple video viewer - chỉ hiển thị video + close"""
    video_path = f"videos/{filename}"
    
    if not os.path.exists(video_path):
        st.error(f"Video file not found: {filename}")
        return
    
    # Simple modal
    with st.container():
        # Header with close button
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### 🎥 Video Viewer: {filename}")
        with col2:
            if st.button("❌ Close", key=f"close_viewer_{filename}"):
                st.session_state[f"show_viewer_{filename}"] = False
                st.rerun()
        
        # Just the video player
        st.video(video_path)

def display_video_stream_modal(filename):
    """Display video with real-time detection stream"""
    video_path = f"videos/{filename}"
    
    if not os.path.exists(video_path):
        st.error(f"Video file not found: {filename}")
        return
    
    with st.container():
        # Header with close button
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### 🎬 Detection Stream: {filename}")
        with col2:
            if st.button("❌ Close", key=f"close_stream_{filename}"):
                st.session_state[f"show_stream_{filename}"] = False
                if f"stream_active_{filename}" in st.session_state:
                    st.session_state[f"stream_active_{filename}"] = False
                st.rerun()
        
        # Stream controls
        col1, col2, col3 = st.columns([1, 1, 4])
        
        with col1:
            if st.button("▶️ Start", key=f"start_stream_{filename}"):
                st.session_state[f"stream_active_{filename}"] = True
                st.session_state[f"stream_pizza_count_{filename}"] = 0  # Reset count
                st.rerun()
        
        with col2:
            if st.button("⏹️ Stop", key=f"stop_stream_{filename}"):
                st.session_state[f"stream_active_{filename}"] = False
                st.rerun()
        
        # Stream display area với fixed width/height
        st.markdown("""
        <style>
        .stream-video {
            width: 100% !important;
            max-width: 800px !important;
            height: auto !important;
            min-height: 400px !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        frame_placeholder = st.empty()
        stats_placeholder = st.empty()
        
        # Check if stream is active
        if st.session_state.get(f"stream_active_{filename}", False):
            import cv2
            import time
            from PIL import Image
            
            counter = st.session_state.pizza_counter
            cap = cv2.VideoCapture(video_path)
            
            if cap.isOpened():
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS) or 25
                frame_count = 0
                
                # Initialize tracking for pizza counting
                tracked_pizzas = set()  # Set to track unique pizza IDs
                total_pizza_detected = st.session_state.get(f"stream_pizza_count_{filename}", 0)
                
                while (cap.isOpened() and 
                       st.session_state.get(f"stream_active_{filename}", False) and
                       st.session_state.get(f"show_stream_{filename}", False)):
                    
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    frame_count += 1
                    
                    # Process frame for detection (every 3rd frame for performance)
                    if frame_count % 3 == 0:
                        # Use tracking instead of simple detection
                        try:
                            results = counter.model.track(
                                frame,
                                persist=True,
                                classes=[counter.pizza_class_id],
                                conf=counter.confidence_threshold,
                                tracker="bytetrack.yaml"
                            )
                            
                            annotated_frame = frame.copy()
                            current_frame_pizzas = 0
                            
                            if (results[0].boxes is not None and 
                                results[0].boxes.id is not None and 
                                len(results[0].boxes.id) > 0):
                                
                                boxes = results[0].boxes.xyxy.cpu().numpy()
                                track_ids = results[0].boxes.id.int().cpu().tolist()
                                confidences = results[0].boxes.conf.cpu().tolist()
                                
                                for box, track_id, conf in zip(boxes, track_ids, confidences):
                                    if conf >= counter.confidence_threshold:
                                        # Count unique tracked pizzas
                                        if track_id not in tracked_pizzas:
                                            tracked_pizzas.add(track_id)
                                            total_pizza_detected += 1
                                        
                                        current_frame_pizzas += 1
                                        
                                        # Draw bounding box
                                        x1, y1, x2, y2 = box.astype(int)
                                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                        cv2.putText(annotated_frame, f'Pizza {track_id}: {conf:.2f}', 
                                                  (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                            
                            # Update session state
                            st.session_state[f"stream_pizza_count_{filename}"] = total_pizza_detected
                            
                            # Convert to RGB and resize for proper display
                            annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                            frame_pil = Image.fromarray(annotated_frame_rgb)
                            
                            # Display frame with proper sizing
                            frame_placeholder.image(frame_pil, width=800, use_column_width=False)
                            
                            # Display stats
                            stats_placeholder.markdown(f"""
                            **Frame:** {frame_count}/{total_frames} | 
                            **Pizza in frame:** {current_frame_pizzas} | 
                            **Total detected:** {total_pizza_detected}
                            """)
                            
                        except Exception as e:
                            # Display original frame if tracking fails
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            frame_pil = Image.fromarray(frame_rgb)
                            frame_placeholder.image(frame_pil, width=800, use_column_width=False)
                            stats_placeholder.error(f"Detection error: {str(e)}")
                    
                    else:
                        # Show original frame for skipped frames
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame_pil = Image.fromarray(frame_rgb)
                        frame_placeholder.image(frame_pil, width=800, use_column_width=False)
                    
                    # Control playback speed
                    time.sleep(1.0 / fps if fps > 0 else 0.033)
                
                cap.release()
                
                if frame_count >= total_frames:
                    stats_placeholder.success(f"Stream completed! Total pizzas detected: {total_pizza_detected}")
                    st.session_state[f"stream_active_{filename}"] = False
            else:
                st.error("Cannot open video file for streaming")
        else:
            # Show static thumbnail when not streaming
            try:
                thumbnail = extract_video_thumbnail(video_path)
                if thumbnail:
                    frame_placeholder.image(thumbnail, width=800, use_column_width=False)
                    total_detected = st.session_state.get(f"stream_pizza_count_{filename}", 0)
                    stats_placeholder.info(f"Click Start to begin detection stream | Total detected: {total_detected}")
                else:
                    frame_placeholder.info("Video preview not available")
            except:
                frame_placeholder.info("Video preview not available")

def display_video_details_modal(video_data):
    """Display detailed video information modal"""
    filename = video_data['filename']
    
    with st.container():
        # Header with close button
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### 📊 Video Details: {filename}")
        with col2:
            if st.button("❌ Close", key=f"close_details_{filename}"):
                st.session_state[f"show_details_{filename}"] = False
                st.rerun()
        
        # Details layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### Basic Information")
            st.markdown(f"""
            - **Filename:** {filename}
            - **Status:** {video_data.get('status', 'Unknown')}
            - **Upload Date:** {format_time_ago(video_data.get('upload_date', ''))}
            - **File Size:** {format_file_size(video_data.get('size_mb', 0))}
            - **Pizza Count:** {video_data.get('pizza_count', 0)}
            """)
            
            st.markdown("#### Processing Information")
            st.markdown(f"""
            - **Total Frames:** {video_data.get('total_frames', 'N/A')}
            - **Processed Frames:** {video_data.get('processed_frames', 'N/A')}
            - **Processing Time:** {video_data.get('processing_time', 'N/A')}
            - **Average Confidence:** {video_data.get('avg_confidence', 'N/A')}
            """)
        
        with col2:
            st.markdown("#### Detection Statistics")
            
            # Get detection statistics
            counter = st.session_state.pizza_counter
            try:
                if counter.db_available:
                    detections = list(counter.detections_collection.find(
                        {'filename': filename}
                    ))
                    
                    if detections:
                        confidences = [d.get('confidence', 0) for d in detections]
                        st.markdown(f"""
                        - **Total Detections:** {len(detections)}
                        - **Max Confidence:** {max(confidences):.2f}
                        - **Min Confidence:** {min(confidences):.2f}
                        - **Avg Confidence:** {sum(confidences)/len(confidences):.2f}
                        """)
                        
                        # Show recent detections
                        st.markdown("#### Recent Detections")
                        for i, detection in enumerate(detections[-5:], 1):
                            st.markdown(f"""
                            **Detection {i}:**
                            - Frame: {detection.get('frame_count', 'N/A')}
                            - Confidence: {detection.get('confidence', 0):.2f}
                            - Time: {format_time_ago(detection.get('timestamp', ''))}
                            """)
                    else:
                        st.info("No detection data available")
                else:
                    st.warning("Database not available")
            except Exception as e:
                st.error(f"Error loading detection data: {str(e)}")

def delete_video(filename):
    """Delete video file and database record"""
    try:
        # Delete file
        video_path = f"videos/{filename}"
        if os.path.exists(video_path):
            os.remove(video_path)
        
        # Delete from database
        counter = st.session_state.pizza_counter
        if counter.db_available:
            counter.videos_collection.delete_one({'filename': filename})
            counter.detections_collection.delete_many({'filename': filename})
        
        st.success(f"Video {filename} deleted successfully")
    except Exception as e:
        st.error(f"Error deleting video: {str(e)}")
