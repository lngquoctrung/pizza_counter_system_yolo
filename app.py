from flask import Flask, render_template, jsonify, request, Response
from werkzeug.utils import secure_filename
from pizza_counter import PizzaCounter
import threading
import os
import cv2
import json
from datetime import datetime

app = Flask(__name__)

# Upload configuration
UPLOAD_FOLDER = './videos'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create videos folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

counter = PizzaCounter()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    """Get comprehensive statistics"""
    stats = counter.get_comprehensive_stats()
    return jsonify(stats)

@app.route('/api/upload_video', methods=['POST'])
def upload_video():
    """Upload video file and auto-process"""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file selected'}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(video_path)

        # Auto-process video in background
        def process_video_background():
            try:
                result = counter.detect_and_count_pizzas(video_path)
                counter.update_video_status(filename, 'completed', result)
                print(f"Video processing completed: {result} pizzas detected")
            except Exception as e:
                counter.update_video_status(filename, 'error', 0)
                print(f"Error processing video: {str(e)}")

        # Mark video as processing
        counter.update_video_status(filename, 'processing', 0)
        
        thread = threading.Thread(target=process_video_background)
        thread.daemon = True
        thread.start()

        return jsonify({
            'message': 'Video uploaded and processing started',
            'video_path': video_path,
            'filename': filename
        })

    return jsonify({'error': 'File format not supported'}), 400

@app.route('/api/videos')
def list_videos():
    """List all videos with processing status"""
    try:
        video_files = []
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if allowed_file(filename):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file_size = os.path.getsize(file_path)
                
                # Get video status from database
                video_info = counter.get_video_info(filename)
                
                video_files.append({
                    'filename': filename,
                    'path': file_path,
                    'size': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'status': video_info.get('status', 'pending'),
                    'pizza_count': video_info.get('pizza_count', 0),
                    'processed_at': video_info.get('processed_at')
                })

        return jsonify({'videos': video_files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stream_video/<filename>')
def stream_video(filename):
    """Stream video with real-time pizza detection (demo mode)"""
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(video_path):
        return jsonify({'error': 'Video file not found'}), 404

    def generate_frames():
        cap = cv2.VideoCapture(video_path)
        
        try:
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    break

                # Run detection on frame (demo mode - no database updates)
                try:
                    annotated_frame = counter.detect_frame_demo(frame)
                    
                    # Encode frame to JPEG
                    ret, buffer = cv2.imencode('.jpg', annotated_frame)
                    if not ret:
                        break
                        
                    frame_bytes = buffer.tobytes()
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                           
                except GeneratorExit:
                    # Client disconnected, stop streaming
                    break
                except Exception as e:
                    print(f"Frame processing error: {e}")
                    break
                    
        except Exception as e:
            print(f"Stream error: {e}")
        finally:
            cap.release()
            print(f"Stream closed for {filename}")

    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Submit user feedback and update model accuracy"""
    track_id = request.json.get('track_id')
    is_correct = request.json.get('is_correct')
    confidence_adjustment = request.json.get('confidence_adjustment', 0)

    # Add feedback to database
    counter.add_user_feedback(track_id, is_correct, confidence_adjustment)

    # Update detection record with feedback
    counter.update_detection_feedback(track_id, is_correct)

    # Refine model accuracy based on feedback
    counter.refine_model_accuracy()

    return jsonify({'message': 'Feedback submitted and model updated'})

@app.route('/api/detections')
def get_detections():
    """Get recent detections for feedback"""
    detections = counter.get_recent_detections()
    return jsonify(detections)

@app.route('/api/model_settings', methods=['GET', 'POST'])
def model_settings():
    """Get or update model settings"""
    if request.method == 'GET':
        settings = counter.get_model_settings()
        return jsonify(settings)
    
    elif request.method == 'POST':
        new_threshold = request.json.get('confidence_threshold')
        if new_threshold:
            counter.update_confidence_threshold(new_threshold)
            return jsonify({'message': 'Model settings updated'})
        
        return jsonify({'error': 'Invalid parameters'}), 400

@app.route('/api/detection_classes', methods=['GET', 'POST'])
def detection_classes():
    """Get or update detection classes"""
    if request.method == 'GET':
        available_classes = counter.get_available_classes()
        current_classes = counter.classes_to_detect
        
        return jsonify({
            'available_classes': available_classes,
            'current_classes': current_classes,
            'current_class_names': [available_classes[cls] for cls in current_classes]
        })
    
    elif request.method == 'POST':
        new_classes = request.json.get('classes', [])
        if new_classes:
            counter.set_detection_classes(new_classes)
            return jsonify({'message': 'Detection classes updated successfully'})
        
        return jsonify({'error': 'No classes specified'}), 400

@app.route('/health-check')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
