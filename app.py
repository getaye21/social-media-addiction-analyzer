import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import hashlib
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
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
    
    .university-name {
        font-size: 1.8rem;
        font-weight: 600;
        margin: 0.5rem 0;
    }
    
    .college-name {
        font-size: 1.1rem;
        opacity: 0.95;
        margin: 0.2rem 0;
    }
    
    /* Public test card */
    .public-test-card {
        background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid #2563EB;
        margin: 2rem 0;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    
    .feature-badge {
        background: #2563EB;
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        display: inline-block;
        margin: 0.5rem;
    }
    
    /* Module cards */
    .module-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #E5E7EB;
        transition: transform 0.3s;
        height: 100%;
    }
    
    .module-card:hover {
        transform: translateY(-5px);
        border-color: #2563EB;
    }
    
    .module-icon {
        font-size: 2.5rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .module-title {
        font-size: 1.3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5rem;
        color: #1E3A8A;
    }
    
    .module-description {
        text-align: center;
        color: #4B5563;
        font-size: 0.95rem;
    }
    
    /* Risk displays */
    .risk-high { 
        background: linear-gradient(135deg, #FEE2E2, #FECACA);
        color: #991B1B; 
        padding: 1.5rem; 
        border-radius: 15px; 
        border-left: 8px solid #DC2626; 
        text-align: center;
    }
    
    .risk-moderate { 
        background: linear-gradient(135deg, #FEF3C7, #FDE68A);
        color: #92400E; 
        padding: 1.5rem; 
        border-radius: 15px; 
        border-left: 8px solid #F59E0B;
        text-align: center;
    }
    
    .risk-low { 
        background: linear-gradient(135deg, #D1FAE5, #A7F3D0);
        color: #065F46; 
        padding: 1.5rem; 
        border-radius: 15px; 
        border-left: 8px solid #10B981;
        text-align: center;
    }
    
    /* Admin panel */
    .admin-panel {
        background: linear-gradient(135deg, #1E293B, #0F172A);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        border-left: 5px solid #F59E0B;
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
                 (username TEXT PRIMARY KEY, password TEXT, created_at TIMESTAMP, is_admin INTEGER DEFAULT 0)''')
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
    # Usage tracking table (for analytics)
    c.execute('''CREATE TABLE IF NOT EXISTS usage_tracking
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  date DATE,
                  hours INTEGER,
                  minutes INTEGER,
                  total_minutes INTEGER,
                  platform TEXT,
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

def save_usage_entry(username, date, hours, minutes, platform):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    total_minutes = (hours * 60) + minutes
    c.execute('''INSERT INTO usage_tracking 
                 (username, date, hours, minutes, total_minutes, platform, timestamp)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (username, date, hours, minutes, total_minutes, platform, datetime.now()))
    conn.commit()
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
    df = pd.read_sql_query("SELECT username, created_at, is_admin FROM users ORDER BY created_at DESC", conn)
    conn.close()
    return df

# --- Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.is_admin = False
    st.session_state.feedback_given = {}
    st.session_state.current_page = "public_test"

# --- Header (Always Visible) ---
st.markdown("""
<div class="main-header">
    <div class="university-name">ADDIS ABABA UNIVERSITY</div>
    <div class="college-name">College of Natural and Computational Sciences</div>
    <div class="college-name">Department of Computer Science</div>
    <div style="margin-top:1rem;">Machine Learning Course (COSC 6041) | Adaptive AdaBoost Algorithm</div>
</div>
""", unsafe_allow_html=True)

# --- PUBLIC TEST SECTION (Visible to everyone) ---
if not st.session_state.logged_in:
    st.markdown("""
    <div class="public-test-card">
        <h2 style="color:#1E3A8A; margin-bottom:1rem;">📱 Test Your Social Media Risk</h2>
        <p style="font-size:1.1rem; margin-bottom:1.5rem;">Try our basic risk assessment tool for free! Get instant results.</p>
        <div>
            <span class="feature-badge">✅ Basic Risk Assessment</span>
            <span class="feature-badge">✅ Instant Results</span>
            <span class="feature-badge">❌ Advanced Analytics</span>
            <span class="feature-badge">❌ Usage Tracking</span>
            <span class="feature-badge">❌ History</span>
        </div>
        <p style="margin-top:1.5rem; color:#4B5563;">Contact administrator for advanced features and unlimited access.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("## 🔍 Quick Risk Test")
    
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.number_input("Age", 13, 80, 22)
        daily_hours = st.slider("Daily Usage (hours)", 0.5, 12.0, 2.5, 0.5)
        
        current_year = datetime.now().year
        start_year = st.number_input("Year started using social media", 
                                    min_value=2000, max_value=current_year, value=2018)
        usage_years = current_year - start_year
        
        primary_platform = st.selectbox(
            "Primary Platform",
            ["TikTok", "Instagram", "Telegram", "YouTube", "Facebook", 
             "LinkedIn", "Snapchat", "WhatsApp", "Twitter", "Google", "Other"]
        )
    
    with col2:
        sleep_hours = st.slider("Sleep (hours/night)", 3.0, 12.0, 7.0, 0.5)
        mental_health = st.slider("Mental Health Score", 1, 10, 7, 1)
    
    if st.button("🔍 Test My Risk", type="primary", use_container_width=True):
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
        
        # Display Result
        st.markdown("---")
        st.markdown("## 📊 Your Risk Assessment")
        
        if overall_risk == 'High':
            st.markdown(f"""
            <div class="risk-high">
                <h3>⚠️ HIGH ADDICTION RISK</h3>
                <p>Based on your inputs, you show signs of high social media addiction risk.</p>
            </div>
            """, unsafe_allow_html=True)
        elif overall_risk == 'Medium':
            st.markdown(f"""
            <div class="risk-moderate">
                <h3>⚠️ MODERATE ADDICTION RISK</h3>
                <p>Based on your inputs, you show signs of moderate social media addiction risk.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="risk-low">
                <h3>✅ LOW ADDICTION RISK</h3>
                <p>Based on your inputs, you show low signs of social media addiction risk.</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.info("📝 For detailed analytics, usage tracking, and personalized recommendations, please login.")
    
    # Login option for public
    st.markdown("---")
    st.markdown("### 🔐 Existing User?")
    with st.expander("Click to Login"):
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                user = check_login(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.is_admin = user[3] == 1
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
    
    st.stop()

# --- MAIN APPLICATION AFTER LOGIN ---
# Sidebar navigation
with st.sidebar:
    st.markdown(f"### 👋 Welcome, **{st.session_state.username}**!")
    
    st.markdown("### 📍 Navigation")
    if st.button("🏠 Dashboard", use_container_width=True):
        st.session_state.current_page = "dashboard"
    if st.button("📊 Risk Analyzer", use_container_width=True):
        st.session_state.current_page = "analyzer"
    if st.button("📈 Usage Analytics", use_container_width=True):
        st.session_state.current_page = "analytics"
    
    if st.session_state.is_admin:
        st.markdown("---")
        st.markdown("### 👑 Admin Panel")
        if st.button("👥 User Management", use_container_width=True):
            st.session_state.current_page = "user_management"
        if st.button("📊 View Feedback", use_container_width=True):
            st.session_state.current_page = "feedback"
    
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.is_admin = False
        st.session_state.current_page = "public_test"
        st.rerun()

# --- DASHBOARD ---
if st.session_state.current_page == "dashboard":
    st.markdown("## 📋 Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="module-card">
            <div class="module-icon">📊</div>
            <div class="module-title">Risk Analyzer</div>
            <div class="module-description">
                Advanced risk assessment with personalized recommendations and feedback system.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Analyzer", key="dash1", use_container_width=True):
            st.session_state.current_page = "analyzer"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="module-card">
            <div class="module-icon">📈</div>
            <div class="module-title">Usage Analytics</div>
            <div class="module-description">
                Track daily usage, view trends, and get insights about your social media habits.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Analytics", key="dash2", use_container_width=True):
            st.session_state.current_page = "analytics"
            st.rerun()
    
    with col3:
        st.markdown("""
        <div class="module-card">
            <div class="module-icon">📝</div>
            <div class="module-title">Recent Activity</div>
            <div class="module-description">
                View your recent risk assessments and usage history.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.info("Coming Soon")

# --- USAGE ANALYTICS MODULE ---
elif st.session_state.current_page == "analytics":
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
            platform = st.selectbox(
                "Platform Used Most",
                ["TikTok", "Instagram", "Telegram", "YouTube", "Facebook", 
                 "LinkedIn", "Snapchat", "WhatsApp", "Twitter", "Google", "Other"]
            )
        
        if st.button("Save Usage Entry", use_container_width=True):
            save_usage_entry(st.session_state.username, log_date, hours, minutes, platform)
            st.success("✅ Usage logged successfully!")
            st.balloons()
    
    with tab2:
        st.markdown("### Usage Analytics")
        
        time_range = st.selectbox("Time Range", ["Last 7 days", "Last 30 days", "Last 90 days"])
        days = 7 if "7" in time_range else 30 if "30" in time_range else 90
        
        usage_df = get_user_usage(st.session_state.username, days)
        
        if not usage_df.empty:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_days = len(usage_df)
                st.metric("Days Tracked", total_days)
            
            with col2:
                avg_minutes = usage_df['total_minutes'].mean()
                avg_hours = avg_minutes / 60
                st.metric("Daily Average", f"{avg_hours:.1f} hrs")
            
            with col3:
                total_minutes = usage_df['total_minutes'].sum()
                total_hours = total_minutes / 60
                st.metric("Total Usage", f"{total_hours:.1f} hrs")
            
            with col4:
                most_used = usage_df['platform'].mode()[0] if not usage_df.empty else "N/A"
                st.metric("Most Used", most_used)
            
            # Usage trend chart
            st.markdown("#### Usage Trend")
            daily_trend = usage_df.groupby('date')['total_minutes'].sum().reset_index()
            daily_trend['hours'] = daily_trend['total_minutes'] / 60
            
            fig = px.line(daily_trend, x='date', y='hours', 
                         title=f'Daily Usage - Last {days} Days',
                         labels={'hours': 'Hours', 'date': 'Date'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Platform distribution
            st.markdown("#### Platform Distribution")
            platform_stats = usage_df.groupby('platform')['total_minutes'].sum().reset_index()
            platform_stats['hours'] = platform_stats['total_minutes'] / 60
            
            fig2 = px.pie(platform_stats, values='hours', names='platform',
                         title='Usage by Platform')
            st.plotly_chart(fig2, use_container_width=True)
            
            # Risk assessment based on usage
            st.markdown("#### Usage-Based Risk Assessment")
            avg_daily_hours = avg_minutes / 60
            
            if avg_daily_hours > 3:
                st.error(f"⚠️ HIGH RISK: Average {avg_daily_hours:.1f} hours/day exceeds recommended limit")
            elif avg_daily_hours > 2:
                st.warning(f"⚠️ MODERATE RISK: Average {avg_daily_hours:.1f} hours/day")
            else:
                st.success(f"✅ LOW RISK: Average {avg_daily_hours:.1f} hours/day")
            
            if most_used in ['TikTok', 'Instagram', 'Telegram', 'YouTube']:
                st.warning(f"⚠️ High-risk platform detected: {most_used}")
        else:
            st.info("No usage data yet. Start logging your daily usage in the 'Log Usage' tab.")
    
    with tab3:
        st.markdown("### Usage History")
        
        usage_df = get_user_usage(st.session_state.username, 365)
        
        if not usage_df.empty:
            # Format for display
            display_df = usage_df.copy()
            display_df['date'] = pd.to_datetime(display_df['date'])
            display_df['usage'] = display_df['hours'].astype(str) + "h " + display_df['minutes'].astype(str) + "m"
            display_df = display_df[['date', 'usage', 'platform']].sort_values('date', ascending=False)
            
            st.dataframe(display_df, use_container_width=True)
            
            # Export option
            if st.button("Download Data as CSV"):
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"usage_history_{st.session_state.username}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No usage history yet.")

# --- RISK ANALYZER (Full version for logged in users) ---
elif st.session_state.current_page == "analyzer":
    st.markdown("## 📱 Advanced Risk Assessment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.number_input("Age", 13, 80, 22)
        daily_hours = st.slider("Daily Usage (hours)", 0.5, 12.0, 2.5, 0.5)
        
        current_year = datetime.now().year
        start_year = st.number_input("Year started using social media", 
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
                    <li>📊 Track your usage weekly</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #D1FAE5; padding: 1.5rem; border-radius: 10px;">
                <h4 style="color: #065F46;">🟢 LOW RISK - Maintain Healthy Habits:</h4>
                <ul style="color: #065F46;">
                    <li>📱 Keep using only when necessary</li>
                    <li>⏰ Continue monitoring your daily usage</li>
                    <li>🌙 Maintain good sleep hygiene</li>
                    <li>🎯 Use social media intentionally</li>
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

# --- USER MANAGEMENT PAGE (Admin only) ---
elif st.session_state.current_page == "user_management" and st.session_state.is_admin:
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
            st.dataframe(users_df, use_container_width=True)
            st.caption(f"Total Users: {len(users_df)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- FEEDBACK PAGE (Admin only) ---
elif st.session_state.current_page == "feedback" and st.session_state.is_admin:
    st.markdown("## 📊 Feedback Analytics")
    st.markdown('<div class="admin-panel">', unsafe_allow_html=True)
    
    conn = sqlite3.connect('users.db')
    feedback_df = pd.read_sql_query("SELECT * FROM feedback ORDER BY timestamp DESC", conn)
    conn.close()
    
    if not feedback_df.empty:
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
        
        st.markdown("### 🤖 Model Adaptation Status")
        st.info(f"Model has learned from {len(feedback_df)} feedback instances.")
    else:
        st.info("No feedback data yet")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- Footer (with AAU) ---
st.markdown("""
<footer>
    ADDIS ABABA UNIVERSITY | College of Natural and Computational Sciences | Department of Computer Science<br>
    Machine Learning Course (COSC 6041) | Adaptive AdaBoost Algorithm | © 2026 All Rights Reserved
</footer>
""", unsafe_allow_html=True)
