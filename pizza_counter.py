import cv2
import os
import numpy as np
from ultralytics import YOLO
from pymongo import MongoClient
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()


class PizzaCounter:
    def __init__(self, model_path="./models/yolo11n.pt", mongodb_uri=os.getenv("MONGODB_URI")):
        """Initialize pizza counter with YOLO model and MongoDB connection"""
        if model_path is None:
            # Download model at runtime
            model_path = "./models/yolo11n.pt"
            if not os.path.exists(model_path):
                print("Downloading YOLO model...")
        self.model = YOLO(model_path)
        
        # COCO dataset class IDs - pizza is class 53
        self.pizza_class_id = 53
        self.classes_to_detect = [self.pizza_class_id]  # Only detect pizza
        
        self.client = MongoClient(mongodb_uri)
        self.db = self.client.pizza_detection
        
        # Collections
        self.detections_collection = self.db.detections
        self.feedback_collection = self.db.feedback
        self.videos_collection = self.db.videos
        self.settings_collection = self.db.settings
        
        # Initialize default settings
        self.init_default_settings()
        
        # Load current settings
        self.load_settings()
        
        # Tracking variables
        self.track_history = defaultdict(lambda: [])
        self.counted_pizzas = set()

    def init_default_settings(self):
        """Initialize default model settings"""
        if self.settings_collection.count_documents({}) == 0:
            default_settings = {
                'confidence_threshold': 0.5,
                'tracking_threshold': 0.3,
                'movement_threshold': 50,
                'created_at': datetime.now()
            }
            self.settings_collection.insert_one(default_settings)

    def load_settings(self):
        """Load current model settings"""
        settings = self.settings_collection.find_one({}, sort=[('created_at', -1)])
        if settings:
            self.confidence_threshold = settings.get('confidence_threshold', 0.5)
            self.tracking_threshold = settings.get('tracking_threshold', 0.3)
            self.movement_threshold = settings.get('movement_threshold', 50)
        else:
            self.confidence_threshold = 0.5
            self.tracking_threshold = 0.3
            self.movement_threshold = 50

    def detect_and_count_pizzas(self, video_path):
        """Process video and count pizzas"""
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        pizza_count = 0
        counted_pizzas = set()
        track_history = defaultdict(lambda: [])

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            frame_count += 1
            
            # Run YOLO tracking on the frame - only detect pizza class
            results = self.model.track(
                frame, 
                persist=True, 
                classes=self.classes_to_detect,  # Only detect pizza
                conf=self.confidence_threshold
            )

            if results[0].boxes is not None:
                boxes = results[0].boxes.xywh.cpu()
                track_ids = results[0].boxes.id.int().cpu().tolist() if results[0].boxes.id is not None else []
                confidences = results[0].boxes.conf.cpu().tolist()
                classes = results[0].boxes.cls.int().cpu().tolist()

                # Process each detection
                for box, track_id, conf, cls in zip(boxes, track_ids, confidences, classes):
                    # Double check it's pizza class
                    if cls == self.pizza_class_id and conf > self.confidence_threshold:
                        x, y, w, h = box
                        
                        # Track pizza movement
                        track = track_history[track_id]
                        track.append((float(x), float(y)))
                        
                        # Keep only recent positions
                        if len(track) > 30:
                            track.pop(0)

                        # Count pizza if it shows movement pattern
                        if len(track) > 10 and track_id not in counted_pizzas:
                            if self.is_pizza_removed(track):
                                counted_pizzas.add(track_id)
                                pizza_count += 1
                                
                                # Save detection to database
                                self.save_detection(track_id, frame_count, conf, video_path)

        cap.release()
        cv2.destroyAllWindows()
        
        return pizza_count

    def detect_frame_demo(self, frame):
        """Detect pizzas in single frame for demo streaming"""
        try:
            # Resize frame if too large to improve performance
            height, width = frame.shape[:2]
            if width > 1280:
                scale = 1280 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))
            
            # Run detection with only pizza class
            results = self.model(
                frame, 
                verbose=False,
                classes=self.classes_to_detect,  # Only detect pizza
                conf=self.confidence_threshold
            )
            
            # Custom annotation for pizza only
            annotated_frame = frame.copy()
            
            if results[0].boxes is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                confidences = results[0].boxes.conf.cpu().numpy()
                classes = results[0].boxes.cls.int().cpu().numpy()
                
                for box, conf, cls in zip(boxes, confidences, classes):
                    if cls == self.pizza_class_id:  # Only draw pizza boxes
                        x1, y1, x2, y2 = box.astype(int)
                        
                        # Draw bounding box
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        
                        # Draw label
                        label = f"Pizza {conf:.2f}"
                        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                        
                        # Background for label
                        cv2.rectangle(annotated_frame, 
                                    (x1, y1 - label_size[1] - 10), 
                                    (x1 + label_size[0], y1), 
                                    (0, 255, 0), -1)
                        
                        # Label text
                        cv2.putText(annotated_frame, label, (x1, y1 - 5), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            
            # Add demo watermark
            cv2.putText(annotated_frame, "PIZZA DETECTION DEMO", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
            # Add detection info
            pizza_count = len(results[0].boxes) if results[0].boxes is not None else 0
            cv2.putText(annotated_frame, f"Pizzas detected: {pizza_count}", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add frame info
            cv2.putText(annotated_frame, f"Size: {annotated_frame.shape[1]}x{annotated_frame.shape[0]}", 
                       (10, annotated_frame.shape[0] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            return annotated_frame
            
        except Exception as e:
            print(f"Detection error: {e}")
            # Return original frame if detection fails
            return frame

    def is_pizza_removed(self, track):
        """Determine if pizza has been removed based on movement"""
        if len(track) < 10:
            return False

        # Calculate movement in Y direction
        start_y = np.mean([pos[1] for pos in track[:5]])
        end_y = np.mean([pos[1] for pos in track[-5:]])
        
        return abs(end_y - start_y) > self.movement_threshold

    def save_detection(self, track_id, frame_count, confidence, video_path):
        """Save detection to MongoDB"""
        detection_data = {
            "track_id": track_id,
            "frame_count": frame_count,
            "confidence": confidence,
            "video_path": video_path,
            "timestamp": datetime.now(),
            "user_feedback": None,
            "feedback_timestamp": None
        }
        self.detections_collection.insert_one(detection_data)

    def update_video_status(self, filename, status, pizza_count=0):
        """Update video processing status"""
        video_data = {
            "filename": filename,
            "status": status,
            "pizza_count": pizza_count,
            "updated_at": datetime.now()
        }
        
        self.videos_collection.update_one(
            {"filename": filename},
            {"$set": video_data},
            upsert=True
        )

    def get_video_info(self, filename):
        """Get video information from database"""
        video_info = self.videos_collection.find_one({"filename": filename})
        if video_info:
            return {
                "status": video_info.get("status", "pending"),
                "pizza_count": video_info.get("pizza_count", 0),
                "processed_at": video_info.get("updated_at")
            }
        return {"status": "pending", "pizza_count": 0, "processed_at": None}

    def get_comprehensive_stats(self):
        """Get comprehensive statistics for dashboard"""
        # Total pizzas detected
        total_pizzas = self.detections_collection.count_documents({})
        
        # Today's count
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_pizzas = self.detections_collection.count_documents({
            "timestamp": {"$gte": today_start}
        })
        
        # Processing videos count
        processing_videos = self.videos_collection.count_documents({"status": "processing"})
        
        # Model accuracy
        total_feedback = self.feedback_collection.count_documents({})
        correct_feedback = self.feedback_collection.count_documents({"is_correct": True})
        accuracy = (correct_feedback / total_feedback * 100) if total_feedback > 0 else 0
        
        # Recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_detections = list(self.detections_collection.find({
            "timestamp": {"$gte": week_ago}
        }).sort("timestamp", -1).limit(10))
        
        # Convert ObjectId to string for JSON serialization
        for detection in recent_detections:
            detection['_id'] = str(detection['_id'])
            
        return {
            "total_pizzas": total_pizzas,
            "today_pizzas": today_pizzas,
            "processing_videos": processing_videos,
            "accuracy_percentage": round(accuracy, 1),
            "confidence_threshold": self.confidence_threshold,
            "recent_detections": recent_detections
        }

    def add_user_feedback(self, track_id, is_correct, confidence_adjustment=0):
        """Add user feedback for model improvement"""
        feedback_data = {
            "track_id": track_id,
            "is_correct": is_correct,
            "confidence_adjustment": confidence_adjustment,
            "timestamp": datetime.now()
        }
        self.feedback_collection.insert_one(feedback_data)

    def update_detection_feedback(self, track_id, is_correct):
        """Update detection record with user feedback"""
        self.detections_collection.update_one(
            {"track_id": track_id},
            {"$set": {
                "user_feedback": is_correct,
                "feedback_timestamp": datetime.now()
            }}
        )

    def refine_model_accuracy(self):
        """Refine model accuracy based on user feedback"""
        # Get recent feedback statistics
        recent_feedback = list(self.feedback_collection.find().sort("timestamp", -1).limit(100))
        
        if len(recent_feedback) < 10:
            return  # Need more feedback data
        
        correct_count = sum(1 for f in recent_feedback if f['is_correct'])
        accuracy_rate = correct_count / len(recent_feedback)
        
        # Adjust confidence threshold based on feedback
        if accuracy_rate < 0.7:  # Low accuracy, increase threshold
            new_threshold = min(0.9, self.confidence_threshold + 0.05)
        elif accuracy_rate > 0.9:  # High accuracy, decrease threshold
            new_threshold = max(0.2, self.confidence_threshold - 0.02)
        else:
            new_threshold = self.confidence_threshold
        
        # Update threshold if changed
        if new_threshold != self.confidence_threshold:
            self.update_confidence_threshold(new_threshold)
            print(f"Model threshold adjusted: {self.confidence_threshold:.2f} -> {new_threshold:.2f}")

    def update_confidence_threshold(self, new_threshold):
        """Update confidence threshold"""
        self.confidence_threshold = new_threshold
        
        # Save to database
        settings_data = {
            'confidence_threshold': new_threshold,
            'tracking_threshold': self.tracking_threshold,
            'movement_threshold': self.movement_threshold,
            'created_at': datetime.now()
        }
        self.settings_collection.insert_one(settings_data)

    def get_recent_detections(self):
        """Get recent detections for feedback"""
        detections = list(self.detections_collection.find({
            "user_feedback": None
        }).sort('timestamp', -1).limit(20))
        
        # Convert ObjectId to string for JSON serialization
        for detection in detections:
            detection['_id'] = str(detection['_id'])
            
        return detections

    def get_model_settings(self):
        """Get current model settings"""
        return {
            "confidence_threshold": self.confidence_threshold,
            "tracking_threshold": self.tracking_threshold,
            "movement_threshold": self.movement_threshold
        }

    def get_available_classes(self):
        """Get list of available classes in the model"""
        return self.model.names

    def print_class_info(self):
        """Print information about classes"""
        class_names = self.get_available_classes()
        print("Available classes:")
        for class_id, class_name in class_names.items():
            print(f"  {class_id}: {class_name}")
        
        print(f"\nCurrently detecting: {[class_names[cls] for cls in self.classes_to_detect]}")

    def set_detection_classes(self, class_names_or_ids):
        """Set which classes to detect"""
        if isinstance(class_names_or_ids[0], str):
            # Convert class names to IDs
            available_classes = self.get_available_classes()
            name_to_id = {name: id for id, name in available_classes.items()}
            self.classes_to_detect = [name_to_id[name] for name in class_names_or_ids if name in name_to_id]
        else:
            # Direct class IDs
            self.classes_to_detect = class_names_or_ids
        
        print(f"Detection classes updated: {self.classes_to_detect}")

if __name__ == "__main__":
    counter = PizzaCounter()
    print("Pizza Counter initialized successfully")
    counter.print_class_info()
