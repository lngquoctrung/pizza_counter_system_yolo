import streamlit as st
from streamlit_option_menu import option_menu
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(
    page_title="Pizza Detection System",
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit's default navigation
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
        section[data-testid="stSidebar"] {
            display: none;
        }
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize pizza counter
if 'pizza_counter' not in st.session_state:
    from utils.pizza_counter import PizzaCounter
    st.session_state.pizza_counter = PizzaCounter()

# Initialize session state variables
if 'current_processing' not in st.session_state:
    st.session_state.current_processing = {}

st.markdown("# 🍕 Pizza Detection Dashboard")

selected = option_menu(
    menu_title="Navigation",
    options=["Dashboard", "Video Library", "Analytics", "Settings"],
    icons=["house", "collection-play", "graph-up", "gear"],
    default_index=0, 
    key="main_menu",
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#0e1117", "border-radius": "10px"},
        "icon": {"color": "#e74c3c", "font-size": "18px"},
        "nav-link": {
            "font-size": "16px",
            "text-align": "center",
            "margin": "0px",
            "padding": "12px",
            "border-radius": "8px",
            "color": "#ffffff"
        },
        "nav-link-selected": {"background-color": "#667eea", "color": "white"}
    }
)

# Save current tab for reference in other components
st.session_state.current_tab = selected

if selected == "Dashboard":
    from pages.dashboard import show_dashboard
    show_dashboard()
elif selected == "Video Library":
    from pages.video_library import show_video_library
    show_video_library()
elif selected == "Analytics":
    from pages.analytics import show_analytics
    show_analytics()
elif selected == "Settings":
    from pages.settings import show_settings
    show_settings()

# Show processing notification on other tabs
if selected != "Dashboard":
    counter = st.session_state.pizza_counter
    active_processing = any(
        key.startswith("processing_") and st.session_state[key].get("active", False)
        for key in st.session_state.keys()
    )
    
    if active_processing:
        for key in st.session_state.keys():
            if key.startswith("processing_") and st.session_state[key].get("active", False):
                status = st.session_state[key]
                filename = status.get("filename", "Unknown")
                
                # Read from shared_progress if available
                shared_progress = status.get("shared_progress", {})
                progress_lock = status.get("lock")
                
                if progress_lock:
                    try:
                        with progress_lock:
                            progress = shared_progress.get("value", 0)
                    except:
                        progress = counter.processing_videos.get(filename, {}).get("progress", 0)
                else:
                    progress = counter.processing_videos.get(filename, {}).get("progress", 0)
                
                st.info(f"🔄 Video processing in progress: **{filename}** ({progress:.1f}%) - Go to Dashboard to see details")
                break
