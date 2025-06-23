# Pizza Detection System

An automated pizza detection and counting system using YOLOv11 and Flask. This project is designed to automatically detect, track, and count pizzas in videos, with a user-friendly web interface and a feedback system to improve accuracy.

## Key Features

* **Upload Video**: Upload a video to the system for automatic processing
* **Pizza Detection**: Uses YOLOv11 to detect pizzas (class 53 in the COCO dataset)
* **Video Library**: Manage a library of processed videos with real-time status
* **Live Stream Demo**: View real-time detection demo without updating the database
* **Feedback System**: Improve model accuracy through user feedback
* **Dashboard**: Comprehensive statistics and system management
* **Auto Processing**: Automatically processes videos in the background
* **Responsive UI**: Responsive interface with modern CSS

## Project Structure

```bash
├── app.py
├── docker-compose.yml
├── Dockerfile
├── models
│   └── yolo11n.pt
├── pizza_counter.py
├── README.md
├── requirements.txt
├── static
│   ├── css
│   │   └── style.css
│   └── js
│       └── script.js
├── templates
│   └── dashboard.html
└── videos
    ├── 1462_CH03_20250607192844_202844.mp4
    ├── 1462_CH04_20250607210159_211703.mp4
    ├── 1464_CH02_20250607180000_190000.mp4
    ├── 1465_CH02_20250607170555_172408.mp4
    ├── 1467_CH04_20250607180000_190000.mp4
    └── Pizza_production_by_Rademaker_online-video-cutter.com.mp4
```

## Technologies Used

* **Backend**: Flask (Python)
* **AI/ML**: YOLOv11 (Ultralytics)
* **Database**: MongoDB with PyMongo
* **Frontend**: HTML5, CSS3, JavaScript (ES6+)
* **Computer Vision**: OpenCV
* **Containerization**: Docker & Docker Compose
* **Environment**: Python-dotenv

## System Requirements

* **CPU**: Intel i5 or equivalent
* **RAM**: 8GB+ (16GB recommended)
* **GPU**: Optional (NVIDIA GPU recommended for faster processing)
* **Storage**: 10GB+ free space
* **Docker**: Docker and Docker Compose

## Installation

### Using Docker (Recommended)

1. **Clone the repository**:

```bash
git clone <repository-url>
cd pizza_detection_system
```

2. **Run with Docker Compose**:

```bash
docker-compose up --build

# Run on background
docker-compose up -d --build
```

3. **Access the app**: [http://localhost:5000](http://localhost:5000)

### Manual Installation

1. **Install Python 3.12+**

2. **Create virtual environment**

```bash
python3 -m venv .venv

# Activate
# Ubuntu
source .venv/bin/activate

# Windows
.\venv\Scripts\activate
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
```

4. **Create `.env` environment file**:

```yml
MONGODB_URI=mongodb://admin:password123@mongodb:27017/pizza_detection?authSource=admin
```

5. **Create required folders**:

```bash
mkdir -p models videos
```

6. **Run the application**:

```bash
python app.py
```

## Usage

### 1. Upload Video

* Drag and drop video into the upload area or click to select a file
* Supported formats: MP4, AVI, MOV, MKV, WEBM, FLV
* Max size: 500MB

### 2. View Results

* Videos are automatically processed in the background
* Status shown as: Processing → Completed/Error
* Pizza count is updated in real-time

### 3. Stream Demo

* Click "Stream Demo" to view real-time detection
* Demo mode does not update the database
* Displays bounding boxes for pizza only

### 4. Feedback System

* Rate detection accuracy
* Adjust confidence threshold
* System automatically refines the model

### 5. Dashboard

* View overall statistics
* Track videos being processed
* Manage model settings

## API Endpoints

| Method   | Endpoint                       | Description              |
| -------- | ------------------------------ | ------------------------ |
| GET      | `/`                            | Main dashboard           |
| POST     | `/api/upload_video`            | Upload a video           |
| GET      | `/api/videos`                  | List videos              |
| GET      | `/api/stream_video/<filename>` | Stream demo video        |
| GET      | `/api/stats`                   | System statistics        |
| POST     | `/api/feedback`                | Submit feedback          |
| GET/POST | `/api/model_settings`          | Model settings           |
| GET/POST | `/api/detection_classes`       | Manage detection classes |
| GET      | `/health-check`                | Health check             |

## Configuration

### Model Settings

* **Confidence Threshold**: 0.1 - 0.9 (default: 0.5)
* **Tracking Threshold**: 0.3
* **Movement Threshold**: 50 pixels
* **Pizza Class ID**: 53 (COCO dataset)

### Database Collections

* `detections`: Stores detection results
* `feedback`: User feedback data
* `videos`: Video processing status
* `settings`: Model configuration

## Troubleshooting

### Common Issues

1. **Stream not working**:

   * Ensure the video has been fully processed
   * Confirm the video file exists in the `videos/` directory

2. **Upload failed**:

   * Check if the file format is supported
   * Ensure file size is < 500MB

3. **MongoDB connection error**:

   * Verify MongoDB is running
   * Check the connection string in `.env`

4. **Model loading error**:

   * Make sure `yolo11n.pt` file exists in the `models/` directory
   * Check file access permissions

### Performance Optimization

* Use GPU for faster processing
* Adjust confidence threshold appropriately
* Resize videos if they are too large (>1280px width)

## Development

### Code Structure

* `app.py`: Flask routes and API endpoints
* `pizza_counter.py`: Core detection logic and database operations
* `static/js/script.js`: Frontend JavaScript using ES6 classes
* `static/css/style.css`: Responsive modern CSS
* `templates/dashboard.html`: Single-page application interface

### Extending the System

* Add new detection classes in `pizza_counter.py`
* Customize UI in `dashboard.html` and `style.css`
* Add new API endpoints in `app.py`

---

### Support

1. **Version**: 1.0.0
2. **Last Updated**: June 2025
3. **Author**: Ly Nguyen Quoc Trung

---
