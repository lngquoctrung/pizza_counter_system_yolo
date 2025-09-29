# Pizza Detection System 🍕

An advanced pizza detection and counting system using YOLO11 and Streamlit. This system automatically detects, tracks, and counts pizzas in videos using state-of-the-art computer vision technology with an intuitive web interface.

## 🚀 Key Features

### Core Functionality
* **Intelligent Pizza Detection**: Uses YOLO11 with advanced tracking algorithms for accurate pizza detection
* **Real-time Video Processing**: Process videos with live progress tracking
* **Smart Counting Algorithm**: Advanced tracking system prevents double-counting pizzas
* **Real-time Detection Stream**: Live detection visualization with bounding boxes
* **Video Library Management**: Comprehensive video management with thumbnails and metadata

### User Interface
* **Modern Dashboard**: Beautiful, responsive interface with real-time statistics
* **Multi-page Navigation**: Dashboard, Video Library, Analytics, and Settings pages
* **Interactive Feedback System**: Rate detection accuracy to improve model performance
* **Progress Tracking**: Real-time processing progress with visual indicators
* **Responsive Design**: Works perfectly on desktop and mobile devices

### Advanced Features
* **Database Integration**: MongoDB for persistent storage of detections and feedback
* **Analytics Dashboard**: Comprehensive charts and statistics
* **Model Configuration**: Adjustable confidence thresholds and detection parameters
* **Export/Import Settings**: Backup and restore system configurations
* **Error Recovery**: Automatic handling of processing failures and restarts

## 📁 Project Structure

```bash
pizza_detection_system/
├── app.py                          # Main Streamlit application
├── assets/
│   └── style.css                   # Custom CSS styling
├── components/                     # UI components
│   ├── recent_detections.py        # Recent detections widget
│   ├── stats_cards.py              # Statistics cards
│   ├── video_card.py               # Video library cards
│   ├── video_stream.py             # Video streaming component
│   └── video_upload.py             # Video upload interface
├── pages/                          # Application pages
│   ├── analytics.py                # Analytics dashboard
│   ├── dashboard.py                # Main dashboard
│   ├── settings.py                 # Settings page
│   └── video_library.py            # Video library page
├── utils/                          # Utility functions
│   ├── helpers.py                  # Helper functions
│   └── pizza_counter.py            # Core detection logic
├── models/
│   └── yolo11n.pt                  # YOLO11 model file
├── videos/                         # Processed videos storage
├── docker-compose.yml              # Docker compose configuration
├── Dockerfile                      # Docker configuration
├── requirements.txt                # Python dependencies
└── README.md                       # Project documentation
```

## 🛠 Technologies Used

### Backend & AI
* **Framework**: Streamlit (Python web framework)
* **AI/ML**: YOLO11 (Ultralytics) with ByteTrack tracking
* **Computer Vision**: OpenCV for video processing
* **Database**: MongoDB with PyMongo driver
* **Environment**: Python-dotenv for configuration

### Frontend & UI
* **Styling**: Custom CSS with modern design
* **Navigation**: Streamlit-option-menu for horizontal navigation
* **Visualization**: Plotly for interactive charts and graphs
* **Icons**: Font Awesome integration

### Infrastructure
* **Containerization**: Docker & Docker Compose
* **Database**: MongoDB with persistent storage
* **File Handling**: Efficient video processing and thumbnail generation

## ⚙️ System Requirements

### Minimum Requirements
* **CPU**: Intel i5 or AMD Ryzen 5 (4 cores)
* **RAM**: 8GB (16GB recommended for large videos)
* **Storage**: 20GB free space
* **Python**: 3.9+ (3.11 recommended)

### Recommended Requirements
* **CPU**: Intel i7 or AMD Ryzen 7 (8 cores)
* **RAM**: 16GB or more
* **GPU**: NVIDIA GPU with CUDA support (optional, for faster processing)
* **Storage**: SSD with 50GB+ free space

## 🐳 Installation

### Quick Start with Docker (Recommended)

1. **Clone the repository**:
```bash
git clone <repository-url>
cd pizza_detection_system
```

2. **Start with Docker Compose**:
```bash
docker-compose up --build

# For background mode
docker-compose up -d --build
```

3. **Access the application**: 
   - Open [http://localhost:8501](http://localhost:8501)
   - Dashboard will load automatically

### Manual Installation

1. **Install Python 3.9+**
   ```bash
   python --version  # Should be 3.9 or higher
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   
   # Activate (Linux/Mac)
   source venv/bin/activate
   
   # Activate (Windows)
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment**:
   Create `.streamlit/secrets.toml`:
   ```toml
   MONGODB_URI = "mongodb://admin:password123@localhost:27017/pizza_detection?authSource=admin"
   ```

5. **Create required directories**:
   ```bash
   mkdir -p models videos thumbnails
   ```

6. **Download YOLO11 model** (automatic on first run):
   ```bash
   # Model will be downloaded automatically to models/yolo11n.pt
   ```

7. **Start MongoDB**:
   ```bash
   docker run -d -p 27017:27017 --name mongodb \
     -e MONGO_INITDB_ROOT_USERNAME=admin \
     -e MONGO_INITDB_ROOT_PASSWORD=password123 \
     mongo:latest
   ```

8. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## 📖 Usage Guide

### 1. 🏠 Dashboard
* **System Statistics**: View total videos, detections, and model accuracy
* **Upload Videos**: Drag & drop or browse to upload videos (MP4, AVI, MOV, MKV, WEBM, FLV)
* **Recent Detections**: See latest pizza detections with feedback options
* **Progress Tracking**: Monitor video processing in real-time

### 2. 🎬 Video Library
* **Video Management**: View all processed videos with thumbnails
* **Search & Filter**: Find videos by name, status, or upload date
* **Video Actions**:
  - **View**: Simple video player
  - **Stream**: Real-time detection with bounding boxes
  - **Details**: Comprehensive video statistics
  - **Delete**: Remove videos and associated data

### 3. 📊 Analytics
* **Detection Trends**: Daily detection charts
* **Confidence Distribution**: Model confidence analysis
* **Performance Metrics**: Processing speed and accuracy stats
* **Custom Date Ranges**: Filter analytics by specific periods

### 4. ⚙️ Settings
* **Model Configuration**:
  - Confidence threshold adjustment
  - Tracking parameters
  - Frame processing settings
* **Detection Classes**: Manage which objects to detect
* **Database Management**: Export/import settings
* **System Health**: Monitor database connection and model status

### 5. 🔄 Real-time Detection Stream
* **Live Processing**: See detection happen in real-time
* **Bounding Boxes**: Visual indicators around detected pizzas
* **Statistics**: Frame-by-frame detection counts
* **Performance Control**: Start/stop streaming as needed

## 🎯 Detection Algorithm

### Advanced Tracking System
The system uses a sophisticated multi-step process:

1. **YOLO11 Detection**: Identifies potential pizzas in each frame
2. **ByteTrack Tracking**: Maintains object identity across frames
3. **Movement Analysis**: Analyzes pizza movement patterns
4. **Smart Counting**: Only counts pizzas that show removal patterns
5. **Confidence Filtering**: Applies configurable confidence thresholds

### Counting Logic
* **Unique Tracking**: Each pizza gets a unique ID
* **Movement Detection**: Tracks upward movement (pizza removal)
* **Distance Thresholds**: Configurable movement sensitivity
* **Anti-Double-Counting**: Prevents counting the same pizza multiple times

## 🔧 Configuration

### Model Settings (Adjustable via Settings page)
```python
CONFIDENCE_THRESHOLD = 0.5      # Detection confidence (0.1-0.9)
TRACKING_THRESHOLD = 0.3        # Tracking confidence
MOVEMENT_THRESHOLD = 50         # Movement distance in pixels
FRAME_SKIP = 3                  # Process every N frames
PIZZA_CLASS_ID = 53             # COCO dataset pizza class
```

### Database Collections
* **detections**: Individual pizza detection records
* **feedback**: User feedback for model improvement
* **videos**: Video processing metadata and status
* **settings**: Model configuration and parameters

## 🚨 Troubleshooting

### Common Issues & Solutions

1. **MongoDB Connection Failed**:
   ```bash
   # Check if MongoDB is running
   docker ps | grep mongo
   
   # Restart MongoDB container
   docker restart mongodb
   ```

2. **Video Upload Fails**:
   - Check file format (supported: MP4, AVI, MOV, MKV, WEBM, FLV)
   - Ensure file size < 200MB
   - Verify sufficient disk space

3. **Detection Stream Freezes**:
   - Stop and restart the stream
   - Check if video file exists in videos/ directory
   - Verify video file is not corrupted

4. **Model Loading Error**:
   ```bash
   # Verify model file exists
   ls -la models/yolo11n.pt
   
   # Re-download if missing (automatic)
   rm models/yolo11n.pt
   # Restart app - model will be downloaded
   ```

5. **Poor Detection Accuracy**:
   - Adjust confidence threshold in Settings
   - Provide feedback on detections to improve model
   - Check video quality and lighting conditions

### Performance Optimization

* **GPU Acceleration**: Install CUDA for faster processing
* **Memory Management**: Close unused applications during processing
* **Video Optimization**: Use 720p resolution for best performance/accuracy balance
* **Database Indexing**: MongoDB automatically indexes for better performance

## 🔒 Security & Privacy

* **Local Processing**: All video processing happens locally
* **No Data Collection**: No personal data is sent to external servers
* **Secure Database**: MongoDB with authentication enabled
* **File Validation**: Comprehensive file type and size validation

## 🚀 Development

### Code Architecture
* **Modular Design**: Separate components for different functionalities
* **Singleton Pattern**: Efficient resource management for AI model
* **Async Processing**: Background video processing with progress updates
* **Error Handling**: Comprehensive error recovery and user feedback

### Extending the System
1. **Add New Detection Classes**: Modify `pizza_counter.py`
2. **Custom UI Components**: Create new components in `components/`
3. **Additional Pages**: Add new pages in `pages/`
4. **API Integration**: Extend functionality in individual page files

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 API Reference

### Internal Functions
```python
# Core detection
counter.process_video(video_path, filename, progress_callback)
counter.process_frame_for_stream(frame)

# Database operations
counter.submit_feedback(detection_id, feedback_type)
counter.get_analytics_data(start_date, end_date)

# Settings management
counter.update_confidence_threshold(threshold)
counter.get_model_settings()
```

## 📊 Performance Metrics

### Typical Performance
* **Processing Speed**: 15-30 FPS (depending on hardware)
* **Detection Accuracy**: 85-95% (with proper feedback)
* **Memory Usage**: 2-4GB RAM during processing
* **Disk Usage**: ~2-3x video file size for thumbnails and metadata

## 🆕 Version History

### v2.0.0 (Current) - September 2025
* **New**: Streamlit-based modern UI
* **New**: Real-time detection streaming
* **New**: Advanced tracking algorithm
* **New**: Comprehensive analytics dashboard
* **New**: MongoDB integration
* **Improved**: Better video processing pipeline
* **Improved**: Enhanced user experience

### v1.0.0 - June 2025
* Initial Flask-based implementation
* Basic pizza detection functionality
* Simple web interface

## 👨‍💻 Support & Contact

* **Version**: 2.0.0
* **Last Updated**: September 30, 2025
* **Framework**: Streamlit + YOLO11
* **Author**: Ly Nguyen Quoc Trung

### Getting Help
1. Check this README for common solutions
2. Review the troubleshooting section
3. Check system requirements and configuration
4. For custom implementations, review the code documentation

***

**🍕 Happy Pizza Detecting! 🍕**

*This system is designed to be both powerful and easy to use. Whether you're monitoring a pizza production line or just curious about pizza detection technology, this system provides accurate, real-time results with a beautiful interface.*

[1](https://mygpt.vn/cao-bach-llama-2-mo-hinh-nen-tang-mo-va-tinh-chinh-cho-chat/)
[2](https://huggingface.co/datasets/5CD-AI/Vietnamese-Locutusque-function-calling-chatml-gg-translated)
[3](https://thigiacmaytinh.com/huong-dan-viet-file-markdown-readme-md/)
[4](https://lobehub.com/vi-VN/mcp/mastanley13-ghl-mcp-chrome-extension)
[5](https://github.com/lhai36366/lhai36366?search=1)
[6](https://cs50.harvard.edu/x/2024/gallery/)
[7](https://www.lri.fr/~adecelle/content/teaching/m1info_pstat_info/tps/count_1w.txt)
[8](https://snap.berkeley.edu/project/11940160)
[9](ftp://ftp.cs.princeton.edu/pub/cs226/autocomplete/words-333333.txt)
[10](https://mirror.umd.edu/xbmc/addons/krypton/addons.xml.gz)