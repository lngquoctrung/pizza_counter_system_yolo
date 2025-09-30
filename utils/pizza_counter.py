import cv2
import os
import numpy as np
import streamlit as st
from ultralytics import YOLO
from pymongo import MongoClient
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv
import threading
import time

load_dotenv()

class PizzaCounter:
    _instance = None
    _initialized = False
    
    def __new__(cls, model_path="./models/yolo11n.pt", mongodb_uri=None):
        if cls._instance is None:
            cls._instance = super(PizzaCounter, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, model_path="./models/yolo11n.pt", mongodb_uri=None):
        """Initialize pizza counter với thuật toán gốc - SINGLETON PATTERN"""
        if self._initialized:
            return
            
        if mongodb_uri is None:
            mongodb_uri = st.secrets["MONGODB_URI"]
        
        if model_path is None:
            model_path = "./models/yolo11n.pt"
        if not os.path.exists(model_path):
            print("Downloading YOLO model...")
        self.model = YOLO(model_path)
        
        # COCO dataset class IDs - pizza is class 53
        self.pizza_class_id = 53
        self.classes_to_detect = [self.pizza_class_id]
        
        # MongoDB connection với proper error handling
        self.db_available = False
        try:
            self.client = MongoClient(mongodb_uri)
            self.db = self.client.pizza_detection
            # Collections
            self.detections_collection = self.db.detections
            self.feedback_collection = self.db.feedback
            self.videos_collection = self.db.videos
            self.settings_collection = self.db.settings
            
            # Test connection
            self.client.admin.command('ping')
            self.db_available = True
            print("✅ MongoDB connected successfully")
        except Exception as e:
            print(f"⚠️ MongoDB connection failed: {e}")
            self.client = None
            self.db = None
            self.db_available = False
        
        # Initialize settings
        self.init_default_settings()
        self.load_settings()
        
        # Processing state
        self.processing_videos = {}
        
        self._initialized = True

    def submit_feedback(self, detection_id, feedback_type, user_comment=None):
        """Submit feedback for a detection"""
        if not self.db_available:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            feedback_doc = {
                'detection_id': detection_id,
                'feedback_type': feedback_type,
                'user_comment': user_comment,
                'timestamp': datetime.now()
            }
            result = self.feedback_collection.insert_one(feedback_doc)
            return {'success': True, 'feedback_id': str(result.inserted_id)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # [Keep all other existing methods unchanged]
    def init_default_settings(self):
        """Initialize default model settings - FIX"""
        if not self.db_available:
            return
        
        try:
            if self.settings_collection.count_documents({}) == 0:
                default_settings = {
                    'confidence_threshold': 0.5,
                    'tracking_threshold': 0.3,
                    'movement_threshold': 50,
                    'frame_skip': 3,
                    'created_at': datetime.now()
                }
                self.settings_collection.insert_one(default_settings)
        except Exception as e:
            print(f"Error initializing settings: {e}")

    def load_settings(self):
        """Load current model settings - FIX"""
        try:
            if self.db_available:
                settings = self.settings_collection.find_one({}, sort=[('created_at', -1)])
                if settings:
                    self.confidence_threshold = settings.get('confidence_threshold', 0.5)
                    self.tracking_threshold = settings.get('tracking_threshold', 0.3)
                    self.movement_threshold = settings.get('movement_threshold', 50)
                    self.frame_skip = settings.get('frame_skip', 3)
                    return
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        self.confidence_threshold = 0.5
        self.tracking_threshold = 0.3
        self.movement_threshold = 50
        self.frame_skip = 3

    def process_video(self, video_path, filename, progress_callback=None):
        try:
            # Mark video as processing
            self.processing_videos[filename] = {
                'status': 'processing',
                'progress': 0,
                'start_time': datetime.now()
            }
            
            # Check if video already exists in DB
            video_id = None
            if self.db_available:
                existing_video = self.videos_collection.find_one({'filename': filename})
                if existing_video:
                    # Update existing video
                    video_id = existing_video['_id']
                    self.videos_collection.update_one(
                        {'_id': video_id},
                        {'$set': {
                            'status': 'processing',
                            'processed_at': None,
                            'pizza_count': 0,
                            'total_frames': 0,
                            'processed_frames': 0
                        }}
                    )
                else:
                    # Insert new video record
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
            
            # Process using original algorithm
            result = self.detect_and_count_pizzas_original(video_path, filename, progress_callback)
            
            # Update video record
            if self.db_available and video_id is not None:
                self.videos_collection.update_one(
                    {'_id': video_id},
                    {'$set': {
                        'status': 'completed',
                        'processed_at': datetime.now(),
                        'pizza_count': result['pizza_count'],
                        'total_frames': result.get('total_frames', 0),
                        'processed_frames': result.get('processed_frames', 0)
                    }}
                )
            
            # Update processing state
            self.processing_videos[filename] = {
                'status': 'completed',
                'progress': 100,
                'pizza_count': result['pizza_count'],
                'end_time': datetime.now()
            }
            
            return {
                'success': True,
                'pizza_count': result['pizza_count'],
                'total_frames': result.get('total_frames', 0),
                'detections': result.get('detections', [])
            }
            
        except Exception as e:
            if filename in self.processing_videos:
                self.processing_videos[filename]['status'] = 'error'
                self.processing_videos[filename]['error'] = str(e)
            
            if self.db_available and video_id is not None:
                self.videos_collection.update_one(
                    {'_id': video_id},
                    {'$set': {'status': 'error', 'error_message': str(e)}}
                )
            
            return {'success': False, 'error': str(e)}


    def detect_and_count_pizzas_original(self, video_path, filename, progress_callback=None):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception("Could not open video file")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_count = 0
        pizza_count = 0
        counted_pizzas = set()
        track_history = defaultdict(lambda: [])
        all_detections = []
        
        print(f"Processing video: {total_frames} frames")
        
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
            
            frame_count += 1
            
            # Update progress every 10 frames
            if progress_callback and frame_count % 10 == 0:
                progress = (frame_count / total_frames) * 100
                try:
                    progress_callback(progress)
                    if filename in self.processing_videos:
                        self.processing_videos[filename]["progress"] = progress
                except Exception as e:
                    print(f"Progress callback error: {e}")
            
            # Skip frames for performance
            if frame_count % self.frame_skip != 0:
                continue
                
            try:
                results = self.model.track(
                    frame,
                    persist=True,
                    classes=self.classes_to_detect,
                    conf=self.confidence_threshold,
                    tracker="bytetrack.yaml"
                )
                
                if (results[0].boxes is not None and 
                    results[0].boxes.id is not None and 
                    len(results[0].boxes.id) > 0):
                    
                    boxes = results[0].boxes.xywh.cpu()
                    track_ids = results[0].boxes.id.int().cpu().tolist()
                    confidences = results[0].boxes.conf.cpu().tolist()
                    classes = results[0].boxes.cls.int().cpu().tolist()
                    
                    # Process each tracked object
                    for box, track_id, conf, cls in zip(boxes, track_ids, confidences, classes):
                        if cls == self.pizza_class_id and conf > self.confidence_threshold:
                            x, y, w, h = box
                            center_x, center_y = float(x), float(y)
                            
                            # Track pizza movement history
                            track = track_history[track_id]
                            track.append((center_x, center_y, frame_count))
                            
                            # Keep only recent positions (last 2 seconds)
                            if len(track) > 60:
                                track.pop(0)
                            
                            # Check if pizza has been "removed" based on movement pattern
                            if len(track) > 20 and track_id not in counted_pizzas:
                                if self.is_pizza_removed_original(track):
                                    counted_pizzas.add(track_id)
                                    pizza_count += 1
                                    print(f"Pizza #{pizza_count} detected and counted (Track ID: {track_id})")
                                    
                                    # Save detection to database
                                    detection_data = {
                                        'track_id': track_id,
                                        'frame_count': frame_count,
                                        'confidence': conf,
                                        'position': {'x': center_x, 'y': center_y},
                                        'timestamp': datetime.now()
                                    }
                                    all_detections.append(detection_data)
                                    
                                    if self.db_available:
                                        self.save_detection_to_db(detection_data, video_path)
                            
            except Exception as e:
                print(f"Error in frame {frame_count}: {e}")
                continue
        
        # Final progress update
        if progress_callback:
            progress_callback(100)
        
        cap.release()
        print(f"Video processing complete: {pizza_count} pizzas counted")
        
        return {
            'pizza_count': pizza_count,
            'total_frames': total_frames,
            'processed_frames': frame_count,
            'detections': all_detections
    }


    def is_pizza_removed_original(self, track):
        """Determine if pizza has been removed based on MOVEMENT PATTERN"""
        if len(track) < 20:
            return False
        
        # Get initial and recent positions
        initial_positions = track[:10]
        recent_positions = track[-10:]
        
        # Calculate average positions
        initial_x = np.mean([pos[0] for pos in initial_positions])
        initial_y = np.mean([pos[1] for pos in initial_positions])
        recent_x = np.mean([pos[0] for pos in recent_positions])
        recent_y = np.mean([pos[1] for pos in recent_positions])
        
        # Calculate movement distance
        movement_distance = np.sqrt((recent_x - initial_x)**2 + (recent_y - initial_y)**2)
        
        # Check for significant upward movement (pizza being picked up)
        vertical_movement = initial_y - recent_y  # Negative Y is up in image coordinates
        
        # Pizza is considered "removed" if:
        # 1. Significant overall movement
        # 2. Upward movement (being picked up)
        # 3. Movement exceeds threshold
        return (movement_distance > self.movement_threshold and
                vertical_movement > 30 and
                movement_distance > 50)

    def save_detection_to_db(self, detection_data, video_path):
        """Save detection to MongoDB"""
        if not self.db_available:
            return
        
        try:
            detection_record = {
                'video_path': video_path,
                'filename': os.path.basename(video_path),
                'track_id': detection_data['track_id'],
                'frame_count': detection_data['frame_count'],
                'confidence': detection_data['confidence'],
                'position': detection_data['position'],
                'timestamp': detection_data['timestamp'],
                'class_id': self.pizza_class_id,
                'class_name': 'pizza'
            }
            self.detections_collection.insert_one(detection_record)
        except Exception as e:
            print(f"Error saving detection: {e}")

    def process_frame_for_stream(self, frame):
        """Process single frame for real-time streaming"""
        try:
            results = self.model(
                frame,
                classes=self.classes_to_detect,
                conf=self.confidence_threshold
            )
            
            detections = []
            annotated_frame = frame.copy()
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])
                        if cls == self.pizza_class_id and conf >= self.confidence_threshold:
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
            if not self.db_available:
                return {
                    'total_videos': 0,
                    'completed_videos': 0,
                    'processing_videos': 0,
                    'currently_processing': len([v for v in self.processing_videos.values() if v['status'] == 'processing']),
                    'total_detections': 0,
                    'recent_detections': 0,
                    'recent_videos': 0,
                    'avg_confidence': 0,
                    'accuracy_percentage': 0,
                    'feedback_count': 0,
                    'model_settings': self.get_model_settings()
                }
            
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
            
            # Currently processing count
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
            print(f"Error getting stats: {e}")
            return {
                'total_videos': 0,
                'completed_videos': 0,
                'processing_videos': 0,
                'currently_processing': 0,
                'total_detections': 0,
                'recent_detections': 0,
                'recent_videos': 0,
                'avg_confidence': 0,
                'accuracy_percentage': 0,
                'feedback_count': 0,
                'model_settings': self.get_model_settings(),
                'error': str(e)
            }

    def get_video_info(self, filename):
        """Get information about a specific video"""
        try:
            if not self.db_available:
                if filename in self.processing_videos:
                    return self.processing_videos[filename]
                return {'status': 'not_found'}
            
            video_doc = self.videos_collection.find_one({'filename': filename})
            if video_doc:
                video_doc['_id'] = str(video_doc['_id'])
                return video_doc
            
            if filename in self.processing_videos:
                return self.processing_videos[filename]
            
            return {'status': 'not_found'}
        except Exception as e:
            return {'error': str(e)}

    def get_model_settings(self):
        """Get current model settings"""
        return {
            'confidence_threshold': self.confidence_threshold,
            'tracking_threshold': self.tracking_threshold,
            'movement_threshold': self.movement_threshold,
            'frame_skip': self.frame_skip
        }

    def update_confidence_threshold(self, threshold):
        """Update confidence threshold"""
        self.confidence_threshold = threshold
        if self.db_available:
            try:
                settings_data = {
                    'confidence_threshold': threshold,
                    'tracking_threshold': self.tracking_threshold,
                    'movement_threshold': self.movement_threshold,
                    'frame_skip': self.frame_skip,
                    'created_at': datetime.now()
                }
                self.settings_collection.insert_one(settings_data)
            except Exception as e:
                print(f"Error updating settings: {e}")

    def get_analytics_data(self, start_date, end_date):
        """Get analytics data for specified date range"""
        try:
            if not self.db_available:
                return {
                    'total_detections': 0,
                    'daily_detections': [],
                    'confidence_distribution': [],
                    'avg_confidence': 0,
                    'videos_processed': 0,
                    'model_accuracy': 0,
                    'detection_log': []
                }
            
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            # Total detections in range
            total_detections = self.detections_collection.count_documents({
                'timestamp': {'$gte': start_datetime, '$lte': end_datetime}
            })
            
            # Daily detection counts
            daily_pipeline = [
                {'$match': {'timestamp': {'$gte': start_datetime, '$lte': end_datetime}}},
                {'$group': {
                    '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$timestamp'}},
                    'count': {'$sum': 1}
                }},
                {'$sort': {'_id': 1}}
            ]
            daily_detections = list(self.detections_collection.aggregate(daily_pipeline))
            daily_data = [{'date': item['_id'], 'count': item['count']} for item in daily_detections]
            
            # Confidence distribution
            confidence_data = list(self.detections_collection.find(
                {'timestamp': {'$gte': start_datetime, '$lte': end_datetime}},
                {'confidence': 1}
            ))
            
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
            
            return {
                'total_detections': total_detections,
                'daily_detections': daily_data,
                'confidence_distribution': confidence_data,
                'avg_confidence': avg_confidence,
                'videos_processed': videos_processed,
                'model_accuracy': model_accuracy,
                'detection_log': detection_log
            }
            
        except Exception as e:
            return {'error': str(e)}

    def get_processing_status(self, filename):
        """Get processing status for a specific video"""
        if filename in self.processing_videos:
            return self.processing_videos[filename]
        
        if self.db_available:
            video_doc = self.videos_collection.find_one({'filename': filename})
            if video_doc:
                return {
                    'status': video_doc['status'],
                    'progress': 100 if video_doc['status'] == 'completed' else 0,
                    'pizza_count': video_doc.get('pizza_count', 0)
                }
        
        return {'status': 'not_found'}
