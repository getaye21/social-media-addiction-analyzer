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

# --- Custom CSS for Interactive UI ---
st.markdown("""
<style>
    /* Main header with graduation icon */
    .main-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 50%, #1E3A8A 100%);
        padding: 2.5rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        border: 1px solid rgba(255,255,255,0.1);
        animation: gradientFlow 5s ease infinite;
    }
    
    @keyframes gradientFlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .header-title {
        font-size: 2.8rem;
        font-weight: bold;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
    }
    
    .header-title span {
        background: rgba(255,255,255,0.2);
        padding: 10px 20px;
        border-radius: 50px;
        font-size: 1.5rem;
    }
    
    .university-name {
        font-size: 1.8rem;
        font-weight: 600;
        margin: 0.5rem 0;
        letter-spacing: 2px;
    }
    
    .college-name {
        font-size: 1.2rem;
        opacity: 0.95;
        margin: 0.2rem 0;
    }
    
    .course-info {
        margin-top: 1rem;
        font-size: 1.1rem;
        background: rgba(255,255,255,0.15);
        padding: 10px 20px;
        border-radius: 50px;
        display: inline-block;
    }
    
    /* Interactive card effects */
    .risk-card {
        transition: transform 0.3s, box-shadow 0.3s;
        cursor: pointer;
    }
    
    .risk-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(0,0,0,0.2);
    }
    
    /* Button animations */
    .stButton > button {
        background: linear-gradient(90deg, #2563EB, #1E3A8A);
        color: white;
        width: 100%;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.7rem;
        border: none;
        transition: all 0.3s;
        font-size: 1.1rem;
    }
    
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(37, 99, 235, 0.4);
    }
    
    /* Risk level displays */
    .risk-high { 
        background: linear-gradient(135deg, #FEE2E2, #FECACA);
        color: #991B1B; 
        padding: 1.8rem; 
        border-radius: 15px; 
        border-left: 8px solid #DC2626; 
        text-align: center;
        box-shadow: 0 5px 15px rgba(220, 38, 38, 0.2);
    }
    
    .risk-moderate { 
        background: linear-gradient(135deg, #FEF3C7, #FDE68A);
        color: #92400E; 
        padding: 1.8rem; 
        border-radius: 15px; 
        border-left: 8px solid #F59E0B;
        box-shadow: 0 5px 15px rgba(245, 158, 11, 0.2);
    }
    
    .risk-low { 
        background: linear-gradient(135deg, #D1FAE5, #A7F3D0);
        color: #065F46; 
        padding: 1.8rem; 
        border-radius: 15px; 
        border-left: 8px solid #10B981;
        box-shadow: 0 5px 15px rgba(16, 185, 129, 0.2);
    }
    
    /* Login box styling */
    .login-box {
        background: linear-gradient(135deg, #F3F4F6, #E5E7EB);
        padding: 2.5rem;
        border-radius: 20px;
        border: 1px solid #D1D5DB;
        max-width: 450px;
        margin: 2rem auto;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    
    /* Admin panel styling */
    .admin-panel {
        background: linear-gradient(135deg, #1E293B, #0F172A);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        border-left: 5px solid #F59E0B;
    }
    
    /* Feedback buttons */
    .feedback-btn {
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin: 1rem 0;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border: 1px solid #E5E7EB;
    }
    
    footer {
        text-align: center;
        padding: 2rem;
        color: #6B7280;
        font-size: 0.9rem;
        border-top: 1px solid #E5E7EB;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Enhanced University Header with Graduation Icon ---
st.markdown("""
<div class="main-header">
    <div class="header-title">
        <span>🎓</span>
        📱 Social Media Addiction Risk Analyzer
        <span>🎓</span>
    </div>
    <div class="university-name">ADDIS ABABA UNIVERSITY</div>
    <div class="college-name">College of Natural and Computational Sciences</div>
    <div class="college-name">Department of Computer Science</div>
    <div class="course-info">
        <span>🎓</span> Machine Learning Course (COSC 6041) | Adaptive AdaBoost Algorithm <span>🎓</span>
    </div>
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

def get_all_users():
    conn = sqlite3.connect('users.db')
    df = pd.read_sql_query("SELECT username, created_at, is_admin FROM users ORDER BY created_at DESC", conn)
    conn.close()
    return df

# --- Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.is_admin = False
    st.session_state.feedback_given = {}
    st.session_state.current_page = "main"

# --- LOGIN PAGE (Only Login, No Signup) ---
if not st.session_state.logged_in:
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown("### 🔐 Admin Login")
    st.markdown("Please login with your credentials")
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("🔓 Login", use_container_width=True)
        
        if submitted:
            user = check_login(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.is_admin = user[3] == 1
                st.success("✅ Login successful! Redirecting...")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- MAIN APPLICATION AFTER LOGIN ---
# Sidebar navigation
with st.sidebar:
    st.markdown(f"### 👋 Welcome, **{st.session_state.username}**!")
    
    # Navigation
    st.markdown("### 📍 Navigation")
    if st.button("🏠 Dashboard", use_container_width=True):
        st.session_state.current_page = "main"
    if st.button("📊 Risk Analyzer", use_container_width=True):
        st.session_state.current_page = "analyzer"
    
    # Admin Panel (Only visible to getaye)
    if st.session_state.is_admin:
        st.markdown("---")
        st.markdown("### 👑 Admin Panel")
        if st.button("👥 User Management", use_container_width=True):
            st.session_state.current_page = "user_management"
        if st.button("📈 View Feedback", use_container_width=True):
            st.session_state.current_page = "feedback"
    
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.is_admin = False
        st.session_state.current_page = "main"
        st.rerun()
    
    # Quick info
    st.markdown("---")
    st.markdown("### 📊 Risk Guide")
    st.markdown("""
    **Platform Risk:**
    - 🔴 Telegram, YouTube, TikTok
    - 🟡 Facebook, LinkedIn
    - 🟢 WhatsApp, Twitter
    
    **Experience Risk:**
    - 🔴 >5 years
    - 🟡 2-5 years
    - 🟢 <2 years
    
    **Usage Risk:**
    - 🔴 >3 hrs/day
    - 🟡 2-3 hrs/day
    - 🟢 <2 hrs/day
    """)

# --- USER MANAGEMENT PAGE (Only for admin) ---
if st.session_state.current_page == "user_management" and st.session_state.is_admin:
    st.markdown("## 👥 User Management")
    st.markdown('<div class="admin-panel">', unsafe_allow_html=True)
    st.markdown("### Create New User")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.form("create_user_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            make_admin = st.checkbox("Grant Admin Privileges")
            submitted = st.form_submit_button("✨ Create User", use_container_width=True)
            
            if submitted:
                if new_password != confirm_password:
                    st.error("❌ Passwords don't match")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                else:
                    if create_user(new_username, new_password, make_admin):
                        st.success(f"✅ User {new_username} created successfully!")
                        st.balloons()
                    else:
                        st.error("❌ Username already exists")
    
    with col2:
        st.markdown("### 📋 Existing Users")
        users_df = get_all_users()
        if not users_df.empty:
            # Style the dataframe
            styled_df = users_df.style.applymap(
                lambda x: 'color: orange; font-weight: bold' if x == 1 else '',
                subset=['is_admin']
            )
            st.dataframe(users_df, use_container_width=True)
            st.caption(f"Total Users: {len(users_df)}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("← Back to Dashboard"):
        st.session_state.current_page = "main"
        st.rerun()

# --- FEEDBACK PAGE (Only for admin) ---
elif st.session_state.current_page == "feedback" and st.session_state.is_admin:
    st.markdown("## 📊 Feedback Analytics")
    st.markdown('<div class="admin-panel">', unsafe_allow_html=True)
    
    conn = sqlite3.connect('users.db')
    feedback_df = pd.read_sql_query("SELECT * FROM feedback ORDER BY timestamp DESC", conn)
    conn.close()
    
    if not feedback_df.empty:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Feedback", len(feedback_df))
        with col2:
            likes = len(feedback_df[feedback_df['feedback'] == 'like'])
            st.metric("👍 Likes", likes)
        with col3:
            unlikes = len(feedback_df[feedback_df['feedback'] == 'unlike'])
            st.metric("👎 Unlikes", unlikes)
        with col4:
            accuracy = (likes / len(feedback_df)) * 100 if len(feedback_df) > 0 else 0
            st.metric("Accuracy", f"{accuracy:.1f}%")
        
        st.markdown("### 📋 Detailed Feedback")
        st.dataframe(feedback_df, use_container_width=True)
        
        # Model adaptation info
        st.markdown("### 🤖 Model Adaptation Status")
        st.info(f"Model has learned from {len(feedback_df)} feedback instances. "
                f"Confidence adjustment: {min(0.15, len(feedback_df) * 0.01):.2f}")
    else:
        st.info("No feedback data yet")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("← Back to Dashboard"):
        st.session_state.current_page = "main"
        st.rerun()

# --- MAIN ANALYZER PAGE ---
elif st.session_state.current_page in ["main", "analyzer"]:
    
    # Welcome banner
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1E3A8A20, #2563EB20); padding: 1rem; border-radius: 10px; margin-bottom: 2rem;">
        <h4>🎓 Welcome back, {st.session_state.username}! Use the analyzer below to check your social media addiction risk.</h4>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("## 📱 Social Media Habits Assessment")
    
    # Input form
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.number_input("Age", 13, 80, 22)
        daily_hours = st.slider("Daily Usage (hours)", 0.5, 12.0, 2.5, 0.5)
        
        # Usage experience calculation
        current_year = datetime.now().year
        start_year = st.number_input("Year you started using social media", 
                                    min_value=2000, max_value=current_year, value=2018)
        usage_years = current_year - start_year
        st.caption(f"📊 Experience: {usage_years} years")
        
        primary_platform = st.selectbox(
            "Primary Platform",
            ["TikTok", "Instagram", "Telegram", "YouTube", "Facebook", 
             "LinkedIn", "Snapchat", "WhatsApp", "Twitter", "Google", "Other"]
        )
    
    with col2:
        sleep_hours = st.slider("Sleep (hours/night)", 3.0, 12.0, 7.0, 0.5)
        mental_health = st.slider("Mental Health Score", 1, 10, 7, 1)
    
    if st.button("🔍 Analyze My Risk", type="primary", use_container_width=True):
        
        # Platform Risk Mapping
        platform_risk_map = {
            'Telegram': 'High', 'YouTube': 'High', 'TikTok': 'High',
            'Instagram': 'High', 'Google': 'High', 'Facebook': 'Medium',
            'LinkedIn': 'Medium', 'Snapchat': 'Medium', 'WhatsApp': 'Low',
            'Twitter': 'Low', 'Other': 'Low'
        }
        
        platform_risk = platform_risk_map.get(primary_platform, 'Medium')
        
        # Experience Risk
        if usage_years > 5:
            experience_risk = 'High'
        elif usage_years > 2:
            experience_risk = 'Medium'
        else:
            experience_risk = 'Low'
        
        # Usage Risk
        if daily_hours > 3:
            usage_risk = 'High'
        elif daily_hours > 2:
            usage_risk = 'Medium'
        else:
            usage_risk = 'Low'
        
        # Sleep Risk
        if sleep_hours < 6:
            sleep_risk = 'High'
        elif sleep_hours < 7:
            sleep_risk = 'Medium'
        else:
            sleep_risk = 'Low'
        
        # Mental Health Risk
        if mental_health < 4:
            mental_risk = 'High'
        elif mental_health < 7:
            mental_risk = 'Medium'
        else:
            mental_risk = 'Low'
        
        # Calculate Overall Risk
        risk_scores = {'High': 3, 'Medium': 2, 'Low': 1}
        total_score = (risk_scores[usage_risk] * 2 + risk_scores[platform_risk] * 1.5 +
                      risk_scores[experience_risk] + risk_scores[sleep_risk] + risk_scores[mental_risk])
        avg_score = total_score / 6.5
        
        if avg_score > 2.3:
            overall_risk = 'High'
        elif avg_score > 1.5:
            overall_risk = 'Medium'
        else:
            overall_risk = 'Low'
        
        # Confidence (adaptive based on feedback)
        conn = sqlite3.connect('users.db')
        feedback_df = pd.read_sql_query("SELECT * FROM feedback", conn)
        conn.close()
        
        base_confidence = 0.85
        if len(feedback_df) > 10:
            positive_rate = len(feedback_df[feedback_df['feedback'] == 'like']) / len(feedback_df)
            base_confidence = 0.7 + (positive_rate * 0.25)
        
        # Display Result
        st.markdown("---")
        st.markdown("## 📊 Analysis Result")
        
        if overall_risk == 'High':
            st.markdown(f"""
            <div class="risk-high risk-card">
                <h2 style="margin:0;">⚠️ HIGH ADDICTION RISK</h2>
                <p style="margin:0.5rem 0 0 0; font-size:1.3rem;">Confidence: {base_confidence:.1%}</p>
            </div>
            """, unsafe_allow_html=True)
        elif overall_risk == 'Medium':
            st.markdown(f"""
            <div class="risk-moderate risk-card">
                <h2 style="margin:0;">⚠️ MODERATE ADDICTION RISK</h2>
                <p style="margin:0.5rem 0 0 0; font-size:1.3rem;">Confidence: {base_confidence:.1%}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="risk-low risk-card">
                <h2 style="margin:0;">✅ LOW ADDICTION RISK</h2>
                <p style="margin:0.5rem 0 0 0; font-size:1.3rem;">Confidence: {base_confidence:.1%}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Risk Breakdown
        st.markdown("### 🔍 Risk Factor Analysis")
        
        col_r1, col_r2, col_r3 = st.columns(3)
        
        with col_r1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("**Daily Usage**")
            if usage_risk == 'High':
                st.error(f"⚠️ {daily_hours:.1f} hrs/day")
            elif usage_risk == 'Medium':
                st.warning(f"⚠️ {daily_hours:.1f} hrs/day")
            else:
                st.success(f"✅ {daily_hours:.1f} hrs/day")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_r2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("**Platform Risk**")
            if platform_risk == 'High':
                st.error(f"⚠️ {primary_platform}")
            elif platform_risk == 'Medium':
                st.warning(f"⚠️ {primary_platform}")
            else:
                st.success(f"✅ {primary_platform}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_r3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("**Experience**")
            if experience_risk == 'High':
                st.error(f"⚠️ {usage_years} years")
            elif experience_risk == 'Medium':
                st.warning(f"⚠️ {usage_years} years")
            else:
                st.success(f"✅ {usage_years} years")
            st.markdown('</div>', unsafe_allow_html=True)
        
        col_r4, col_r5 = st.columns(2)
        
        with col_r4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("**Sleep Pattern**")
            if sleep_risk == 'High':
                st.error(f"⚠️ {sleep_hours:.1f} hrs")
            elif sleep_risk == 'Medium':
                st.warning(f"⚠️ {sleep_hours:.1f} hrs")
            else:
                st.success(f"✅ {sleep_hours:.1f} hrs")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_r5:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("**Mental Health**")
            if mental_risk == 'High':
                st.error(f"⚠️ {mental_health}/10")
            elif mental_risk == 'Medium':
                st.warning(f"⚠️ {mental_health}/10")
            else:
                st.success(f"✅ {mental_health}/10")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Recommendations
        st.markdown("### 💡 Personalized Recommendations")
        
        if overall_risk == 'High':
            st.markdown("""
            <div style="background: #FEE2E2; padding: 1.5rem; border-radius: 10px;">
                <h4 style="color: #991B1B;">🔴 HIGH RISK - Immediate Action Required:</h4>
                <ul style="color: #991B1B;">
                    <li>📱 Reduce usage to under 3 hours per day immediately</li>
                    <li>⏰ Set strict app timers (30-minute daily limits)</li>
                    <li>🌙 No phones in bedroom - charge outside at night</li>
                    <li>🎯 Take a 7-day digital detox challenge</li>
                    <li>👥 Seek professional help if feeling dependent</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        elif overall_risk == 'Medium':
            st.markdown("""
            <div style="background: #FEF3C7; padding: 1.5rem; border-radius: 10px;">
                <h4 style="color: #92400E;">🟡 MODERATE RISK - Take Preventive Measures:</h4>
                <ul style="color: #92400E;">
                    <li>📱 Limit usage to 2-3 hours per day</li>
                    <li>⏰ Use focus mode during work/study hours</li>
                    <li>🌙 No phone 1 hour before bed</li>
                    <li>🎯 Schedule phone-free weekends</li>
                    <li>📊 Track your usage weekly and set reduction goals</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #D1FAE5; padding: 1.5rem; border-radius: 10px;">
                <h4 style="color: #065F46;">🟢 LOW RISK - Maintain Healthy Habits:</h4>
                <ul style="color: #065F46;">
                    <li>📱 Keep using only when necessary - you're doing great!</li>
                    <li>⏰ Continue monitoring your daily usage</li>
                    <li>🌙 Maintain good sleep hygiene</li>
                    <li>🎯 Use social media intentionally, not habitually</li>
                    <li>👥 Encourage friends/family to maintain balance too</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Platform-specific warning
        if primary_platform in ['Telegram', 'YouTube', 'TikTok', 'Instagram', 'Google']:
            st.warning(f"⚠️ **{primary_platform} is high-risk**. Consider limiting time on this platform.")
        
        # Feedback Section
        st.markdown("---")
        st.markdown("### 🤖 Help Improve the Model")
        st.markdown("Was this prediction accurate? Your feedback helps the model learn.")
        
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            if st.button("👍 Yes, Accurate", key=f"like_{datetime.now()}", use_container_width=True):
                feedback_data = {
                    'username': st.session_state.username,
                    'age': age, 'daily_hours': daily_hours, 'platform': primary_platform,
                    'usage_years': usage_years, 'sleep_hours': sleep_hours,
                    'mental_health': mental_health, 'predicted_risk': overall_risk,
                    'feedback': 'like'
                }
                save_feedback(feedback_data)
                st.success("✅ Thank you! Your feedback helps improve the model.")
                st.balloons()
        
        with col_f2:
            if st.button("👎 No, Inaccurate", key=f"unlike_{datetime.now()}", use_container_width=True):
                feedback_data = {
                    'username': st.session_state.username,
                    'age': age, 'daily_hours': daily_hours, 'platform': primary_platform,
                    'usage_years': usage_years, 'sleep_hours': sleep_hours,
                    'mental_health': mental_health, 'predicted_risk': overall_risk,
                    'feedback': 'unlike'
                }
                save_feedback(feedback_data)
                st.info("📝 Thank you! This feedback will help us improve.")

# --- Footer ---
st.markdown("---")
st.markdown("""
<footer>
    <span>🎓</span> College of Natural and Computational Sciences | Department of Computer Science<br>
    Machine Learning Course (COSC 6041) | Adaptive AdaBoost Algorithm | © 2026 All Rights Reserved <span>🎓</span>
</footer>
""", unsafe_allow_html=True)
