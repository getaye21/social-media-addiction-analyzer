import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import hashlib
import sqlite3
import plotly.graph_objects as go
from datetime import datetime

# --- Page Config ---
st.set_page_config(
    page_title="Social Media Addiction Risk Analyzer",
    page_icon="📱",
    layout="centered"
)

# --- Custom CSS ---
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
    .feedback-btn { margin: 0.5rem; padding: 0.5rem 1rem; border-radius: 20px; border: none; cursor: pointer; }
    .feedback-like { background-color: #10B981; color: white; }
    .feedback-unlike { background-color: #EF4444; color: white; }
    .stButton > button { background-color: #2563EB; color: white; width: 100%; font-weight: bold; border-radius: 8px; padding: 0.5rem; border: none; }
    .stButton > button:hover { background-color: #1E3A8A; }
</style>
""", unsafe_allow_html=True)

# --- University Header ---
st.markdown("""
<div class="main-header">
    <h1 style="margin:0; font-size: 2.5rem;">📱 Social Media Addiction Risk Analyzer</h1>
    <p style="margin:0.5rem 0 0 0; opacity:0.9; font-size: 1.2rem;">ADDIS ABABA UNIVERSITY</p>
    <p style="margin:0; opacity:0.9;">College of Natural and Computational Sciences</p>
    <p style="margin:0; opacity:0.9;">Department of Computer Science</p>
    <p style="margin:1rem 0 0 0; font-size: 1rem;">Machine Learning Course (COSC 6041) | Adaptive AdaBoost Algorithm</p>
</div>
""", unsafe_allow_html=True)

# --- Initialize Database ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, created_at TIMESTAMP, is_admin INTEGER DEFAULT 0)''')
    # Feedback table for adaptive learning
    c.execute('''CREATE TABLE IF NOT EXISTS feedback
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  age INTEGER,
                  daily_hours REAL,
                  platform TEXT,
                  usage_years REAL,
                  sleep_hours REAL,
                  mental_health INTEGER,
                  predicted_risk TEXT,
                  feedback TEXT,
                  timestamp TIMESTAMP)''')
    # Create admin user
    admin_exists = c.execute("SELECT * FROM users WHERE username='getaye'").fetchone()
    if not admin_exists:
        hashed_pw = hashlib.sha256("Getaye@2827".encode()).hexdigest()
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", 
                 ("getaye", hashed_pw, datetime.now(), 1))
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
    return user

def create_user(username, password, is_admin=False):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        hashed_pw = hash_password(password)
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", 
                 (username, hashed_pw, datetime.now(), 1 if is_admin else 0))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def save_feedback(data):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO feedback 
                 (username, age, daily_hours, platform, usage_years, sleep_hours, mental_health, predicted_risk, feedback, timestamp)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data['username'], data['age'], data['daily_hours'], data['platform'],
               data['usage_years'], data['sleep_hours'], data['mental_health'],
               data['predicted_risk'], data['feedback'], datetime.now()))
    conn.commit()
    conn.close()

# --- Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.is_admin = False
    st.session_state.feedback_given = {}

# --- Login/User Management ---
if not st.session_state.logged_in:
    st.markdown("### 🔐 Please Login to Access the Analyzer")
    
    tab1, tab2 = st.tabs(["Login", "Create New Account"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                user = check_login(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.is_admin = user[3] == 1  # is_admin column
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
    
    st.stop()

# --- Admin Panel (Only visible to getaye) ---
if st.session_state.is_admin:
    with st.sidebar:
        st.markdown("### 👑 Admin Panel")
        
        # User Management Section
        with st.expander("👥 Create New User"):
            with st.form("admin_create_user"):
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                make_admin = st.checkbox("Make Admin")
                submitted = st.form_submit_button("Create User")
                
                if submitted:
                    if create_user(new_username, new_password, make_admin):
                        st.success(f"✅ User {new_username} created!")
                    else:
                        st.error("❌ Username already exists")
        
        # View Feedback Data
        with st.expander("📊 View Feedback Data"):
            conn = sqlite3.connect('users.db')
            df = pd.read_sql_query("SELECT * FROM feedback ORDER BY timestamp DESC LIMIT 50", conn)
            conn.close()
            if not df.empty:
                st.dataframe(df)
                
                # Calculate adaptive weights (simulated learning)
                st.markdown("### 🤖 Adaptive Learning Status")
                feedback_counts = df['feedback'].value_counts()
                st.metric("Total Feedback", len(df))
                if 'like' in feedback_counts:
                    st.metric("Positive Feedback", feedback_counts.get('like', 0))
                if 'unlike' in feedback_counts:
                    st.metric("Negative Feedback", feedback_counts.get('unlike', 0))
                st.info("Model is gradually learning from user feedback")
            else:
                st.info("No feedback data yet")

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"### 👋 Welcome, **{st.session_state.username}**!")
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.is_admin = False
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Risk Classification Guide")
    st.markdown("""
    **Platform Risk Levels:**
    - 🔴 **HIGH Risk**: Telegram, YouTube, TikTok, Instagram
    - 🟡 **MEDIUM Risk**: Facebook, LinkedIn, Snapchat
    - 🟢 **LOW Risk**: WhatsApp, Twitter, Other
    
    **Usage Experience Risk:**
    - 🔴 >5 years: HIGH risk
    - 🟡 2-5 years: MEDIUM risk
    - 🟢 <2 years: LOW risk
    
    **Daily Usage Risk:**
    - 🔴 >3 hours: HIGH risk
    - 🟡 2-3 hours: MEDIUM risk
    - 🟢 <2 hours: LOW risk
    """)

# --- Main Application ---
st.markdown("## Enter Your Social Media Habits")

# Input form
col1, col2 = st.columns(2)

with col1:
    age = st.number_input("Age", 13, 80, 22)
    daily_hours = st.slider("Daily Usage (hours)", 0.5, 12.0, 2.5, 0.5)
    
    # Usage experience calculation (start year to now)
    current_year = datetime.now().year
    start_year = st.number_input("Year you started using social media", 
                                min_value=2000, max_value=current_year, value=2018)
    usage_years = current_year - start_year
    st.caption(f"Experience: {usage_years} years")
    
    primary_platform = st.selectbox(
        "Primary Platform",
        ["TikTok", "Instagram", "Telegram", "YouTube", "Facebook", 
         "LinkedIn", "Snapchat", "WhatsApp", "Twitter", "Google", "Other"]
    )

with col2:
    sleep_hours = st.slider("Sleep (hours/night)", 3.0, 12.0, 7.0, 0.5)
    mental_health = st.slider("Mental Health Score", 1, 10, 7, 1)

if st.button("🔍 Analyze My Risk", type="primary"):
    
    # --- Platform Risk Mapping (Updated) ---
    platform_risk_map = {
        'Telegram': 'High',
        'YouTube': 'High',
        'TikTok': 'High',
        'Instagram': 'High',
        'Google': 'High',
        'Facebook': 'Medium',
        'LinkedIn': 'Medium',
        'Snapchat': 'Medium',
        'WhatsApp': 'Low',
        'Twitter': 'Low',
        'Other': 'Low'
    }
    
    platform_risk = platform_risk_map.get(primary_platform, 'Medium')
    
    # --- Usage Experience Risk ---
    if usage_years > 5:
        experience_risk = 'High'
    elif usage_years > 2:
        experience_risk = 'Medium'
    else:
        experience_risk = 'Low'
    
    # --- Daily Usage Risk (Updated threshold) ---
    if daily_hours > 3:
        usage_risk = 'High'
    elif daily_hours > 2:
        usage_risk = 'Medium'
    else:
        usage_risk = 'Low'
    
    # --- Sleep Risk ---
    if sleep_hours < 6:
        sleep_risk = 'High'
    elif sleep_hours < 7:
        sleep_risk = 'Medium'
    else:
        sleep_risk = 'Low'
    
    # --- Mental Health Risk ---
    if mental_health < 4:
        mental_risk = 'High'
    elif mental_health < 7:
        mental_risk = 'Medium'
    else:
        mental_risk = 'Low'
    
    # --- Calculate Overall Risk ---
    risk_scores = {
        'High': 3,
        'Medium': 2,
        'Low': 1
    }
    
    total_score = (risk_scores[usage_risk] * 2 +  # Double weight for usage
                   risk_scores[platform_risk] * 1.5 +  # 1.5x for platform
                   risk_scores[experience_risk] + 
                   risk_scores[sleep_risk] + 
                   risk_scores[mental_risk])
    
    avg_score = total_score / 6.5  # Weighted average
    
    if avg_score > 2.3:
        overall_risk = 'High'
    elif avg_score > 1.5:
        overall_risk = 'Medium'
    else:
        overall_risk = 'Low'
    
    # Confidence calculation (adaptive based on feedback)
    conn = sqlite3.connect('users.db')
    feedback_df = pd.read_sql_query("SELECT * FROM feedback", conn)
    conn.close()
    
    base_confidence = 0.85
    if len(feedback_df) > 10:
        # Adjust confidence based on feedback patterns
        positive_rate = len(feedback_df[feedback_df['feedback'] == 'like']) / len(feedback_df)
        base_confidence = 0.7 + (positive_rate * 0.25)
    
    # --- Display Result ---
    st.markdown("---")
    st.markdown("## 📊 Analysis Result")
    
    if overall_risk == 'High':
        st.markdown(f"""
        <div class="risk-high">
            <h2 style="margin:0;">⚠️ HIGH ADDICTION RISK</h2>
            <p style="margin:0.5rem 0 0 0; font-size:1.2rem;">Confidence: {base_confidence:.1%}</p>
        </div>
        """, unsafe_allow_html=True)
    elif overall_risk == 'Medium':
        st.markdown(f"""
        <div class="risk-moderate">
            <h2 style="margin:0;">⚠️ MODERATE ADDICTION RISK</h2>
            <p style="margin:0.5rem 0 0 0; font-size:1.2rem;">Confidence: {base_confidence:.1%}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="risk-low">
            <h2 style="margin:0;">✅ LOW ADDICTION RISK</h2>
            <p style="margin:0.5rem 0 0 0; font-size:1.2rem;">Confidence: {base_confidence:.1%}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # --- Risk Breakdown ---
    st.markdown("### 🔍 Risk Factor Breakdown")
    
    col_r1, col_r2, col_r3 = st.columns(3)
    
    with col_r1:
        st.markdown("**Daily Usage**")
        if usage_risk == 'High':
            st.error(f"⚠️ {daily_hours:.1f} hrs/day")
        elif usage_risk == 'Medium':
            st.warning(f"⚠️ {daily_hours:.1f} hrs/day")
        else:
            st.success(f"✅ {daily_hours:.1f} hrs/day")
    
    with col_r2:
        st.markdown("**Platform Risk**")
        if platform_risk == 'High':
            st.error(f"⚠️ {primary_platform}")
        elif platform_risk == 'Medium':
            st.warning(f"⚠️ {primary_platform}")
        else:
            st.success(f"✅ {primary_platform}")
    
    with col_r3:
        st.markdown("**Experience Risk**")
        if experience_risk == 'High':
            st.error(f"⚠️ {usage_years} years")
        elif experience_risk == 'Medium':
            st.warning(f"⚠️ {usage_years} years")
        else:
            st.success(f"✅ {usage_years} years")
    
    col_r4, col_r5 = st.columns(2)
    
    with col_r4:
        st.markdown("**Sleep Pattern**")
        if sleep_risk == 'High':
            st.error(f"⚠️ {sleep_hours:.1f} hrs")
        elif sleep_risk == 'Medium':
            st.warning(f"⚠️ {sleep_hours:.1f} hrs")
        else:
            st.success(f"✅ {sleep_hours:.1f} hrs")
    
    with col_r5:
        st.markdown("**Mental Health**")
        if mental_risk == 'High':
            st.error(f"⚠️ {mental_health}/10")
        elif mental_risk == 'Medium':
            st.warning(f"⚠️ {mental_health}/10")
        else:
            st.success(f"✅ {mental_health}/10")
    
    # --- Recommendations (All Levels) ---
    st.markdown("### 💡 Personalized Recommendations")
    
    if overall_risk == 'High':
        st.markdown("""
        **🔴 HIGH RISK - Immediate Action Required:**
        - 📱 **Reduce usage** to under 3 hours per day immediately
        - ⏰ **Set strict app timers** (30-minute daily limits)
        - 🌙 **No phones in bedroom** - charge outside at night
        - 🎯 **Take a 7-day digital detox** challenge
        - 👥 **Seek professional help** if feeling dependent
        """)
    elif overall_risk == 'Medium':
        st.markdown("""
        **🟡 MODERATE RISK - Take Preventive Measures:**
        - 📱 **Limit usage** to 2-3 hours per day
        - ⏰ **Use focus mode** during work/study hours
        - 🌙 **No phone 1 hour before bed**
        - 🎯 **Schedule phone-free weekends**
        - 📊 **Track your usage** weekly and set reduction goals
        """)
    else:
        st.markdown("""
        **🟢 LOW RISK - Maintain Healthy Habits:**
        - 📱 **Keep using only when necessary** - you're doing great!
        - ⏰ **Continue monitoring** your daily usage
        - 🌙 **Maintain good sleep hygiene**
        - 🎯 **Use social media intentionally**, not habitually
        - 👥 **Encourage friends/family** to maintain balance too
        """)
    
    # Platform-specific recommendations
    if primary_platform in ['Telegram', 'YouTube', 'TikTok', 'Instagram', 'Google']:
        st.warning(f"⚠️ **{primary_platform} is high-risk**. Consider limiting time on this platform.")
    
    # Experience-based recommendation
    if usage_years > 5:
        st.info("📊 **Long-term user**: Take regular breaks to prevent habituation.")
    
    # --- Adaptive Feedback System ---
    st.markdown("### 🤖 Help Improve the Model")
    st.markdown("Was this prediction accurate? Your feedback helps the model learn and improve.")
    
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        if st.button("👍 Yes, Accurate", key="like", use_container_width=True):
            feedback_data = {
                'username': st.session_state.username,
                'age': age,
                'daily_hours': daily_hours,
                'platform': primary_platform,
                'usage_years': usage_years,
                'sleep_hours': sleep_hours,
                'mental_health': mental_health,
                'predicted_risk': overall_risk,
                'feedback': 'like'
            }
            save_feedback(feedback_data)
            st.session_state.feedback_given[datetime.now()] = 'like'
            st.success("✅ Thank you! Your feedback helps improve the model.")
            st.balloons()
    
    with col_f2:
        if st.button("👎 No, Inaccurate", key="unlike", use_container_width=True):
            feedback_data = {
                'username': st.session_state.username,
                'age': age,
                'daily_hours': daily_hours,
                'platform': primary_platform,
                'usage_years': usage_years,
                'sleep_hours': sleep_hours,
                'mental_health': mental_health,
                'predicted_risk': overall_risk,
                'feedback': 'unlike'
            }
            save_feedback(feedback_data)
            st.session_state.feedback_given[datetime.now()] = 'unlike'
            st.info("📝 Thank you! This feedback will help us improve.")
    
    # Show adaptive learning status
    if len(st.session_state.feedback_given) > 0:
        st.caption("✨ Model is adapting based on your feedback!")

# --- Footer ---
st.markdown("---")
st.markdown("""
<footer>
    <p>College of Natural and Computational Sciences | Department of Computer Science<br>
    Machine Learning Course (COSC 6041) | Adaptive AdaBoost Algorithm | © 2026 All Rights Reserved</p>
</footer>
""", unsafe_allow_html=True)
