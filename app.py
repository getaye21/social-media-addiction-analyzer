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
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Custom CSS for Mobile Responsive ---
st.markdown("""
<style>
    /* Mobile responsive adjustments */
    @media (max-width: 768px) {
        .main-header {
            padding: 1rem !important;
        }
        .header-title {
            font-size: 1.8rem !important;
            flex-wrap: wrap;
        }
        .university-name {
            font-size: 1.2rem !important;
        }
        .college-name {
            font-size: 0.9rem !important;
        }
        .public-test-card {
            padding: 1rem !important;
        }
        .feature-badge {
            display: block;
            margin: 0.3rem !important;
        }
        .row-widget.stButton {
            margin-bottom: 0.5rem;
        }
        div[data-testid="column"] {
            margin-bottom: 1rem;
        }
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
    
    .header-title {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
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
    
    /* Public test section */
    .public-section {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .public-card {
        flex: 1;
        min-width: 280px;
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    .feature-badge {
        background: #2563EB;
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        display: inline-block;
        margin: 0.2rem;
    }
    
    /* Comments section */
    .comment-box {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin: 1rem 0;
    }
    
    .comment-meta {
        font-size: 0.8rem;
        color: #64748b;
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
    
    /* Module cards */
    .module-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #E5E7EB;
        transition: transform 0.3s;
        height: 100%;
        margin-bottom: 1rem;
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
    # Comments table (for public users)
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
                  ip_address TEXT,
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

# --- Activity Logging Function ---
def log_activity(activity_type, username, description):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO activities 
                 (activity_type, username, description, ip_address, timestamp)
                 VALUES (?, ?, ?, ?, ?)''',
              (activity_type, username, description, "web", datetime.now()))
    conn.commit()
    conn.close()

# --- Comment Functions ---
def save_comment(name, email, comment):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO comments (name, email, comment, status, timestamp)
                 VALUES (?, ?, ?, ?, ?)''',
              (name, email, comment, 'pending', datetime.now()))
    conn.commit()
    conn.close()
    return True

def get_pending_comments():
    conn = sqlite3.connect('users.db')
    df = pd.read_sql_query("SELECT * FROM comments WHERE status='pending' ORDER BY timestamp DESC", conn)
    conn.close()
    return df

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

# --- Recent Activity Functions ---
def get_recent_activities(limit=50):
    conn = sqlite3.connect('users.db')
    df = pd.read_sql_query(f"SELECT * FROM activities ORDER BY timestamp DESC LIMIT {limit}", conn)
    conn.close()
    return df

def get_recent_logins(limit=20):
    conn = sqlite3.connect('users.db')
    df = pd.read_sql_query(f"SELECT username, last_login FROM users WHERE last_login IS NOT NULL ORDER BY last_login DESC LIMIT {limit}", conn)
    conn.close()
    return df

def update_last_login(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET last_login=? WHERE username=?", (datetime.now(), username))
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
        log_activity("login", username, f"User logged in")
    conn.close()
    return user

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
    log_activity("usage_log", username, f"Logged {hours}h {minutes}m usage")
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

# --- Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.is_admin = False
    st.session_state.feedback_given = {}
    st.session_state.current_page = "public_test"

# --- Header (with 🎓 for public page only) ---
if not st.session_state.logged_in:
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
        <div style="margin-top:1rem;">Machine Learning Course (COSC 6041) | Adaptive AdaBoost Algorithm</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="main-header">
        <div class="university-name">ADDIS ABABA UNIVERSITY</div>
        <div class="college-name">College of Natural and Computational Sciences</div>
        <div class="college-name">Department of Computer Science</div>
        <div style="margin-top:0.5rem;">Machine Learning Course (COSC 6041) | Adaptive AdaBoost Algorithm</div>
    </div>
    """, unsafe_allow_html=True)

# --- PUBLIC SECTION (Test, Login, Comments side by side) ---
if not st.session_state.logged_in:
    st.markdown('<div class="public-section">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="public-card">', unsafe_allow_html=True)
        st.markdown("### 📝 About the App")
        st.markdown("""
        This application uses **Adaptive AdaBoost Machine Learning** to analyze social media addiction risk.
        
        **Features:**
        - ✅ Basic risk assessment
        - ✅ Instant results
        - ❌ Advanced analytics (login required)
        - ❌ Usage tracking (login required)
        - ❌ Personalized recommendations (login required)
        
        **Contact admin for advanced features:**
        - 👤 getaye (admin)
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="public-card">', unsafe_allow_html=True)
        st.markdown("### 🔍 Quick Risk Test")
        with st.form("public_test_form"):
            age = st.number_input("Age", 13, 80, 22)
            daily_hours = st.slider("Daily Usage (hours)", 0.5, 12.0, 2.5, 0.5)
            current_year = datetime.now().year
            start_year = st.number_input("Year started", min_value=2000, max_value=current_year, value=2018)
            primary_platform = st.selectbox("Platform", ["TikTok", "Instagram", "Telegram", "YouTube", "Facebook", "Other"])
            test_submitted = st.form_submit_button("Test My Risk", use_container_width=True)
            
            if test_submitted:
                usage_years = current_year - start_year
                # Simple risk calculation
                if daily_hours > 3 or usage_years > 5 or primary_platform in ['TikTok', 'Instagram', 'Telegram']:
                    risk = "HIGH"
                    risk_class = "risk-high"
                elif daily_hours > 2 or usage_years > 2:
                    risk = "MODERATE"
                    risk_class = "risk-moderate"
                else:
                    risk = "LOW"
                    risk_class = "risk-low"
                
                st.markdown(f'<div class="{risk_class}"><h3>{risk} RISK</h3><p>Based on your inputs</p></div>', unsafe_allow_html=True)
                st.info("📝 Login for detailed analysis and recommendations")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="public-card">', unsafe_allow_html=True)
        st.markdown("### 🔐 Existing Users")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Login", use_container_width=True)
            
            if login_submitted:
                user = check_login(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.is_admin = user[3] == 1
                    st.session_state.current_page = "dashboard"
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="public-card">', unsafe_allow_html=True)
        st.markdown("### 💬 Questions or Comments")
        with st.form("comment_form"):
            name = st.text_input("Your Name")
            email = st.text_input("Email (optional)")
            comment = st.text_area("Your Question/Comment")
            comment_submitted = st.form_submit_button("Submit", use_container_width=True)
            
            if comment_submitted and name and comment:
                save_comment(name, email, comment)
                st.success("✅ Thank you! Admin will respond soon.")
                st.balloons()
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- SIDEBAR (Logged in users) ---
with st.sidebar:
    st.markdown(f"### 👋 Welcome, **{st.session_state.username}**!")
    
    st.markdown("### 📍 Navigation")
    if st.button("🏠 Dashboard", use_container_width=True):
        st.session_state.current_page = "dashboard"
        st.rerun()
    if st.button("📊 Risk Analyzer", use_container_width=True):
        st.session_state.current_page = "analyzer"
        st.rerun()
    if st.button("📈 Usage Analytics", use_container_width=True):
        st.session_state.current_page = "analytics"
        st.rerun()
    
    if st.session_state.is_admin:
        st.markdown("---")
        st.markdown("### 👑 Admin Panel")
        if st.button("👥 User Management", use_container_width=True):
            st.session_state.current_page = "user_management"
            st.rerun()
        if st.button("📊 Feedback & Comments", use_container_width=True):
            st.session_state.current_page = "admin_feedback"
            st.rerun()
        if st.button("📋 Recent Activity", use_container_width=True):
            st.session_state.current_page = "recent_activity"
            st.rerun()
    
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        log_activity("logout", st.session_state.username, "User logged out")
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.is_admin = False
        st.session_state.current_page = "public_test"
        st.rerun()

# --- DASHBOARD (Directly after login) ---
if st.session_state.current_page == "dashboard":
    st.markdown("## 📋 Dashboard")
    
    # Welcome message
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1E3A8A20, #2563EB20); padding: 1rem; border-radius: 10px; margin-bottom: 2rem;">
        <h4>Welcome back, {st.session_state.username}!</h4>
        <p>Use the modules below to analyze and track your social media usage.</p>
    </div>
    """, unsafe_allow_html=True)
    
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
        # Get quick stats
        conn = sqlite3.connect('users.db')
        usage_count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM usage_tracking WHERE username='{st.session_state.username}'", conn).iloc[0]['count']
        feedback_count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM feedback WHERE username='{st.session_state.username}'", conn).iloc[0]['count']
        conn.close()
        
        st.markdown(f"""
        <div class="module-card">
            <div class="module-icon">📊</div>
            <div class="module-title">Your Stats</div>
            <div class="module-description">
                <p>📊 Usage entries: {usage_count}</p>
                <p>📝 Feedback given: {feedback_count}</p>
                <p>📅 Member since: {datetime.now().strftime('%B %Y')}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

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
            display_df = usage_df.copy()
            display_df['date'] = pd.to_datetime(display_df['date'])
            display_df['usage'] = display_df['hours'].astype(str) + "h " + display_df['minutes'].astype(str) + "m"
            display_df = display_df[['date', 'usage', 'platform']].sort_values('date', ascending=False)
            
            st.dataframe(display_df, use_container_width=True)
            
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

# --- RISK ANALYZER ---
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
        
        primary_platform = st.selectbox(
            "Primary Platform",
            ["TikTok", "Instagram", "Telegram", "YouTube", "Facebook", 
             "LinkedIn", "Snapchat", "WhatsApp", "Twitter", "Google", "Other"]
        )
    
    with col2:
        sleep_hours = st.slider("Sleep (hours/night)", 3.0, 12.0, 7.0, 0.5)
        mental_health = st.slider("Mental Health Score", 1, 10, 7, 1)
    
    if st.button("🔍 Analyze My Risk", type="primary", use_container_width=True):
        
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
        
        conn = sqlite3.connect('users.db')
        feedback_df = pd.read_sql_query("SELECT * FROM feedback", conn)
        conn.close()
        
        base_confidence = 0.85
        if len(feedback_df) > 10:
            positive_rate = len(feedback_df[feedback_df['feedback'] == 'like']) / len(feedback_df)
            base_confidence = 0.7 + (positive_rate * 0.25)
        
        st.markdown("---")
        st.markdown("## 📊 Analysis Result")
        
        if overall_risk == 'High':
            st.markdown(f"""
            <div class="risk-high">
                <h2>⚠️ HIGH ADDICTION RISK</h2>
                <p>Confidence: {base_confidence:.1%}</p>
            </div>
            """, unsafe_allow_html=True)
        elif overall_risk == 'Medium':
            st.markdown(f"""
            <div class="risk-moderate">
                <h2>⚠️ MODERATE ADDICTION RISK</h2>
                <p>Confidence: {base_confidence:.1%}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="risk-low">
                <h2>✅ LOW ADDICTION RISK</h2>
                <p>Confidence: {base_confidence:.1%}</p>
            </div>
            """, unsafe_allow_html=True)
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if st.button("👍 Yes, Accurate", key="like", use_container_width=True):
                feedback_data = {
                    'username': st.session_state.username,
                    'age': age, 'daily_hours': daily_hours, 'platform': primary_platform,
                    'usage_years': usage_years, 'sleep_hours': sleep_hours,
                    'mental_health': mental_health, 'predicted_risk': overall_risk,
                    'feedback': 'like'
                }
                save_feedback(feedback_data)
                st.success("✅ Thank you!")
        
        with col_f2:
            if st.button("👎 No, Inaccurate", key="unlike", use_container_width=True):
                feedback_data = {
                    'username': st.session_state.username,
                    'age': age, 'daily_hours': daily_hours, 'platform': primary_platform,
                    'usage_years': usage_years, 'sleep_hours': sleep_hours,
                    'mental_health': mental_health, 'predicted_risk': overall_risk,
                    'feedback': 'unlike'
                }
                save_feedback(feedback_data)
                st.info("📝 Thank you!")

# --- RECENT ACTIVITY PAGE (Admin only) ---
elif st.session_state.current_page == "recent_activity" and st.session_state.is_admin:
    st.markdown("## 📋 Recent Activity Log")
    st.markdown('<div class="admin-panel">', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 All Activities", "👥 User Logins", "💬 Comments", "📝 Feedback"])
    
    with tab1:
        activities = get_recent_activities(100)
        if not activities.empty:
            for _, row in activities.iterrows():
                st.markdown(f"""
                <div class="activity-card">
                    <strong>{row['activity_type']}</strong> - {row['username']}<br>
                    {row['description']}<br>
                    <span class="activity-time">{row['timestamp']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No activities yet")
    
    with tab2:
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
    
    with tab3:
        comments = get_all_comments()
        if not comments.empty:
            for _, row in comments.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="comment-box">
                        <strong>{row['name']}</strong> ({row['email'] or 'no email'})<br>
                        <em>"{row['comment']}"</em><br>
                        <span class="comment-meta">Status: {row['status']} | {row['timestamp']}</span>
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
                        <div style="background: #EFF6FF; padding: 0.5rem; border-radius: 5px; margin-top: 0.5rem;">
                            <strong>Admin Reply:</strong> {row['reply']}<br>
                            <span class="comment-meta">{row['replied_at']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("---")
        else:
            st.info("No comments yet")
    
    with tab4:
        conn = sqlite3.connect('users.db')
        feedback_df = pd.read_sql_query("SELECT * FROM feedback ORDER BY timestamp DESC", conn)
        conn.close()
        
        if not feedback_df.empty:
            st.dataframe(feedback_df, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Feedback", len(feedback_df))
            with col2:
                likes = len(feedback_df[feedback_df['feedback'] == 'like'])
                st.metric("👍 Likes", likes)
            with col3:
                unlikes = len(feedback_df[feedback_df['feedback'] == 'unlike'])
                st.metric("👎 Unlikes", unlikes)
        else:
            st.info("No feedback yet")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- USER MANAGEMENT PAGE (Admin only) ---
elif st.session_state.current_page == "user_management" and st.session_state.is_admin:
    st.markdown("## 👥 User Management")
    st.markdown('<div class="admin-panel">', unsafe_allow_html=True)
    
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
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- ADMIN FEEDBACK PAGE ---
elif st.session_state.current_page == "admin_feedback" and st.session_state.is_admin:
    st.markdown("## 📊 Feedback & Comments")
    st.markdown('<div class="admin-panel">', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📝 Pending Comments", "📊 Model Feedback"])
    
    with tab1:
        pending = get_pending_comments()
        if not pending.empty:
            for _, row in pending.iterrows():
                with st.form(key=f"admin_reply_{row['id']}"):
                    st.markdown(f"""
                    **From:** {row['name']} ({row['email'] or 'no email'})  
                    **Date:** {row['timestamp']}  
                    **Comment:** "{row['comment']}"
                    """)
                    reply = st.text_area("Your Reply", key=f"reply_{row['id']}")
                    if st.form_submit_button("Send Reply"):
                        update_comment_reply(row['id'], reply)
                        st.success("Reply sent!")
                        st.rerun()
                    st.markdown("---")
        else:
            st.info("No pending comments")
    
    with tab2:
        conn = sqlite3.connect('users.db')
        feedback_df = pd.read_sql_query("SELECT * FROM feedback ORDER BY timestamp DESC", conn)
        conn.close()
        
        if not feedback_df.empty:
            st.dataframe(feedback_df, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Feedback", len(feedback_df))
            with col2:
                likes = len(feedback_df[feedback_df['feedback'] == 'like'])
                st.metric("👍 Likes", likes)
            with col3:
                unlikes = len(feedback_df[feedback_df['feedback'] == 'unlike'])
                st.metric("👎 Unlikes", unlikes)
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
