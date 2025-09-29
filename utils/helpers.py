import os
import streamlit as st
from datetime import datetime, timedelta
import cv2
from PIL import Image
import io

# Allowed video file extensions
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def format_time_ago(timestamp):
    """Format timestamp as 'time ago' string"""
    if not timestamp:
        return "Unknown"
    
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

def get_status_color(status):
    """Get color for status display"""
    status_colors = {
        'completed': 'green',
        'processing': 'orange',
        'error': 'red',
        'pending': 'gray',
        'uploading': 'blue'
    }
    return status_colors.get(status.lower(), 'gray')

def get_status_icon(status):
    """Get icon for status display"""
    status_icons = {
        'completed': '✅',
        'processing': '⏳',
        'error': '❌',
        'pending': '⏸️',
        'uploading': '📤'
    }
    return status_icons.get(status.lower(), '❓')

def validate_video_file(uploaded_file):
    """Validate uploaded video file"""
    if not uploaded_file:
        return False, "No file uploaded"
    
    if not allowed_file(uploaded_file.name):
        return False, f"File type not supported. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check file size (max 500MB by default)
    max_size = 500 * 1024 * 1024  # 500MB in bytes
    if uploaded_file.size > max_size:
        return False, f"File size too large. Maximum allowed: {format_file_size(max_size)}"
    
    return True, "File is valid"

def save_uploaded_file(uploaded_file, upload_folder="./videos"):
    """Save uploaded file to specified folder"""
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Generate unique filename to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{uploaded_file.name}"
    file_path = os.path.join(upload_folder, filename)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path, filename

def extract_video_thumbnail(video_path):
    """Extract thumbnail from video"""
    try:
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Convert to PIL Image
            pil_image = Image.fromarray(frame_rgb)
            return pil_image
        else:
            return None
    except Exception:
        return None

def get_video_info(video_path):
    """Get basic video information"""
    try:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return None
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        cap.release()
        
        return {
            'fps': fps,
            'frame_count': frame_count,
            'duration': duration,
            'width': width,
            'height': height,
            'resolution': f"{width}x{height}"
        }
    except Exception:
        return None

def format_duration(seconds):
    """Format duration in seconds to readable format"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}m {seconds}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def create_progress_bar_html(progress, color="blue"):
    """Create HTML progress bar"""
    return f"""
    <div style="background-color: #f0f0f0; border-radius: 10px; padding: 2px; width: 100%; margin: 5px 0;">
        <div style="background-color: {color}; width: {progress}%; height: 20px; border-radius: 8px; 
                    display: flex; align-items: center; justify-content: center; color: white; font-size: 12px;">
            {int(progress)}%
        </div>
    </div>
    """

def display_metric_card(title, value, delta=None, color="blue"):
    """Display a metric card with styling"""
    delta_html = ""
    if delta is not None:
        delta_color = "green" if delta >= 0 else "red"
        delta_symbol = "▲" if delta >= 0 else "▼"
        delta_html = f'<div style="color: {delta_color}; font-size: 0.8em;">{delta_symbol} {abs(delta)}</div>'
    
    return f"""
    <div style="background: linear-gradient(135deg, {color}, rgba({color}, 0.8)); 
                border-radius: 10px; padding: 20px; margin: 10px 0; color: white; text-align: center;">
        <div style="font-size: 0.9em; opacity: 0.9;">{title}</div>
        <div style="font-size: 2em; font-weight: bold; margin: 10px 0;">{value}</div>
        {delta_html}
    </div>
    """

def show_toast(message, toast_type="info"):
    """Show toast notification"""
    toast_colors = {
        "success": "#4CAF50",
        "error": "#f44336",
        "warning": "#ff9800",
        "info": "#2196F3"
    }
    
    color = toast_colors.get(toast_type, "#2196F3")
    
    st.markdown(f"""
    <div style="background-color: {color}; color: white; padding: 10px; border-radius: 5px; margin: 10px 0;">
        {message}
    </div>
    """, unsafe_allow_html=True)

def convert_cv2_to_pil(cv2_image):
    """Convert OpenCV image to PIL Image"""
    rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb_image)

def convert_pil_to_bytes(pil_image):
    """Convert PIL Image to bytes"""
    img_buffer = io.BytesIO()
    pil_image.save(img_buffer, format='JPEG')
    img_bytes = img_buffer.getvalue()
    return img_bytes

def is_processing_complete(processing_status):
    """Check if video processing is complete"""
    return processing_status.get('status') in ['completed', 'error']

def get_available_classes():
    """Get available detection classes"""
    # COCO dataset classes relevant for food detection
    return {
        53: 'pizza',
        47: 'cup',
        46: 'wine glass',
        50: 'spoon',
        51: 'bowl',
        52: 'banana',
        54: 'donut',
        55: 'cake',
        56: 'chair',
        57: 'couch',
        58: 'potted plant',
        59: 'bed',
        60: 'dining table'
    }

def cleanup_old_files(folder_path, max_age_days=30):
    """Clean up old files in specified folder"""
    try:
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(days=max_age_days)
        
        deleted_count = 0
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
        
        return deleted_count
    except Exception as e:
        return 0

def ensure_directory_exists(directory_path):
    """Ensure directory exists, create if it doesn't"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        return True
    return False

def safe_get_date(date_value, default=None):
    """Safely convert date value to datetime object"""
    if date_value is None:
        return default or datetime.min
    
    if isinstance(date_value, datetime):
        return date_value
    
    if isinstance(date_value, str):
        try:
            # Try ISO format
            return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try standard format
                return datetime.strptime(date_value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return default or datetime.min
    
    return default or datetime.min

def safe_sort_by_date(items, date_key='processed_at', reverse=True):
    """Safely sort items by date field"""
    def get_date(item):
        date_val = item.get(date_key)
        return safe_get_date(date_val, datetime.min)
    
    return sorted(items, key=get_date, reverse=reverse)