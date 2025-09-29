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

st.markdown("""
<style>
    .stApp {
        background: #1a1a1a !important;
        min-height: 100vh;
    }
    
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    .css-1d391kg {
        display: none !important;
    }
    
    .reportview-container .main .block-container {
        padding-top: 2rem;
    }
    
    .stApp, .stApp * {
        color: #ffffff !important;
    }
    
    div[data-testid="stMarkdownContainer"] h1 {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

if 'pizza_counter' not in st.session_state:
    from utils.pizza_counter import PizzaCounter
    st.session_state.pizza_counter = PizzaCounter()

st.markdown("# 🍕 Pizza Detection Dashboard")

selected = option_menu(
    menu_title="Navigation",
    options=["Dashboard", "Video Library", "Analytics", "Settings"],
    icons=["house", "collection-play", "graph-up", "gear"],
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "rgba(0,0,0,0.3)", "border-radius": "10px"},
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
