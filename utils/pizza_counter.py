import cv2
import os
import numpy as np
import streamlit as st
from ultralytics import YOLO
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class PizzaCounter:
    def __init__(self, model_path="./models/yolo11n.pt", mongodb_uri=st.secrets["MONGODB_URI"]):
        """Initialize pizza counter with YOLO model and MongoDB connection"""
        if model_path is None:
            model_path = "./models/yolo11n.pt"
            
        if not os.path.exists(model_path):
            print("Downloading YOLO model...")
            
        self.model = YOLO(model_path)
        
        # COCO dataset class IDs - pizza is class 53
        self.pizza_class_id = 53
        self.classes_to_detect = [self.pizza_class_id]
        
        self.client = MongoClient(mongodb_uri)
        self.db = self.client.pizza_detection
        
        # Collections
        self.detections_collection = self.db.detections
        self.feedback_collection = self.db.feedback
        self.videos_collection = self.db.videos
        self.settings_collection = self.db.settings
        
        # Processing state
        self.processing_videos = {}
        self.stream_active = False
        
        # Default settings
        self.default_settings = {
            'confidence_threshold': 0.5,
            'frame_skip': 3,
            'max_video_size': 500,  # MB
            'processing_threads': 2
        }
        
        # Initialize default settings if not exist
        self._initialize_settings()
        
    def _initialize_settings(self):
        """Initialize default settings in database"""
        existing_settings = self.settings_collection.find_one({'type': 'model_settings'})
        if not existing_settings:
            self.settings_collection.insert_one({
                'type': 'model_settings',
                'settings': self.default_settings,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
    
    def get_model_settings(self):
        """Get current model settings"""
        settings_doc = self.settings_collection.find_one({'type': 'model_settings'})
        if settings_doc:
            return settings_doc['settings']
        return self.default_settings
    
    def update_confidence_threshold(self, threshold):
        """Update confidence threshold"""
        settings = self.get_model_settings()
        settings['confidence_threshold'] = threshold
        
        self.settings_collection.update_one(
            {'type': 'model_settings'},
            {
                '$set': {
                    'settings': settings,
                    'updated_at': datetime.now()
                }
            },
            upsert=True
        )
        
    def process_video(self, video_path, filename, progress_callback=None):
        """Process video and count pizzas with progress tracking"""
        try:
            # Mark video as processing
            self.processing_videos[filename] = {
                'status': 'processing',
                'progress': 0,
                'start_time': datetime.now()
            }
            
            # Insert video record
            video_doc = {
                'filename': filename,
                'file_path': video_path,
                'status': 'processing',
                'uploaded_at': datetime.now(),
                'processed_at': None,
                'pizza_count': 0,
                'total_frames': 0,
                'processed_frames': 0
            }
            
            video_result = self.videos_collection.insert_one(video_doc)
            video_id = video_result.inserted_id
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("Could not open video file")
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_count = 0
            pizza_detections = []
            
            settings = self.get_model_settings()
            confidence_threshold = settings.get('confidence_threshold', 0.5)
            frame_skip = settings.get('frame_skip', 3)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Skip frames for performance
                if frame_count % frame_skip != 0:
                    continue
                
                # Update progress
                progress = (frame_count / total_frames) * 100
                self.processing_videos[filename]['progress'] = progress
                
                if progress_callback:
                    progress_callback(progress)
                
                # Run detection
                results = self.model(frame, classes=self.classes_to_detect, conf=confidence_threshold)
                
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            conf = float(box.conf[0])
                            cls = int(box.cls[0])
                            
                            if cls == self.pizza_class_id and conf >= confidence_threshold:
                                x1, y1, x2, y2 = box.xyxy[0].tolist()
                                
                                detection = {
                                    'video_id': video_id,
                                    'filename': filename,
                                    'frame_number': frame_count,
                                    'timestamp': datetime.now(),
                                    'confidence': conf,
                                    'bbox': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2},
                                    'class_id': cls,
                                    'class_name': 'pizza'
                                }
                                
                                pizza_detections.append(detection)
            
            cap.release()
            
            # Save detections
            if pizza_detections:
                self.detections_collection.insert_many(pizza_detections)
            
            # Update video record
            self.videos_collection.update_one(
                {'_id': video_id},
                {
                    '$set': {
                        'status': 'completed',
                        'processed_at': datetime.now(),
                        'pizza_count': len(pizza_detections),
                        'total_frames': total_frames,
                        'processed_frames': frame_count
                    }
                }
            )
            
            # Update processing state
            self.processing_videos[filename] = {
                'status': 'completed',
                'progress': 100,
                'pizza_count': len(pizza_detections),
                'end_time': datetime.now()
            }
            
            return {
                'success': True,
                'pizza_count': len(pizza_detections),
                'total_frames': total_frames,
                'detections': pizza_detections
            }
            
        except Exception as e:
            # Mark as error
            if filename in self.processing_videos:
                self.processing_videos[filename]['status'] = 'error'
                self.processing_videos[filename]['error'] = str(e)
            
            if 'video_id' in locals():
                self.videos_collection.update_one(
                    {'_id': video_id},
                    {'$set': {'status': 'error', 'error_message': str(e)}}
                )
            
            return {'success': False, 'error': str(e)}
    
    def process_frame_for_stream(self, frame):
        """Process single frame for real-time streaming"""
        try:
            settings = self.get_model_settings()
            confidence_threshold = settings.get('confidence_threshold', 0.5)
            
            # Run detection
            results = self.model(frame, classes=self.classes_to_detect, conf=confidence_threshold)
            
            detections = []
            annotated_frame = frame.copy()
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])
                        
                        if cls == self.pizza_class_id and conf >= confidence_threshold:
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            
                            # Draw bounding box
                            cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                            cv2.putText(annotated_frame, f'Pizza: {conf:.2f}', (int(x1), int(y1) - 10),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                            
                            detections.append({
                                'confidence': conf,
                                'bbox': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2},
                                'class_name': 'pizza'
                            })
            
            return {
                'frame': annotated_frame,
                'detections': detections,
                'pizza_count': len(detections)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_comprehensive_stats(self):
        """Get comprehensive system statistics"""
        try:
            # Basic counts
            total_videos = self.videos_collection.count_documents({})
            completed_videos = self.videos_collection.count_documents({'status': 'completed'})
            processing_videos = self.videos_collection.count_documents({'status': 'processing'})
            total_detections = self.detections_collection.count_documents({})
            
            # Recent stats (last 24 hours)
            yesterday = datetime.now() - timedelta(days=1)
            recent_detections = self.detections_collection.count_documents({'timestamp': {'$gte': yesterday}})
            recent_videos = self.videos_collection.count_documents({'uploaded_at': {'$gte': yesterday}})
            
            # Average confidence
            pipeline = [
                {'$group': {'_id': None, 'avg_confidence': {'$avg': '$confidence'}}}
            ]
            avg_conf_result = list(self.detections_collection.aggregate(pipeline))
            avg_confidence = avg_conf_result[0]['avg_confidence'] if avg_conf_result else 0
            
            # Model accuracy (based on feedback)
            total_feedback = self.feedback_collection.count_documents({})
            positive_feedback = self.feedback_collection.count_documents({'feedback_type': 'correct'})
            accuracy_percentage = (positive_feedback / total_feedback * 100) if total_feedback > 0 else 0
            
            # Processing status
            currently_processing = len([v for v in self.processing_videos.values() if v['status'] == 'processing'])
            
            return {
                'total_videos': total_videos,
                'completed_videos': completed_videos,
                'processing_videos': processing_videos,
                'currently_processing': currently_processing,
                'total_detections': total_detections,
                'recent_detections': recent_detections,
                'recent_videos': recent_videos,
                'avg_confidence': round(avg_confidence, 3) if avg_confidence else 0,
                'accuracy_percentage': round(accuracy_percentage, 1),
                'feedback_count': total_feedback,
                'model_settings': self.get_model_settings()
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_video_info(self, filename):
        """Get information about a specific video"""
        try:
            video_doc = self.videos_collection.find_one({'filename': filename})
            if video_doc:
                # Convert ObjectId to string for JSON serialization
                video_doc['_id'] = str(video_doc['_id'])
                return video_doc
            
            # Check if video is currently being processed
            if filename in self.processing_videos:
                return self.processing_videos[filename]
            
            return {'status': 'not_found'}
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_analytics_data(self, start_date, end_date):
        """Get analytics data for specified date range"""
        try:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            # Total detections in range
            total_detections = self.detections_collection.count_documents({
                'timestamp': {'$gte': start_datetime, '$lte': end_datetime}
            })
            
            # Daily detection counts
            daily_pipeline = [
                {'$match': {'timestamp': {'$gte': start_datetime, '$lte': end_datetime}}},
                {
                    '$group': {
                        '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$timestamp'}},
                        'count': {'$sum': 1}
                    }
                },
                {'$sort': {'_id': 1}}
            ]
            
            daily_detections = list(self.detections_collection.aggregate(daily_pipeline))
            daily_data = [{'date': item['_id'], 'count': item['count']} for item in daily_detections]
            
            # Confidence distribution
            confidence_pipeline = [
                {'$match': {'timestamp': {'$gte': start_datetime, '$lte': end_datetime}}},
                {'$project': {'confidence': 1}}
            ]
            
            confidence_data = list(self.detections_collection.aggregate(confidence_pipeline))
            
            # Average confidence
            avg_confidence = sum(item['confidence'] for item in confidence_data) / len(confidence_data) if confidence_data else 0
            
            # Videos processed in range
            videos_processed = self.videos_collection.count_documents({
                'processed_at': {'$gte': start_datetime, '$lte': end_datetime}
            })
            
            # Model accuracy
            total_feedback = self.feedback_collection.count_documents({
                'timestamp': {'$gte': start_datetime, '$lte': end_datetime}
            })
            positive_feedback = self.feedback_collection.count_documents({
                'timestamp': {'$gte': start_datetime, '$lte': end_datetime},
                'feedback_type': 'correct'
            })
            model_accuracy = (positive_feedback / total_feedback * 100) if total_feedback > 0 else 0
            
            # Detailed detection log
            detection_log = list(self.detections_collection.find({
                'timestamp': {'$gte': start_datetime, '$lte': end_datetime}
            }).sort('timestamp', -1).limit(100))
            
            # Format detection log for display
            formatted_log = []
            for detection in detection_log:
                formatted_log.append({
                    'timestamp': detection['timestamp'],
                    'filename': detection['filename'],
                    'confidence': detection['confidence'],
                    'pizza_count': 1  # Each detection represents one pizza
                })
            
            return {
                'total_detections': total_detections,
                'daily_detections': daily_data,
                'confidence_distribution': confidence_data,
                'avg_confidence': avg_confidence,
                'videos_processed': videos_processed,
                'model_accuracy': model_accuracy,
                'detection_log': formatted_log
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def submit_feedback(self, detection_id, feedback_type, user_comment=None):
        """Submit feedback for a detection"""
        try:
            feedback_doc = {
                'detection_id': detection_id,
                'feedback_type': feedback_type,  # 'correct', 'incorrect', 'missed'
                'user_comment': user_comment,
                'timestamp': datetime.now()
            }
            
            result = self.feedback_collection.insert_one(feedback_doc)
            
            # Update model accuracy based on feedback
            self._update_model_accuracy()
            
            return {'success': True, 'feedback_id': str(result.inserted_id)}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _update_model_accuracy(self):
        """Update model accuracy based on feedback"""
        total_feedback = self.feedback_collection.count_documents({})
        positive_feedback = self.feedback_collection.count_documents({'feedback_type': 'correct'})
        
        accuracy = (positive_feedback / total_feedback * 100) if total_feedback > 0 else 0
        
        # Store accuracy in settings
        self.settings_collection.update_one(
            {'type': 'model_accuracy'},
            {
                '$set': {
                    'accuracy': accuracy,
                    'total_feedback': total_feedback,
                    'positive_feedback': positive_feedback,
                    'updated_at': datetime.now()
                }
            },
            upsert=True
        )
    
    def get_available_classes(self):
        """Get available YOLO classes"""
        # COCO dataset classes (relevant ones for pizza detection)
        coco_classes = {
            53: 'pizza',
            47: 'cup',
            46: 'wine glass',
            50: 'spoon',
            51: 'bowl',
            52: 'banana',
            54: 'donut',
            55: 'cake'
        }
        return coco_classes
    
    def set_detection_classes(self, class_ids):
        """Set which classes to detect"""
        self.classes_to_detect = class_ids
        
        # Update in settings
        settings = self.get_model_settings()
        settings['detection_classes'] = class_ids
        
        self.settings_collection.update_one(
            {'type': 'model_settings'},
            {
                '$set': {
                    'settings': settings,
                    'updated_at': datetime.now()
                }
            },
            upsert=True
        )
    
    def reset_model_settings(self):
        """Reset model settings to defaults"""
        self.settings_collection.update_one(
            {'type': 'model_settings'},
            {
                '$set': {
                    'settings': self.default_settings,
                    'updated_at': datetime.now()
                }
            },
            upsert=True
        )
    
    def rebuild_statistics(self):
        """Rebuild all statistics"""
        try:
            # Recalculate model accuracy
            self._update_model_accuracy()
            
            # Rebuild video statistics
            videos = self.videos_collection.find({'status': 'completed'})
            for video in videos:
                detection_count = self.detections_collection.count_documents({'video_id': video['_id']})
                self.videos_collection.update_one(
                    {'_id': video['_id']},
                    {'$set': {'pizza_count': detection_count}}
                )
            
            return {'success': True, 'message': 'Statistics rebuilt successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_processing_status(self, filename):
        """Get processing status for a specific video"""
        if filename in self.processing_videos:
            return self.processing_videos[filename]
        
        # Check database
        video_doc = self.videos_collection.find_one({'filename': filename})
        if video_doc:
            return {
                'status': video_doc['status'],
                'progress': 100 if video_doc['status'] == 'completed' else 0,
                'pizza_count': video_doc.get('pizza_count', 0)
            }
        
        return {'status': 'not_found'}
