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
        
        # Create available_classes dict since PizzaCounter doesn't have get_available_classes method
        available_classes = {53: 'pizza'}  # COCO dataset pizza class
        current_classes = counter.classes_to_detect
        
        class_options = []
        for class_id, class_name in available_classes.items():
            class_options.append(f"{class_name} (ID: {class_id})")
        
        selected_classes = st.multiselect(
            "Classes to detect",
            options=class_options,
            default=[f"pizza (ID: 53)"] if 53 in current_classes else [],
            help="Select which object classes to detect"
        )
        
        if st.button("Update Detection Classes"):
            # Extract class IDs from selected options
            new_classes = []
            for option in selected_classes:
                class_id = int(option.split("ID: ")[1].split(")")[0])
                new_classes.append(class_id)
            
            counter.classes_to_detect = new_classes
            st.success(f"Updated detection classes: {selected_classes}")
    
    # Tracking Settings
    st.markdown("## 🎯 Tracking Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tracking_threshold = st.slider(
            "Tracking Threshold",
            min_value=0.1,
            max_value=1.0,
            value=current_settings.get('tracking_threshold', 0.3),
            step=0.05,
            help="Minimum confidence for object tracking"
        )
        
        movement_threshold = st.slider(
            "Movement Threshold",
            min_value=10,
            max_value=200,
            value=int(current_settings.get('movement_threshold', 50)),
            step=5,
            help="Minimum movement distance to count as removed"
        )
    
    with col2:
        frame_skip = st.slider(
            "Frame Skip",
            min_value=1,
            max_value=10,
            value=int(current_settings.get('frame_skip', 3)),
            step=1,
            help="Number of frames to skip for performance"
        )
        
        if st.button("Update Tracking Settings"):
            counter.tracking_threshold = tracking_threshold
            counter.movement_threshold = movement_threshold
            counter.frame_skip = frame_skip
            st.success("Tracking settings updated successfully!")
    
    # System Information
    st.markdown("## 💾 System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Model Path:** ./models/yolo11n.pt")
        st.info(f"**Database Status:** {'Connected' if counter.db_available else 'Disconnected'}")
        st.info(f"**Pizza Class ID:** {counter.pizza_class_id}")
    
    with col2:
        st.info(f"**Current Classes:** {counter.classes_to_detect}")
        st.info(f"**Processing Videos:** {len(counter.processing_videos)}")
        
        # Model info
        try:
            model_info = f"**Model Type:** {counter.model.__class__.__name__}"
            st.info(model_info)
        except:
            st.info("**Model Type:** YOLO11n")
    
    # Export/Import Settings
    st.markdown("## 📤 Settings Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export Settings"):
            settings_data = {
                'confidence_threshold': counter.confidence_threshold,
                'tracking_threshold': counter.tracking_threshold,
                'movement_threshold': counter.movement_threshold,
                'frame_skip': counter.frame_skip,
                'classes_to_detect': counter.classes_to_detect,
                'pizza_class_id': counter.pizza_class_id
            }
            
            import json
            settings_json = json.dumps(settings_data, indent=2)
            st.download_button(
                label="Download Settings JSON",
                data=settings_json,
                file_name="pizza_detection_settings.json",
                mime="application/json"
            )
    
    with col2:
        uploaded_settings = st.file_uploader(
            "Import Settings",
            type=['json'],
            help="Upload a settings JSON file"
        )
        
        if uploaded_settings is not None:
            try:
                import json
                settings_data = json.load(uploaded_settings)
                
                # Validate and apply settings
                if all(key in settings_data for key in ['confidence_threshold', 'tracking_threshold']):
                    counter.confidence_threshold = settings_data['confidence_threshold']
                    counter.tracking_threshold = settings_data['tracking_threshold']
                    counter.movement_threshold = settings_data.get('movement_threshold', 50)
                    counter.frame_skip = settings_data.get('frame_skip', 3)
                    counter.classes_to_detect = settings_data.get('classes_to_detect', [53])
                    
                    st.success("Settings imported successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Invalid settings file format")
            except Exception as e:
                st.error(f"Error importing settings: {str(e)}")
    
    # Database Management
    if counter.db_available:
        st.markdown("## 🗄️ Database Management")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Clear Detection History"):
                if st.session_state.get('confirm_clear_detections', False):
                    try:
                        counter.detections_collection.delete_many({})
                        st.success("Detection history cleared!")
                        st.session_state.confirm_clear_detections = False
                    except Exception as e:
                        st.error(f"Error clearing detections: {e}")
                else:
                    st.session_state.confirm_clear_detections = True
                    st.warning("Click again to confirm deletion")
        
        with col2:
            if st.button("Clear Video Records"):
                if st.session_state.get('confirm_clear_videos', False):
                    try:
                        counter.videos_collection.delete_many({})
                        st.success("Video records cleared!")
                        st.session_state.confirm_clear_videos = False
                    except Exception as e:
                        st.error(f"Error clearing videos: {e}")
                else:
                    st.session_state.confirm_clear_videos = True
                    st.warning("Click again to confirm deletion")
        
        with col3:
            if st.button("Clear All Feedback"):
                if st.session_state.get('confirm_clear_feedback', False):
                    try:
                        counter.feedback_collection.delete_many({})
                        st.success("Feedback cleared!")
                        st.session_state.confirm_clear_feedback = False
                    except Exception as e:
                        st.error(f"Error clearing feedback: {e}")
                else:
                    st.session_state.confirm_clear_feedback = True
                    st.warning("Click again to confirm deletion")
        
        # Database Stats
        st.markdown("### Database Statistics")
        try:
            detection_count = counter.detections_collection.count_documents({})
            video_count = counter.videos_collection.count_documents({})
            feedback_count = counter.feedback_collection.count_documents({})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Detections", detection_count)
            with col2:
                st.metric("Total Videos", video_count)
            with col3:
                st.metric("Total Feedback", feedback_count)
        except Exception as e:
            st.error(f"Error getting database stats: {e}")
    
    # Reset to Default Settings
    st.markdown("## ⚙️ Reset Settings")
    if st.button("Reset to Default Settings"):
        if st.session_state.get('confirm_reset', False):
            counter.confidence_threshold = 0.5
            counter.tracking_threshold = 0.3
            counter.movement_threshold = 50
            counter.frame_skip = 3
            counter.classes_to_detect = [53]
            
            st.success("Settings reset to default values!")
            st.session_state.confirm_reset = False
            st.experimental_rerun()
        else:
            st.session_state.confirm_reset = True
            st.warning("Click again to confirm reset")
