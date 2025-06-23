class PizzaDetectionSystem {
    constructor() {
        this.currentStreamUrl = null;
        this.init();
        this.setupEventListeners();
        this.loadInitialData();
        this.startPeriodicUpdates();
    }

    init() {
        this.uploadArea = document.getElementById('uploadArea');
        this.videoInput = document.getElementById('videoInput');
        this.uploadProgress = document.getElementById('uploadProgress');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.videoGrid = document.getElementById('videoGrid');
        this.streamModal = document.getElementById('streamModal');
        this.streamImage = document.getElementById('streamImage');
        this.confidenceSlider = document.getElementById('confidenceSlider');
        this.confidenceValue = document.getElementById('confidenceValue');
        this.detectionsList = document.getElementById('detectionsList');
        this.toastContainer = document.getElementById('toastContainer');
        this.classSelect = document.getElementById('classSelect');
    }

    setupEventListeners() {
        // Upload area drag and drop
        this.uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        this.uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        this.uploadArea.addEventListener('click', () => this.videoInput.click());

        // File input change
        this.videoInput.addEventListener('change', this.handleFileSelect.bind(this));

        // Confidence slider
        this.confidenceSlider.addEventListener('input', (e) => {
            this.confidenceValue.textContent = e.target.value;
        });

        // Modal close events - improved
        window.addEventListener('click', (e) => {
            if (e.target === this.streamModal) {
                this.closeStreamModal();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.streamModal.style.display === 'block') {
                this.closeStreamModal();
            }
        });

        // Handle page unload to clean up streams
        window.addEventListener('beforeunload', () => {
            this.stopCurrentStream();
        });

        // Handle visibility change to pause/resume stream
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.currentStreamUrl) {
                console.log('Page hidden, stream may be paused');
            }
        });
    }

    handleDragOver(e) {
        e.preventDefault();
        this.uploadArea.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.uploadVideo(files[0]);
        }
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.uploadVideo(file);
        }
    }

    async uploadVideo(file) {
        // Validate file type
        const allowedTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm', 'video/x-flv'];
        if (!allowedTypes.includes(file.type)) {
            this.showToast('File format not supported!', 'error');
            return;
        }

        // Validate file size (max 500MB)
        const maxSize = 500 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showToast('File too large! Maximum 500MB.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('video', file);

        // Show progress
        this.uploadProgress.style.display = 'block';
        this.progressFill.style.width = '0%';
        this.progressText.textContent = 'Uploading...';

        try {
            const xhr = new XMLHttpRequest();
            
            // Upload progress
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    this.progressFill.style.width = percentComplete + '%';
                    this.progressText.textContent = `Uploading... ${Math.round(percentComplete)}%`;
                }
            });

            // Upload complete
            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    this.showToast('Upload successful! Processing video...', 'success');
                    this.progressText.textContent = 'Processing video...';
                    
                    // Refresh video list after a short delay
                    setTimeout(() => {
                        this.loadVideoLibrary();
                        this.uploadProgress.style.display = 'none';
                        this.videoInput.value = '';
                    }, 2000);
                } else {
                    const error = JSON.parse(xhr.responseText);
                    this.showToast(`Upload error: ${error.error}`, 'error');
                    this.uploadProgress.style.display = 'none';
                }
            });

            // Upload error
            xhr.addEventListener('error', () => {
                this.showToast('Connection error! Please try again.', 'error');
                this.uploadProgress.style.display = 'none';
            });

            xhr.open('POST', '/api/upload_video');
            xhr.send(formData);

        } catch (error) {
            console.error('Upload error:', error);
            this.showToast('An error occurred during upload!', 'error');
            this.uploadProgress.style.display = 'none';
        }
    }

    async loadInitialData() {
        await Promise.all([
            this.loadStats(),
            this.loadVideoLibrary(),
            this.loadRecentDetections(),
            this.loadModelSettings(),
        ]);
    }

    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            
            document.getElementById('totalPizzas').textContent = stats.total_pizzas || 0;
            document.getElementById('todayPizzas').textContent = stats.today_pizzas || 0;
            document.getElementById('accuracy').textContent = `${stats.accuracy_percentage || 0}%`;
            document.getElementById('processingVideos').textContent = stats.processing_videos || 0;
            document.getElementById('modelThreshold').textContent = stats.confidence_threshold || 0.5;
            
            // Update last update time
            const now = new Date();
            document.getElementById('lastUpdate').textContent = now.toLocaleTimeString('en-US');
            
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    async loadVideoLibrary() {
        try {
            const response = await fetch('/api/videos');
            const data = await response.json();
            
            this.renderVideoGrid(data.videos || []);
        } catch (error) {
            console.error('Error loading video library:', error);
            this.showToast('Unable to load video list!', 'error');
        }
    }

    renderVideoGrid(videos) {
        if (videos.length === 0) {
            this.videoGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-video" style="font-size: 3rem; color: #bdc3c7; margin-bottom: 15px;"></i>
                    <p style="color: #7f8c8d;">No videos uploaded yet</p>
                </div>
            `;
            return;
        }

        this.videoGrid.innerHTML = videos.map(video => `
            <div class="video-card">
                <div class="video-info">
                    <div class="video-filename">${video.filename}</div>
                    <div class="video-meta">Size: ${video.size_mb} MB</div>
                    <div class="video-meta">Pizzas detected: ${video.pizza_count}</div>
                    <div class="video-meta">
                        <span class="video-status status-${video.status}">${this.getStatusText(video.status)}</span>
                    </div>
                    ${video.processed_at ? `<div class="video-meta">Processed: ${new Date(video.processed_at).toLocaleString('en-US')}</div>` : ''}
                </div>
                <div class="video-actions">
                    <button class="btn-stream" 
                            onclick="pizzaSystem.streamVideo('${video.filename}')"
                            ${video.status !== 'completed' ? 'disabled' : ''}>
                        <i class="fas fa-play"></i> Stream Demo
                    </button>
                </div>
            </div>
        `).join('');
    }

    getStatusText(status) {
        const statusMap = {
            'completed': 'Completed',
            'processing': 'Processing',
            'error': 'Error',
            'pending': 'Pending'
        };
        return statusMap[status] || status;
    }

    async streamVideo(filename) {
        try {
            this.streamModal.style.display = 'block';
            
            // Clear any existing stream
            this.stopCurrentStream();
            
            // Set up new stream with error handling
            this.currentStreamUrl = `/api/stream_video/${filename}`;
            this.streamImage.src = this.currentStreamUrl;
            
            // Add error handling for stream
            this.streamImage.onerror = () => {
                console.log('Stream ended or error occurred');
                // Don't show error toast when user closes modal
                if (this.streamModal.style.display === 'block') {
                    this.showToast('Stream ended', 'info');
                }
            };
            
            this.streamImage.onload = () => {
                console.log('Stream started successfully');
            };
            
        } catch (error) {
            console.error('Error streaming video:', error);
            this.showToast('Error streaming video!', 'error');
        }
    }

    stopCurrentStream() {
        if (this.streamImage) {
            this.streamImage.src = '';
            this.streamImage.onerror = null;
            this.streamImage.onload = null;
        }
        this.currentStreamUrl = null;
    }

    closeStreamModal() {
        // Stop stream first
        this.stopCurrentStream();
        
        // Hide modal
        this.streamModal.style.display = 'none';
        
        // Small delay to ensure stream is properly closed
        setTimeout(() => {
            console.log('Stream modal closed');
        }, 100);
    }

    async loadRecentDetections() {
        try {
            const response = await fetch('/api/detections');
            const detections = await response.json();
            
            this.renderDetectionsList(detections);
        } catch (error) {
            console.error('Error loading detections:', error);
        }
    }

    renderDetectionsList(detections) {
        if (detections.length === 0) {
            this.detectionsList.innerHTML = `
                <div class="empty-state">
                    <p style="color: #7f8c8d; text-align: center;">No detections need feedback</p>
                </div>
            `;
            return;
        }

        this.detectionsList.innerHTML = detections.map(detection => `
            <div class="detection-item">
                <div class="detection-info">
                    <div>
                        <strong>Track ID:</strong> ${detection.track_id}<br>
                        <strong>Confidence:</strong> ${(detection.confidence * 100).toFixed(1)}%
                    </div>
                    <div class="detection-meta">
                        ${new Date(detection.timestamp).toLocaleString('en-US')}
                    </div>
                </div>
                <div class="feedback-buttons">
                    <button class="btn-correct" onclick="pizzaSystem.submitFeedback(${detection.track_id}, true)">
                        <i class="fas fa-check"></i> Correct
                    </button>
                    <button class="btn-incorrect" onclick="pizzaSystem.submitFeedback(${detection.track_id}, false)">
                        <i class="fas fa-times"></i> Incorrect
                    </button>
                </div>
            </div>
        `).join('');
    }

    async submitFeedback(trackId, isCorrect) {
        try {
            const response = await fetch('/api/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    track_id: trackId,
                    is_correct: isCorrect
                })
            });

            if (response.ok) {
                this.showToast('Feedback submitted!', 'success');
                this.loadRecentDetections();
                this.loadStats(); // Refresh accuracy
            } else {
                this.showToast('Error submitting feedback!', 'error');
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
            this.showToast('Connection error!', 'error');
        }
    }

    async loadModelSettings() {
        try {
            const response = await fetch('/api/model_settings');
            const settings = await response.json();
            
            this.confidenceSlider.value = settings.confidence_threshold;
            this.confidenceValue.textContent = settings.confidence_threshold;
        } catch (error) {
            console.error('Error loading model settings:', error);
        }
    }

    async updateModelSettings() {
        try {
            const newThreshold = parseFloat(this.confidenceSlider.value);
            
            const response = await fetch('/api/model_settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    confidence_threshold: newThreshold
                })
            });

            if (response.ok) {
                this.showToast('Model settings updated!', 'success');
                this.loadStats();
            } else {
                this.showToast('Error updating settings!', 'error');
            }
        } catch (error) {
            console.error('Error updating model settings:', error);
            this.showToast('Connection error!', 'error');
        }
    }

    async loadDetectionClasses() {
        try {
            const response = await fetch('/api/detection_classes');
            const data = await response.json();
            
            this.renderClassSelection(data.available_classes, data.current_classes);
            document.getElementById('currentClasses').textContent = data.current_class_names.join(', ');
        } catch (error) {
            console.error('Error loading detection classes:', error);
        }
    }

    renderClassSelection(availableClasses, currentClasses) {
        if (!this.classSelect) return;
        
        this.classSelect.innerHTML = Object.entries(availableClasses).map(([id, name]) => `
            <option value="${id}" ${currentClasses.includes(parseInt(id)) ? 'selected' : ''}>
                ${id}: ${name}
            </option>
        `).join('');
    }

    startPeriodicUpdates() {
        // Update stats every 30 seconds
        setInterval(() => {
            this.loadStats();
        }, 30000);

        // Update video library every 60 seconds
        setInterval(() => {
            this.loadVideoLibrary();
        }, 60000);

        // Update detections every 45 seconds
        setInterval(() => {
            this.loadRecentDetections();
        }, 45000);
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-${this.getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;

        this.toastContainer.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);

        // Click to dismiss
        toast.addEventListener('click', () => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        });
    }

    getToastIcon(type) {
        const iconMap = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return iconMap[type] || 'info-circle';
    }
}

// Global functions for HTML onclick events
function updateModelSettings() {
    pizzaSystem.updateModelSettings();
}

function updateDetectionClasses() {
    pizzaSystem.updateDetectionClasses();
}

function closeStreamModal() {
    pizzaSystem.closeStreamModal();
}

// Initialize the system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.pizzaSystem = new PizzaDetectionSystem();
});
