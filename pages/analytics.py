import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def show_analytics():
    st.markdown("# 📊 Analytics Dashboard")
    
    counter = st.session_state.pizza_counter
    
    # Date range selector
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30),
            key="analytics_start_date"
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            key="analytics_end_date"
        )
    
    # Load analytics data
    analytics_data = counter.get_analytics_data(start_date, end_date)
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_detections = analytics_data.get('total_detections', 0)
        st.metric("Total Detections", total_detections)
    
    with col2:
        avg_confidence = analytics_data.get('avg_confidence', 0)
        st.metric("Avg Confidence", f"{avg_confidence:.2f}")
    
    with col3:
        videos_processed = analytics_data.get('videos_processed', 0)
        st.metric("Videos Processed", videos_processed)
    
    with col4:
        model_accuracy = analytics_data.get('model_accuracy', 0)
        st.metric("Model Accuracy", f"{model_accuracy}%")
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Daily Detection Trend")
        display_daily_trend_chart(analytics_data)
    
    with col2:
        st.markdown("### 🎯 Confidence Distribution")
        display_confidence_distribution(analytics_data)
    
    # Detailed tables
    st.markdown("### 📋 Detailed Detection Log")
    display_detection_log(analytics_data)

def display_daily_trend_chart(data):
    """Display daily detection trend chart"""
    daily_data = data.get('daily_detections', [])
    
    if daily_data:
        df = pd.DataFrame(daily_data)
        fig = px.line(
            df, 
            x='date', 
            y='count',
            title="Daily Pizza Detections",
            markers=True
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Detections Count"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No detection data available for the selected period.")

def display_confidence_distribution(data):
    """Display confidence score distribution"""
    confidence_data = data.get('confidence_distribution', [])
    
    if confidence_data:
        df = pd.DataFrame(confidence_data)
        fig = px.histogram(
            df,
            x='confidence',
            nbins=20,
            title="Confidence Score Distribution"
        )
        fig.update_layout(
            xaxis_title="Confidence Score",
            yaxis_title="Frequency"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No confidence data available.")

def display_detection_log(data):
    """Display detailed detection log table"""
    detection_log = data.get('detection_log', [])
    
    if detection_log:
        df = pd.DataFrame(detection_log)
        
        # Format the dataframe
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        st.dataframe(
            df,
            width='stretch',
            column_config={
                "confidence": st.column_config.ProgressColumn(
                    "Confidence",
                    help="Detection confidence score",
                    min_value=0.0,
                    max_value=1.0,
                ),
                "timestamp": "Detection Time",
                "video_filename": "Video",
                "pizza_count": "Pizza Count"
            }
        )
        
        # Export option
        if st.button("📥 Export to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"pizza_detections_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No detection log data available.")
