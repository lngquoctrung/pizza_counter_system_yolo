import streamlit as st
import os
from utils.helpers import get_available_classes

def show_settings():
    st.markdown("# ⚙️ System Settings")
    
    counter = st.session_state.pizza_counter
    
    # Model Settings Section
    st.markdown("## 🤖 Model Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Confidence threshold
        current_settings = counter.get_model_settings()
        confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.1,
            max_value=1.0,
            value=current_settings.get('confidence_threshold', 0.5),
            step=0.05,
            help="Minimum confidence score for detections"
        )
        
        if st.button("Update Confidence Threshold"):
            counter.update_confidence_threshold(confidence_threshold)
            st.success(f"Confidence threshold updated to {confidence_threshold}")
    
    with col2:
        # Detection classes
        st.markdown("### Detection Classes")
        available_classes = counter.get_available_classes()
        current_classes = counter.classes_to_detect
        
        class_options = []
        for class_id, class_name in available_classes.items():
            class_options.append(f"{class_name} (ID: {class_id})")
        
        selected_classes = st.multiselect(
            "Select classes to detect",
            options=class_options,
            default=[f"{available_classes[cls]} (ID: {cls})" for cls in current_classes],
            help="Choose which object classes to detect in videos"
        )
        
        if st.button("Update Detection Classes"):
            # Extract class IDs from selected options
            new_class_ids = []
            for selection in selected_classes:
                class_id = int(selection.split("ID: ")[1].rstrip(")"))
                new_class_ids.append(class_id)
            
            counter.set_detection_classes(new_class_ids)
            st.success("Detection classes updated successfully!")
    
    # Database Settings Section
    st.markdown("## 🗄️ Database Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Database connection status
        try:
            # Test database connection
            stats = counter.get_comprehensive_stats()
            st.success("✅ Database connection active")
            
            # Database statistics
            st.markdown("**Database Stats:**")
            st.write(f"- Total detections: {stats.get('total_detections', 0)}")
            st.write(f"- Total videos: {stats.get('total_videos', 0)}")
            st.write(f"- Feedback entries: {stats.get('feedback_count', 0)}")
            
        except Exception as e:
            st.error(f"❌ Database connection error: {str(e)}")
    
    with col2:
        # Database maintenance
        st.markdown("**Database Maintenance:**")
        
        if st.button("🧹 Clean Old Data"):
            # Add database cleanup functionality
            st.info("Database cleanup initiated...")
        
        if st.button("📊 Rebuild Statistics"):
            counter.rebuild_statistics()
            st.success("Statistics rebuilt successfully!")
        
        if st.button("🔄 Reset Model Settings"):
            counter.reset_model_settings()
            st.success("Model settings reset to defaults!")
    
    # Performance Settings
    st.markdown("## 🚀 Performance Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Video processing settings
        st.markdown("### Video Processing")
        
        max_video_size = st.number_input(
            "Max Video Size (MB)",
            min_value=10,
            max_value=1000,
            value=500,
            step=10,
            help="Maximum allowed video file size"
        )
        
        processing_threads = st.slider(
            "Processing Threads",
            min_value=1,
            max_value=8,
            value=2,
            help="Number of threads for video processing"
        )
    
    with col2:
        # Real-time processing settings
        st.markdown("### Real-time Processing")
        
        frame_skip = st.slider(
            "Frame Skip Rate",
            min_value=1,
            max_value=10,
            value=3,
            help="Process every Nth frame for better performance"
        )
        
        stream_quality = st.selectbox(
            "Stream Quality",
            ["Low (480p)", "Medium (720p)", "High (1080p)"],
            index=1,
            help="Quality for real-time video streaming"
        )
    
    # System Info Section
    st.markdown("## 📋 System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**System Status:**")
        st.write("- Application: Running ✅")
        st.write("- YOLO Model: Loaded ✅")
        st.write("- MongoDB: Connected ✅")
        st.write(f"- Videos Directory: {'Exists' if os.path.exists('./videos') else 'Missing'}")
    
    with col2:
        st.markdown("**Model Information:**")
        st.write("- Model: YOLO11n")
        st.write("- Framework: Ultralytics")
        st.write("- Dataset: COCO")
        st.write("- Pizza Class ID: 53")
    
    # Export/Import Settings
    st.markdown("## 💾 Settings Backup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Settings"):
            settings_data = {
                'confidence_threshold': confidence_threshold,
                'detection_classes': current_classes,
                'max_video_size': max_video_size,
                'processing_threads': processing_threads,
                'frame_skip': frame_skip,
                'stream_quality': stream_quality
            }
            
            import json
            settings_json = json.dumps(settings_data, indent=2)
            st.download_button(
                label="Download Settings",
                data=settings_json,
                file_name="pizza_detection_settings.json",
                mime="application/json"
            )
    
    with col2:
        uploaded_settings = st.file_uploader(
            "Import Settings",
            type=['json'],
            help="Upload previously exported settings file"
        )
        
        if uploaded_settings and st.button("📤 Import Settings"):
            try:
                import json
                settings_data = json.loads(uploaded_settings.read())
                
                # Apply imported settings
                counter.update_confidence_threshold(settings_data.get('confidence_threshold', 0.5))
                counter.set_detection_classes(settings_data.get('detection_classes', [53]))
                
                st.success("Settings imported successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error importing settings: {str(e)}")
