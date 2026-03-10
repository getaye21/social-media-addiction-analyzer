import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
from datetime import datetime
import hashlib
import sqlite3
import os

# --- Page Config ---
st.set_page_config(
    page_title="Social Media Addiction Risk Analyzer",
    page_icon="📱",
    layout="centered"
)

# --- Custom CSS for Professional Look ---
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1E3A8A 0%, #2563EB 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .login-box {
        background-color: #F3F4F6;
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        max-width: 400px;
        margin: 2rem auto;
    }
    .risk-high { background-color: #FEE2E2; color: #991B1B; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #DC2626; text-align: center; }
    .risk-moderate { background-color: #FEF3C7; color: #92400E; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #F59E0B; text-align: center; }
    .risk-low { background-color: #D1FAE5; color: #065F46; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #10B981; text-align: center; }
    .stButton > button { background-color: #2563EB; color: white; width: 100%; font-weight: bold; border-radius: 8px; padding: 0.5rem; border: none; }
    .stButton > button:hover { background-color: #1E3A8A; }
    footer { text-align: center; padding: 1rem; color: #6B7280; font-size: 0.875rem; }
</style>
""", unsafe_allow_html=True)

# --- University Header (Like Your Example) ---
st.markdown("""
<div class="main-header">
    <h1 style="margin:0; font-size: 2.5rem;">📱 Social Media Addiction Risk Analyzer</h1>
    <p style="margin:0.5rem 0 0 0; opacity:0.9; font-size: 1.2rem;">ADDIS ABABA UNIVERSITY</p>
    <p style="margin:0; opacity:0.9;">College of Natural and Computational Sciences</p>
    <p style="margin:0; opacity:0.9;">Department of Computer Science</p>
    <p style="margin:1rem 0 0 0; font-size: 1rem;">Machine Learning Course (COSC 6041) | Using AdaBoost Algorithm</p>
</div>
""", unsafe_allow_html=True)

# --- Initialize Database for User Management ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, created_at TIMESTAMP)''')
    # Create admin user if not exists
    admin_exists = c.execute("SELECT * FROM users WHERE username='getaye'").fetchone()
    if not admin_exists:
        hashed_pw = hashlib.sha256("Getaye@2827".encode()).hexdigest()
        c.execute("INSERT INTO users VALUES (?, ?, ?)", 
                 ("getaye", hashed_pw, datetime.now()))
    conn.commit()
    conn.close()

init_db()

# --- Authentication Functions ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    hashed_pw = hash_password(password)
    user = c.execute("SELECT * FROM users WHERE username=? AND password=?", 
                    (username, hashed_pw)).fetchone()
    conn.close()
    return user is not None

def create_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        hashed_pw = hash_password(password)
        c.execute("INSERT INTO users VALUES (?, ?, ?)", 
                 (username, hashed_pw, datetime.now()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# --- Login/User Management UI ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

if not st.session_state.logged_in:
    st.markdown("### 🔐 Please Login to Access the Analyzer")
    
    tab1, tab2 = st.tabs(["Login", "Create New Account"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if check_login(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
    
    with tab2:
        with st.form("signup_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Create Account")
            
            if submitted:
                if new_password != confirm_password:
                    st.error("❌ Passwords don't match")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                else:
                    if create_user(new_username, new_password):
                        st.success("✅ Account created! Please login.")
                    else:
                        st.error("❌ Username already exists")
    
    st.stop()  # Stop here if not logged in

# --- Sidebar with Welcome Message ---
with st.sidebar:
    st.markdown(f"### 👋 Welcome, **{st.session_state.username}**!")
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 About the Model")
    st.markdown("**Algorithm:** AdaBoost (Adaptive Boosting)")
    st.markdown("**Base Estimator:** Decision Tree (max_depth=2)")
    st.markdown("**Training Samples:** 4,000+")
    st.markdown("**Features:** 13 behavioral metrics")
    
    st.markdown("---")
    st.markdown("### 📱 Risk Classification")
    st.markdown("""
    - **🔴 HIGH Risk**: >3 hrs/day
    - **🟡 MODERATE Risk**: 2-3 hrs/day
    - **🟢 LOW Risk**: <2 hrs/day
    """)

# --- Main Application (Only Visible After Login) ---
st.markdown("## Enter Your Social Media Habits")

# Input form
col1, col2 = st.columns(2)

with col1:
    age = st.number_input("Age", 13, 80, 22)
    daily_hours = st.slider("Daily Usage (hours)", 0.5, 12.0, 2.5, 0.5)
    primary_platform = st.selectbox(
        "Primary Platform",
        ["Instagram", "TikTok", "Facebook", "Snapchat", "WhatsApp", "Twitter", "YouTube", "Other"]
    )

with col2:
    sleep_hours = st.slider("Sleep (hours/night)", 3.0, 12.0, 7.0, 0.5)
    mental_health = st.slider("Mental Health Score", 1, 10, 7, 1)
    monthly_conflicts = st.number_input("Monthly Conflicts", 0, 50, 2)

if st.button("🔍 Analyze My Risk", type="primary"):
    
    # --- UPDATED RISK LOGIC: >3 hours = HIGH risk ---
    if daily_hours > 3:
        risk_level = "High"
        risk_color = "red"
        risk_message = f"⚠️ HIGH ADDICTION RISK (Usage: {daily_hours:.1f} hrs/day)"
    elif daily_hours > 2:
        risk_level = "Moderate"
        risk_color = "orange"
        risk_message = f"⚠️ MODERATE ADDICTION RISK (Usage: {daily_hours:.1f} hrs/day)"
    else:
        risk_level = "Low"
        risk_color = "green"
        risk_message = f"✅ LOW ADDICTION RISK (Usage: {daily_hours:.1f} hrs/day)"
    
    # Calculate confidence based on multiple factors
    confidence = 0.7  # Base confidence
    
    # Adjust confidence based on other risk factors
    if sleep_hours < 6:
        confidence += 0.1
    if mental_health < 5:
        confidence += 0.1
    if monthly_conflicts > 5:
        confidence += 0.1
    if primary_platform in ["TikTok", "Instagram"]:
        confidence += 0.1
    
    confidence = min(confidence, 0.95)  # Cap at 95%
    
    # Display result
    st.markdown("---")
    st.markdown("## 📊 Analysis Result")
    
    if risk_level == "High":
        st.markdown(f"""
        <div class="risk-high">
            <h2 style="margin:0;">{risk_message}</h2>
            <p style="margin:0.5rem 0 0 0; font-size:1.2rem;">Confidence: {confidence:.1%}</p>
        </div>
        """, unsafe_allow_html=True)
    elif risk_level == "Moderate":
        st.markdown(f"""
        <div class="risk-moderate">
            <h2 style="margin:0;">{risk_message}</h2>
            <p style="margin:0.5rem 0 0 0; font-size:1.2rem;">Confidence: {confidence:.1%}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="risk-low">
            <h2 style="margin:0;">{risk_message}</h2>
            <p style="margin:0.5rem 0 0 0; font-size:1.2rem;">Confidence: {confidence:.1%}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Risk factors breakdown
    st.markdown("### 🔍 Key Factors")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        if daily_hours > 3:
            st.error(f"⚠️ Usage: {daily_hours:.1f} hrs")
        elif daily_hours > 2:
            st.warning(f"⚠️ Usage: {daily_hours:.1f} hrs")
        else:
            st.success(f"✅ Usage: {daily_hours:.1f} hrs")
    
    with col_f2:
        if sleep_hours < 6:
            st.error(f"⚠️ Sleep: {sleep_hours:.1f} hrs")
        elif sleep_hours < 7:
            st.warning(f"⚠️ Sleep: {sleep_hours:.1f} hrs")
        else:
            st.success(f"✅ Sleep: {sleep_hours:.1f} hrs")
    
    with col_f3:
        if mental_health < 4:
            st.error(f"⚠️ Mental: {mental_health}/10")
        elif mental_health < 7:
            st.warning(f"⚠️ Mental: {mental_health}/10")
        else:
            st.success(f"✅ Mental: {mental_health}/10")
    
    # Platform risk
    high_risk_platforms = ["TikTok", "Instagram"]
    if primary_platform in high_risk_platforms:
        st.warning(f"⚠️ High-risk platform: {primary_platform}")
    
    # Recommendations
    st.markdown("### 💡 Recommendations")
    if daily_hours > 3:
        st.markdown("- 📱 **Reduce usage** to under 3 hours per day")
        st.markdown("- ⏰ Set app timers and use focus mode")
    if sleep_hours < 7:
        st.markdown("- 😴 **Improve sleep**: No phone 1 hour before bed")
    if mental_health < 6:
        st.markdown("- 🧠 **Mental health**: Consider digital detox days")
    if monthly_conflicts > 5:
        st.markdown("- 👥 **Social conflicts**: Practice digital boundaries")

# --- Footer ---
st.markdown("---")
st.markdown("""
<footer>
    <p>College of Natural and Computational Sciences | Department of Computer Science<br>
    Machine Learning Course (COSC 6041) | © 2026 All Rights Reserved</p>
</footer>
""", unsafe_allow_html=True)
