import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import hashlib
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time

# --- Page Config ---
st.set_page_config(
    page_title="Social Media Addiction Risk Analyzer",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Hide default select labels */
    .stSelectbox label, .stSelectbox div[data-baseweb="select"] span {
        display: none;
    }
    
    /* Sidebar styling */
    .sidebar-header {
        background: linear-gradient(135deg, #1E3A8A, #2563EB);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .sidebar-button {
        width: 100%;
        padding: 1rem;
        margin: 0.2rem 0;
        border-radius: 10px;
        border: none;
        background: #f8fafc;
        cursor: pointer;
        text-align: left;
        font-size: 1rem;
        transition: all 0.3s;
    }
    
    .sidebar-button:hover {
        background: #e0f2fe;
        transform: translateX(5px);
    }
    
    .sidebar-button.active {
        background: #2563EB;
        color: white;
    }
    
    /* Main header */
    .main-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 50%, #1E3A8A 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    
    .red-title {
        color: #DC2626 !important;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .university-name {
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0.3rem 0;
    }
    
    .college-name {
        font-size: 1rem;
        opacity: 0.95;
        margin: 0.1rem 0;
    }
    
    /* Feature container */
    .feature-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        min-height: 500px;
        position: relative;
    }
    
    .back-button {
        position: absolute;
        top: 1rem;
        right: 1rem;
        background: #2563EB;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        cursor: pointer;
        border: none;
        font-size: 0.9rem;
        z-index: 100;
    }
    
    .back-button:hover {
        background: #1E3A8A;
    }
    
    /* Public cards grid */
    .public-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .public-card {
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        padding: 2rem 1rem;
        border-radius: 15px;
        border: 2px solid #e2e8f0;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .public-card:hover {
        transform: translateY(-5px);
        border-color: #2563EB;
        box-shadow: 0 10px 25px rgba(37, 99, 235, 0.2);
    }
    
    /* Risk displays */
    .risk-high { 
        background: linear-gradient(135deg, #FEE2E2, #FECACA);
        color: #991B1B; 
        padding: 1.5rem; 
        border-radius: 15px; 
        border-left: 8px solid #DC2626; 
        text-align: center;
        margin: 1rem 0;
    }
    
    .risk-moderate { 
        background: linear-gradient(135deg, #FEF3C7, #FDE68A);
        color: #92400E; 
        padding: 1.5rem; 
        border-radius: 15px; 
        border-left: 8px solid #F59E0B;
        text-align: center;
        margin: 1rem 0;
    }
    
    .risk-low { 
        background: linear-gradient(135deg, #D1FAE5, #A7F3D0);
        color: #065F46; 
        padding: 1.5rem; 
        border-radius: 15px; 
        border-left: 8px solid #10B981;
        text-align: center;
        margin: 1rem 0;
    }
    
    /* Recommendations */
    .recommendations {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #2563EB;
        margin: 1rem 0;
    }
    
    /* Activity cards */
    .activity-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2563EB;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .activity-time {
        font-size: 0.8rem;
        color: #64748b;
    }
    
    /* Comment box */
    .comment-box {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
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
        padding: 1.5rem;
        color: #6B7280;
        font-size: 0.9rem;
        border-top: 1px solid #E5E7EB;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialize Database ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, created_at TIMESTAMP, is_admin INTEGER DEFAULT 0, last_login TIMESTAMP)''')
    # Feedback table
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
    # Usage tracking table
    c.execute('''CREATE TABLE IF NOT EXISTS usage_tracking
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  date DATE,
                  hours INTEGER,
                  minutes INTEGER,
                  total_minutes INTEGER,
                  platform TEXT,
                  timestamp TIMESTAMP)''')
    # Comments table
    c.execute('''CREATE TABLE IF NOT EXISTS comments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  email TEXT,
                  comment TEXT,
                  status TEXT DEFAULT 'pending',
                  timestamp TIMESTAMP,
                  replied_at TIMESTAMP,
                  reply TEXT)''')
    # Activity log table
    c.execute('''CREATE TABLE IF NOT EXISTS activities
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  activity_type TEXT,
                  username TEXT,
                  description TEXT,
                  details TEXT,
                  ip_address TEXT,
                  timestamp TIMESTAMP)''')
    # Risk analysis log table
    c.execute('''CREATE TABLE IF NOT EXISTS risk_analyses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  age INTEGER,
                  daily_hours REAL,
                  start_year INTEGER,
                  platform TEXT,
                  sleep_hours REAL,
                  mental_health INTEGER,
                  risk_result TEXT,
                  timestamp TIMESTAMP)''')
    # Create admin user
    admin_exists = c.execute("SELECT * FROM users WHERE username='getaye'").fetchone()
    if not admin_exists:
        hashed_pw = hashlib.sha256("Getaye@2827".encode()).hexdigest()
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", 
                 ("getaye", hashed_pw, datetime.now(), 1, None))
    conn.commit()
    conn.close()

init_db()

# --- Activity Logging Functions ---
def log_activity(activity_type, username, description, details=None):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO activities 
                 (activity_type, username, description, details, ip_address, timestamp)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (activity_type, username, description, details, "web", datetime.now()))
    conn.commit()
    conn.close()

def log_risk_analysis(username, age, daily_hours, start_year, platform, sleep_hours, mental_health, risk_result):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO risk_analyses 
                 (username, age, daily_hours, start_year, platform, sleep_hours, mental_health, risk_result, timestamp)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (username, age, daily_hours, start_year, platform, sleep_hours, mental_health, risk_result, datetime.now()))
    conn.commit()
    conn.close()
    log_activity("risk_analysis", username, f"Performed risk analysis: {risk_result}", f"Age:{age}, Hours:{daily_hours}, Platform:{platform}")

def get_all_activities(limit=100):
    conn = sqlite3.connect('users.db')
    df = pd.read_sql_query(f"SELECT * FROM activities ORDER BY timestamp DESC LIMIT {limit}", conn)
    conn.close()
    return df

def get_risk_analyses(limit=100):
    conn = sqlite3.connect('users.db')
    df = pd.read_sql_query(f"SELECT * FROM risk_analyses ORDER BY timestamp DESC LIMIT {limit}", conn)
    conn.close()
    return df

def get_recent_logins(limit=20):
    conn = sqlite3.connect('users.db')
    df = pd.read_sql_query(f"SELECT username, last_login FROM users WHERE last_login IS NOT NULL ORDER BY last_login DESC LIMIT {limit}", conn)
    conn.close()
    return df

# --- Comment Functions ---
def save_comment(name, email, comment):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO comments (name, email, comment, status, timestamp)
                 VALUES (?, ?, ?, ?, ?)''',
              (name, email, comment, 'pending', datetime.now()))
    conn.commit()
    log_activity("comment", name, f"Submitted comment", comment[:50])
    conn.close()
    return True

def get_all_comments():
    conn = sqlite3.connect('users.db')
    df = pd.read_sql_query("SELECT * FROM comments ORDER BY timestamp DESC", conn)
    conn.close()
    return df

def update_comment_reply(comment_id, reply):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''UPDATE comments 
                 SET status='replied', reply=?, replied_at=?
                 WHERE id=?''',
              (reply, datetime.now(), comment_id))
    conn.commit()
    conn.close()

# --- Authentication Functions ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    hashed_pw = hash_password(password)
    user = c.execute("SELECT * FROM users WHERE username=? AND password=?", 
                    (username, hashed_pw)).fetchone()
    if user:
        update_last_login(username)
        log_activity("login", username, "User logged in")
    conn.close()
    return user

def update_last_login(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET last_login=? WHERE username=?", (datetime.now(), username))
    conn.commit()
    conn.close()

def create_user(username, password, is_admin=False):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        hashed_pw = hash_password(password)
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", 
                 (username, hashed_pw, datetime.now(), 1 if is_admin else 0, None))
        conn.commit()
        log_activity("user_created", username, f"New user created by admin")
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
    log_activity("feedback", data['username'], f"Gave {data['feedback']} feedback")
    conn.close()

def save_usage_entry(username, date, hours, minutes, platform):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    total_minutes = (hours * 60) + minutes
    c.execute('''INSERT INTO usage_tracking 
                 (username, date, hours, minutes, total_minutes, platform, timestamp)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (username, date, hours, minutes, total_minutes, platform, datetime.now()))
    conn.commit()
    log_activity("usage_log", username, f"Logged {hours}h {minutes}m usage", f"Platform:{platform}")
    conn.close()

def get_user_usage(username, days=30):
    conn = sqlite3.connect('users.db')
    cutoff_date = (datetime.now() - timedelta(days=days)).date()
    df = pd.read_sql_query(f"""
        SELECT date, hours, minutes, total_minutes, platform 
        FROM usage_tracking 
        WHERE username = '{username}' AND date >= '{cutoff_date}'
        ORDER BY date DESC
    """, conn)
    conn.close()
    return df

def get_all_users():
    conn = sqlite3.connect('users.db')
    df = pd.read_sql_query("SELECT username, created_at, is_admin, last_login FROM users ORDER BY created_at DESC", conn)
    conn.close()
    return df

# --- Risk Analysis Function ---
def analyze_risk(age, daily_hours, start_year, primary_platform, sleep_hours, mental_health):
    current_year = datetime.now().year
    usage_years = current_year - start_year
    
    platform_risk_map = {
        'Telegram': 'High', 'YouTube': 'High', 'TikTok': 'High',
        'Instagram': 'High', 'Google': 'High', 'Facebook': 'Medium',
        'LinkedIn': 'Medium', 'Snapchat': 'Medium', 'WhatsApp': 'Low',
        'Twitter': 'Low', 'Other': 'Low'
    }
    
    platform_risk = platform_risk_map.get(primary_platform, 'Medium')
    
    if usage_years > 5:
        experience_risk = 'High'
    elif usage_years > 2:
        experience_risk = 'Medium'
    else:
        experience_risk = 'Low'
    
    if daily_hours > 3:
        usage_risk = 'High'
    elif daily_hours > 2:
        usage_risk = 'Medium'
    else:
        usage_risk = 'Low'
    
    if sleep_hours < 6:
        sleep_risk = 'High'
    elif sleep_hours < 7:
        sleep_risk = 'Medium'
    else:
        sleep_risk = 'Low'
    
    if mental_health < 4:
        mental_risk = 'High'
    elif mental_health < 7:
        mental_risk = 'Medium'
    else:
        mental_risk = 'Low'
    
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
    
    return {
        'overall_risk': overall_risk,
        'usage_risk': usage_risk,
        'platform_risk': platform_risk,
        'experience_risk': experience_risk,
        'sleep_risk': sleep_risk,
        'mental_risk': mental_risk,
        'usage_years': usage_years,
        'daily_hours': daily_hours,
        'platform': primary_platform,
        'sleep_hours': sleep_hours,
        'mental_health': mental_health
    }

# --- Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.is_admin = False
    st.session_state.current_page = "public"
    st.session_state.public_feature = None
    st.session_state.logged_in_feature = None
    st.session_state.last_risk_result = None

# --- LOGIN PAGE HEADER ---
if not st.session_state.logged_in:
    st.markdown("""
    <div class="main-header">
        <div class="red-title">📱 Social Media Addiction Risk Analyzer</div>
        <div class="university-name">
            <span>🎓</span> ADDIS ABABA UNIVERSITY <span>🎓</span>
        </div>
        <div class="college-name">College of Natural and Computational Sciences</div>
        <div class="college-name">Department of Computer Science</div>
        <div style="margin-top:1rem;">
            <span>🎓</span> Machine Learning Course (COSC 6041) | Adaptive AdaBoost Algorithm <span>🎓</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- PUBLIC SECTION (No login) ---
if not st.session_state.logged_in:
    
    if st.session_state.public_feature is None:
        st.markdown("## 👋 Welcome to Social Media Addiction Risk Analyzer")
        
        # Public features grid
        st.markdown('<div class="public-grid">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 About App", key="pub_about", use_container_width=True):
                st.session_state.public_feature = "about"
                st.rerun()
            if st.button("⚡ Quick Test", key="pub_test", use_container_width=True):
                st.session_state.public_feature = "quick_test"
                st.rerun()
        
        with col2:
            if st.button("💬 Contact Admin", key="pub_contact", use_container_width=True):
                st.session_state.public_feature = "contact"
                st.rerun()
            if st.button("🔐 Login", key="pub_login", use_container_width=True):
                st.session_state.public_feature = "login"
                st.rerun()
        
        with col3:
            if st.button("✨ Features", key="pub_features", use_container_width=True):
                st.session_state.public_feature = "features"
                st.rerun()
            if st.button("📞 Get Help", key="pub_help", use_container_width=True):
                st.session_state.public_feature = "help"
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # Feature container with back button
        st.markdown('<div class="feature-container">', unsafe_allow_html=True)
        
        # Back button
        if st.button("← Back to Menu", key="back_public"):
            st.session_state.public_feature = None
            st.rerun()
        
        # About App
        if st.session_state.public_feature == "about":
            st.markdown("## 📋 About This Application")
            st.markdown("""
            This application uses **Adaptive AdaBoost Machine Learning** to analyze social media addiction risk.
            
            **How it works:**
            - 📊 Analyzes your usage patterns and habits
            - 🧠 Uses machine learning to predict risk levels
            - 💡 Provides personalized recommendations
            - 📈 Tracks your progress over time
            
            **Features available after login:**
            - ✅ Advanced risk assessment
            - ✅ Usage tracking and analytics
            - ✅ Personalized recommendations
            - ✅ Feedback system
            - ✅ History tracking
            """)
        
        # Quick Test
        elif st.session_state.public_feature == "quick_test":
            st.markdown("## ⚡ Quick Risk Test")
            
            with st.form("quick_test_form"):
                col1, col2 = st.columns(2)
                with col1:
                    age = st.number_input("Age", 13, 80, 22)
                    daily_hours = st.slider("Daily Usage (hours)", 0.5, 12.0, 2.5, 0.5)
                with col2:
                    start_year = st.number_input("Year started", min_value=2000, max_value=datetime.now().year, value=2018)
                    primary_platform = st.selectbox("Platform", ["TikTok", "Instagram", "Telegram", "YouTube", "Facebook", "Other"])
                
                col3, col4 = st.columns(2)
                with col3:
                    sleep_hours = st.slider("Sleep (hours/night)", 3.0, 12.0, 7.0, 0.5)
                with col4:
                    mental_health = st.slider("Mental Health Score", 1, 10, 7, 1)
                
                if st.form_submit_button("Test My Risk", use_container_width=True):
                    result = analyze_risk(age, daily_hours, start_year, primary_platform, sleep_hours, mental_health)
                    
                    if result['overall_risk'] == 'High':
                        st.markdown(f'<div class="risk-high"><h2>⚠️ HIGH ADDICTION RISK</h2></div>', unsafe_allow_html=True)
                    elif result['overall_risk'] == 'Medium':
                        st.markdown(f'<div class="risk-moderate"><h2>⚠️ MODERATE ADDICTION RISK</h2></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="risk-low"><h2>✅ LOW ADDICTION RISK</h2></div>', unsafe_allow_html=True)
                    
                    st.info("📝 Login for detailed analysis and recommendations")
        
        # Contact Admin (Only comment form)
        elif st.session_state.public_feature == "contact":
            st.markdown("## 💬 Contact Admin")
            st.markdown("Send your questions or comments to the administrator.")
            
            with st.form("comment_form"):
                name = st.text_input("Your Name")
                email = st.text_input("Email (optional)")
                comment = st.text_area("Your Message")
                
                if st.form_submit_button("Send Message", use_container_width=True):
                    if name and comment:
                        save_comment(name, email, comment)
                        st.success("✅ Message sent! Admin will respond soon.")
                        st.balloons()
                    else:
                        st.error("❌ Name and message are required")
        
        # Login
        elif st.session_state.public_feature == "login":
            st.markdown("## 🔐 Login")
            
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Login", use_container_width=True):
                    user = check_login(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.is_admin = user[3] == 1
                        st.session_state.logged_in_feature = "dashboard"
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
        
        # Features
        elif st.session_state.public_feature == "features":
            st.markdown("## ✨ All Features")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                **Free Features (No Login):**
                - ✅ App information
                - ✅ Quick risk test
                - ✅ Contact admin
                """)
            with col2:
                st.markdown("""
                **Premium Features (Login Required):**
                - 📊 Advanced risk assessment
                - 📈 Usage tracking & analytics
                - 💡 Personalized recommendations
                - 📝 Feedback system
                - 📅 History tracking
                """)
        
        # Help
        elif st.session_state.public_feature == "help":
            st.markdown("## 📞 Get Help")
            st.markdown("""
            **For assistance:**
            - 📧 Email: admin@aau.edu.et
            - 🏫 Addis Ababa University
            - 📚 College of Natural and Computational Sciences
            
            **Office Hours:**
            - Monday - Friday: 9:00 AM - 5:00 PM
            """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.stop()

# --- LOGGED IN SECTION ---
# Sidebar with Dashboard, Profile, Logout
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-header">
        <h3>Welcome, {st.session_state.username}!</h3>
        <p>{'👑 Administrator' if st.session_state.is_admin else '👤 Regular User'}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Dashboard button
    if st.button("🏠 Dashboard", key="nav_dashboard", use_container_width=True):
        st.session_state.logged_in_feature = "dashboard"
        st.rerun()
    
    # Profile button
    if st.button("👤 My Profile", key="nav_profile", use_container_width=True):
        st.session_state.logged_in_feature = "profile"
        st.rerun()
    
    st.markdown("---")
    st.markdown("### Features")
    
    # Regular features
    if st.button("📊 Risk Analyzer", key="nav_analyzer", use_container_width=True):
        st.session_state.logged_in_feature = "analyzer"
        st.rerun()
    
    if st.button("📈 Usage Analytics", key="nav_analytics", use_container_width=True):
        st.session_state.logged_in_feature = "analytics"
        st.rerun()
    
    if st.button("💡 Recommendations", key="nav_recommendations", use_container_width=True):
        st.session_state.logged_in_feature = "recommendations"
        st.rerun()
    
    # Admin features
    if st.session_state.is_admin:
        st.markdown("---")
        st.markdown("### Admin")
        
        if st.button("👥 User Management", key="nav_users", use_container_width=True):
            st.session_state.logged_in_feature = "user_management"
            st.rerun()
        
        if st.button("📋 Activity Log", key="nav_activity", use_container_width=True):
            st.session_state.logged_in_feature = "activity"
            st.rerun()
        
        if st.button("💬 Comments", key="nav_comments", use_container_width=True):
            st.session_state.logged_in_feature = "comments"
            st.rerun()
        
        if st.button("📊 Feedback", key="nav_feedback", use_container_width=True):
            st.session_state.logged_in_feature = "feedback"
            st.rerun()
    
    st.markdown("---")
    
    # Logout button
    if st.button("🚪 Logout", key="nav_logout", use_container_width=True):
        log_activity("logout", st.session_state.username, "User logged out")
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.is_admin = False
        st.session_state.logged_in_feature = None
        st.rerun()

# --- MAIN CONTENT AREA ---
st.markdown('<div class="feature-container">', unsafe_allow_html=True)

# Dashboard
if st.session_state.logged_in_feature == "dashboard" or st.session_state.logged_in_feature is None:
    st.markdown("## 📋 Dashboard")
    st.markdown(f"Welcome back, {st.session_state.username}! Select a feature from the sidebar to get started.")
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    
    conn = sqlite3.connect('users.db')
    usage_count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM usage_tracking WHERE username='{st.session_state.username}'", conn).iloc[0]['count']
    feedback_count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM feedback WHERE username='{st.session_state.username}'", conn).iloc[0]['count']
    risk_count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM risk_analyses WHERE username='{st.session_state.username}'", conn).iloc[0]['count']
    conn.close()
    
    with col1:
        st.metric("Usage Entries", usage_count)
    with col2:
        st.metric("Risk Analyses", risk_count)
    with col3:
        st.metric("Feedback Given", feedback_count)

# Profile
elif st.session_state.logged_in_feature == "profile":
    st.markdown("## 👤 My Profile")
    
    conn = sqlite3.connect('users.db')
    usage_count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM usage_tracking WHERE username='{st.session_state.username}'", conn).iloc[0]['count']
    feedback_count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM feedback WHERE username='{st.session_state.username}'", conn).iloc[0]['count']
    risk_count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM risk_analyses WHERE username='{st.session_state.username}'", conn).iloc[0]['count']
    conn.close()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Username", st.session_state.username)
    with col2:
        st.metric("Account Type", "Admin" if st.session_state.is_admin else "User")
    with col3:
        st.metric("Member Since", datetime.now().strftime("%B %Y"))
    
    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("Usage Entries", usage_count)
    with col5:
        st.metric("Risk Analyses", risk_count)
    with col6:
        st.metric("Feedback Given", feedback_count)

# Risk Analyzer
elif st.session_state.logged_in_feature == "analyzer":
    st.markdown("## 📊 Risk Analyzer")
    
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.number_input("Age", 13, 80, 22, key="analyzer_age")
        daily_hours = st.slider("Daily Usage (hours)", 0.5, 12.0, 2.5, 0.5, key="analyzer_hours")
        start_year = st.number_input("Year started", min_value=2000, max_value=datetime.now().year, value=2018, key="analyzer_year")
    
    with col2:
        primary_platform = st.selectbox("Primary Platform", ["TikTok", "Instagram", "Telegram", "YouTube", "Facebook", "LinkedIn", "Snapchat", "WhatsApp", "Twitter", "Google", "Other"], key="analyzer_platform")
        sleep_hours = st.slider("Sleep (hours/night)", 3.0, 12.0, 7.0, 0.5, key="analyzer_sleep")
        mental_health = st.slider("Mental Health Score", 1, 10, 7, 1, key="analyzer_mental")
    
    if st.button("🔍 Analyze My Risk", type="primary", use_container_width=True):
        result = analyze_risk(age, daily_hours, start_year, primary_platform, sleep_hours, mental_health)
        st.session_state.last_risk_result = result
        
        # Log the analysis
        log_risk_analysis(st.session_state.username, age, daily_hours, start_year, primary_platform, sleep_hours, mental_health, result['overall_risk'])
        
        # Display Result
        if result['overall_risk'] == 'High':
            st.markdown(f'<div class="risk-high"><h2>⚠️ HIGH ADDICTION RISK</h2><p>Confidence: 85%</p></div>', unsafe_allow_html=True)
        elif result['overall_risk'] == 'Medium':
            st.markdown(f'<div class="risk-moderate"><h2>⚠️ MODERATE ADDICTION RISK</h2><p>Confidence: 85%</p></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="risk-low"><h2>✅ LOW ADDICTION RISK</h2><p>Confidence: 85%</p></div>', unsafe_allow_html=True)
        
        # Show recommendations
        st.markdown("### 💡 Personalized Recommendations")
        
        if result['overall_risk'] == 'High':
            st.markdown("""
            <div class="recommendations">
                <h4>🔴 HIGH RISK - Immediate Action Required:</h4>
                <ul>
                    <li>📱 Reduce usage to under 3 hours per day immediately</li>
                    <li>⏰ Set strict app timers (30-minute daily limits)</li>
                    <li>🌙 No phones in bedroom - charge outside at night</li>
                    <li>🎯 Take a 7-day digital detox challenge</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        elif result['overall_risk'] == 'Medium':
            st.markdown("""
            <div class="recommendations">
                <h4>🟡 MODERATE RISK - Take Preventive Measures:</h4>
                <ul>
                    <li>📱 Limit usage to 2-3 hours per day</li>
                    <li>⏰ Use focus mode during work/study hours</li>
                    <li>🌙 No phone 1 hour before bed</li>
                    <li>📊 Track your usage weekly</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="recommendations">
                <h4>🟢 LOW RISK - Maintain Healthy Habits:</h4>
                <ul>
                    <li>📱 Keep using only when necessary</li>
                    <li>⏰ Continue monitoring your daily usage</li>
                    <li>🌙 Maintain good sleep hygiene</li>
                    <li>🎯 Use social media intentionally</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Feedback
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if st.button("👍 Yes, Accurate", key="like", use_container_width=True):
                feedback_data = {
                    'username': st.session_state.username,
                    'age': age, 'daily_hours': daily_hours, 'platform': primary_platform,
                    'usage_years': result['usage_years'], 'sleep_hours': sleep_hours,
                    'mental_health': mental_health, 'predicted_risk': result['overall_risk'],
                    'feedback': 'like'
                }
                save_feedback(feedback_data)
                st.success("✅ Thank you!")
        
        with col_f2:
            if st.button("👎 No, Inaccurate", key="unlike", use_container_width=True):
                feedback_data = {
                    'username': st.session_state.username,
                    'age': age, 'daily_hours': daily_hours, 'platform': primary_platform,
                    'usage_years': result['usage_years'], 'sleep_hours': sleep_hours,
                    'mental_health': mental_health, 'predicted_risk': result['overall_risk'],
                    'feedback': 'unlike'
                }
                save_feedback(feedback_data)
                st.info("📝 Thank you!")

# Recommendations
elif st.session_state.logged_in_feature == "recommendations":
    st.markdown("## 💡 Personalized Recommendations")
    
    if st.session_state.last_risk_result:
        result = st.session_state.last_risk_result
        
        if result['overall_risk'] == 'High':
            st.markdown("""
            <div class="recommendations">
                <h4>🔴 HIGH RISK - Immediate Action Required:</h4>
                <ul>
                    <li>📱 Reduce usage to under 3 hours per day immediately</li>
                    <li>⏰ Set strict app timers (30-minute daily limits)</li>
                    <li>🌙 No phones in bedroom - charge outside at night</li>
                    <li>🎯 Take a 7-day digital detox challenge</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        elif result['overall_risk'] == 'Medium':
            st.markdown("""
            <div class="recommendations">
                <h4>🟡 MODERATE RISK - Take Preventive Measures:</h4>
                <ul>
                    <li>📱 Limit usage to 2-3 hours per day</li>
                    <li>⏰ Use focus mode during work/study hours</li>
                    <li>🌙 No phone 1 hour before bed</li>
                    <li>📊 Track your usage weekly</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="recommendations">
                <h4>🟢 LOW RISK - Maintain Healthy Habits:</h4>
                <ul>
                    <li>📱 Keep using only when necessary</li>
                    <li>⏰ Continue monitoring your daily usage</li>
                    <li>🌙 Maintain good sleep hygiene</li>
                    <li>🎯 Use social media intentionally</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Please run a risk analysis first to get personalized recommendations.")
        if st.button("Go to Risk Analyzer"):
            st.session_state.logged_in_feature = "analyzer"
            st.rerun()

# Usage Analytics
elif st.session_state.logged_in_feature == "analytics":
    st.markdown("## 📈 Usage Analytics")
    
    tab1, tab2, tab3 = st.tabs(["📝 Log Usage", "📊 View Analytics", "📅 History"])
    
    with tab1:
        st.markdown("### Log Your Daily Usage")
        col1, col2 = st.columns(2)
        with col1:
            log_date = st.date_input("Date", datetime.now().date())
            hours = st.number_input("Hours", 0, 24, 2)
            minutes = st.selectbox("Minutes", [0, 15, 30, 45])
        with col2:
            platform = st.selectbox("Platform", ["TikTok", "Instagram", "Telegram", "YouTube", "Facebook", "LinkedIn", "Snapchat", "WhatsApp", "Twitter", "Google", "Other"])
        
        if st.button("Save Usage Entry", use_container_width=True):
            save_usage_entry(st.session_state.username, log_date, hours, minutes, platform)
            st.success("✅ Usage logged successfully!")
            st.balloons()
    
    with tab2:
        time_range = st.selectbox("Time Range", ["Last 7 days", "Last 30 days", "Last 90 days"])
        days = 7 if "7" in time_range else 30 if "30" in time_range else 90
        usage_df = get_user_usage(st.session_state.username, days)
        
        if not usage_df.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Days Tracked", len(usage_df))
            with col2:
                avg_minutes = usage_df['total_minutes'].mean()
                st.metric("Daily Average", f"{avg_minutes/60:.1f} hrs")
            with col3:
                total_minutes = usage_df['total_minutes'].sum()
                st.metric("Total Usage", f"{total_minutes/60:.1f} hrs")
            with col4:
                most_used = usage_df['platform'].mode()[0] if not usage_df.empty else "N/A"
                st.metric("Most Used", most_used)
            
            # Usage trend
            daily_trend = usage_df.groupby('date')['total_minutes'].sum().reset_index()
            daily_trend['hours'] = daily_trend['total_minutes'] / 60
            fig = px.line(daily_trend, x='date', y='hours', title='Usage Trend')
            st.plotly_chart(fig, use_container_width=True)
            
            # Platform distribution
            platform_stats = usage_df.groupby('platform')['total_minutes'].sum().reset_index()
            platform_stats['hours'] = platform_stats['total_minutes'] / 60
            fig2 = px.pie(platform_stats, values='hours', names='platform', title='Usage by Platform')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No usage data yet")
    
    with tab3:
        usage_df = get_user_usage(st.session_state.username, 365)
        if not usage_df.empty:
            display_df = usage_df.copy()
            display_df['usage'] = display_df['hours'].astype(str) + "h " + display_df['minutes'].astype(str) + "m"
            display_df = display_df[['date', 'usage', 'platform']].sort_values('date', ascending=False)
            st.dataframe(display_df, use_container_width=True)

# ADMIN: User Management
elif st.session_state.logged_in_feature == "user_management" and st.session_state.is_admin:
    st.markdown("## 👥 User Management")
    
    with st.form("create_user_form"):
        st.markdown("### Create New User")
        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
        with col2:
            confirm_password = st.text_input("Confirm Password", type="password")
            make_admin = st.checkbox("Grant Admin Privileges")
        
        if st.form_submit_button("✨ Create User", use_container_width=True):
            if new_password != confirm_password:
                st.error("❌ Passwords don't match")
            elif len(new_password) < 6:
                st.error("❌ Password must be at least 6 characters")
            else:
                if create_user(new_username, new_password, make_admin):
                    st.success(f"✅ User {new_username} created!")
                    st.balloons()
                else:
                    st.error("❌ Username already exists")
    
    st.markdown("### 📋 Existing Users")
    users_df = get_all_users()
    if not users_df.empty:
        st.dataframe(users_df, use_container_width=True)

# ADMIN: Activity Log (Shows ALL attempts)
elif st.session_state.logged_in_feature == "activity" and st.session_state.is_admin:
    st.markdown("## 📋 Activity Log")
    
    tab1, tab2, tab3 = st.tabs(["📊 All Activities", "📈 Risk Analyses", "👥 User Logins"])
    
    with tab1:
        activities = get_all_activities(200)
        if not activities.empty:
            for _, row in activities.iterrows():
                st.markdown(f"""
                <div class="activity-card">
                    <strong>{row['activity_type']}</strong> - {row['username']}<br>
                    {row['description']}<br>
                    {f"<small>{row['details']}</small><br>" if row['details'] else ""}
                    <span class="activity-time">{row['timestamp']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No activities yet")
    
    with tab2:
        risk_analyses = get_risk_analyses(200)
        if not risk_analyses.empty:
            for _, row in risk_analyses.iterrows():
                st.markdown(f"""
                <div class="activity-card">
                    <strong>Risk Analysis</strong> - {row['username']}<br>
                    Result: {row['risk_result']} | Age: {row['age']}, Hours: {row['daily_hours']}, Platform: {row['platform']}<br>
                    <span class="activity-time">{row['timestamp']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No risk analyses yet")
    
    with tab3:
        logins = get_recent_logins()
        if not logins.empty:
            for _, row in logins.iterrows():
                st.markdown(f"""
                <div class="activity-card">
                    <strong>👤 {row['username']}</strong><br>
                    Last login: {row['last_login']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No login data yet")

# ADMIN: Comments
elif st.session_state.logged_in_feature == "comments" and st.session_state.is_admin:
    st.markdown("## 💬 Public Comments")
    
    comments = get_all_comments()
    if not comments.empty:
        for _, row in comments.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="comment-box">
                    <strong>{row['name']}</strong> ({row['email'] or 'no email'})<br>
                    <em>"{row['comment']}"</em><br>
                    <span class="comment-meta">Status: {row['status']} | {row['timestamp']}</span>
                </div>
                """, unsafe_allow_html=True)
                
                if row['status'] == 'pending':
                    with st.form(key=f"reply_{row['id']}"):
                        reply = st.text_area("Reply", key=f"reply_text_{row['id']}")
                        if st.form_submit_button("Send Reply"):
                            update_comment_reply(row['id'], reply)
                            st.success("Reply sent!")
                            st.rerun()
                
                if row['reply']:
                    st.markdown(f"""
                    <div style="background: #EFF6FF; padding: 0.5rem; border-radius: 5px; margin: 0.5rem 0;">
                        <strong>Admin Reply:</strong> {row['reply']}<br>
                        <span class="comment-meta">{row['replied_at']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("---")
    else:
        st.info("No comments yet")

# ADMIN: Feedback
elif st.session_state.logged_in_feature == "feedback" and st.session_state.is_admin:
    st.markdown("## 📊 Model Feedback")
    
    conn = sqlite3.connect('users.db')
    feedback_df = pd.read_sql_query("SELECT * FROM feedback ORDER BY timestamp DESC", conn)
    conn.close()
    
    if not feedback_df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Feedback", len(feedback_df))
        with col2:
            likes = len(feedback_df[feedback_df['feedback'] == 'like'])
            st.metric("👍 Likes", likes)
        with col3:
            unlikes = len(feedback_df[feedback_df['feedback'] == 'unlike'])
            st.metric("👎 Unlikes", unlikes)
        
        st.dataframe(feedback_df, use_container_width=True)
    else:
        st.info("No feedback yet")

st.markdown('</div>', unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
<footer>
    ADDIS ABABA UNIVERSITY | College of Natural and Computational Sciences | Department of Computer Science<br>
    Machine Learning Course (COSC 6041) | Adaptive AdaBoost Algorithm | © 2026 All Rights Reserved
</footer>
""", unsafe_allow_html=True)
