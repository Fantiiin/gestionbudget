import streamlit as st
from database import init_db
from auth import show_auth_page
from styles import inject_css

st.set_page_config(page_title="Budget Tracker", page_icon="🧾", layout="wide", initial_sidebar_state="collapsed")

init_db()
inject_css()

if not show_auth_page():
    st.stop()
else:
    st.switch_page("pages/1_📊_Dashboard.py")
