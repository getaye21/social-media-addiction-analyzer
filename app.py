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
import os
import shutil
import joblib
from sklearn.ensemble import AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# ----------------------------------------------------------------------
# SQLite datetime adapter (Python 3.12+)
# ----------------------------------------------------------------------
def adapt_datetime(dt):
    return dt.isoformat()

def convert_datetime(s):
    try:
        if isinstance(s, bytes):
            s = s.decode('utf-8')
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None

sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("timestamp", convert_datetime)

# ----------------------------------------------------------------------
# Persistent storage on Hugging Face
# ----------------------------------------------------------------------
def get_db_path():
    if os.path.exists('/data'):
        db_path = '/data/users.db'
        backup_path = '/data/users.db.backup'
    else:
        db_path = 'users.db'
        backup_path = 'users.db.backup'
    if not os.path.exists(db_path) and os.path.exists('users.db'):
        shutil.copy2('users.db', db_path)
        print(f"✅ Copied local database to {db_path}")
    return db_path, backup_path

def get_model_path():
    if os.path.exists('/data'):
        return '/data/adaboost_model.pkl'
    return 'adaboost_model.pkl'

def get_db_connection():
    db_path, _ = get_db_path()
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    return conn

def backup_database():
    db_path, backup_path = get_db_path()
    if os.path.exists(db_path):
        try:
            shutil.copy2(db_path, backup_path)
            print(f"✅ Database backed up to {backup_path}")
        except Exception as e:
            print(f"⚠️ Backup failed: {e}")

def restore_from_backup():
    db_path, backup_path = get_db_path()
    if not os.path.exists(db_path) and os.path.exists(backup_path):
        try:
            shutil.copy2(backup_path, db_path)
            print(f"✅ Restored database from backup")
            return True
        except Exception as e:
            print(f"⚠️ Restore failed: {e}")
    return False

# ----------------------------------------------------------------------
# Synthetic dataset generation (used for initial training & retraining)
# ----------------------------------------------------------------------
def generate_synthetic_data(n_samples=5000, random_seed=42):
    np.random.seed(random_seed)
    data = {
        'age': np.random.randint(13, 50, n_samples),
        'daily_hours': np.random.uniform(0.5, 15.0, n_samples),
        'work_related': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
        'sleep_hours': np.random.uniform(3.0, 10.0, n_samples),
        'mental_health': np.random.randint(1, 11, n_samples),
        'usage_years': np.random.uniform(0.5, 15.0, n_samples),
    }
    df = pd.DataFrame(data)

    # Risk score based on expert rules
    risk_score = (
        df['daily_hours'] * 0.4 +
        (10 - df['sleep_hours']) * 0.2 +
        (10 - df['mental_health']) * 0.3 +
        df['usage_years'] * 0.1
    )
    platforms = ['TikTok', 'Instagram', 'YouTube', 'Facebook', 'WhatsApp']
    df['platform'] = np.random.choice(platforms, n_samples)
    platform_risk = {'TikTok': 1.2, 'Instagram': 1.1, 'YouTube': 1.1,
                     'Facebook': 1.0, 'WhatsApp': 0.9}
    df['platform_risk_factor'] = df['platform'].map(platform_risk)
    risk_score = risk_score * df['platform_risk_factor']
    risk_score = (risk_score - risk_score.min()) / (risk_score.max() - risk_score.min()) * 10
    df['target'] = pd.cut(risk_score, bins=[0, 4, 7, 10], labels=[0, 1, 2])

    platform_dummies = pd.get_dummies(df['platform'], prefix='platform')
    X = pd.concat([df[['age', 'daily_hours', 'work_related', 'sleep_hours',
                       'mental_health', 'usage_years']],
                   platform_dummies], axis=1)
    y = df['target']
    return X, y

def train_and_save_model(X, y, synthetic_flag=True):
    base_learner = DecisionTreeClassifier(max_depth=2, random_state=42)
    model = AdaBoostClassifier(estimator=base_learner, n_estimators=200,
                               learning_rate=0.8, random_state=42)
    model.fit(X, y)

    y_pred = model.predict(X)
    acc = accuracy_score(y, y_pred)
    prec = precision_score(y, y_pred, average='weighted', zero_division=0)
    rec = recall_score(y, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y, y_pred, average='weighted', zero_division=0)

    model_data = {
        'model': model,
        'features': X.columns.tolist(),
        'metrics': {
            'accuracy': acc,
            'precision': prec,
            'recall': rec,
            'f1_score': f1,
            'training_samples': len(X),
            'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'synthetic': synthetic_flag
        }
    }
    joblib.dump(model_data, get_model_path())

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO model_metrics 
                 (accuracy, precision, recall, f1_score, training_samples, timestamp)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (acc, prec, rec, f1, len(X), datetime.now()))
    conn.commit()
    conn.close()
    return model_data

def generate_initial_model():
    st.info("Initializing AdaBoost model with synthetic data...")
    X_syn, y_syn = generate_synthetic_data(n_samples=5000, random_seed=42)
    return train_and_save_model(X_syn, y_syn, synthetic_flag=True)

def train_model_from_feedback():
    """Retrain using synthetic + all real 'like' feedback (called after each like)."""
    X_syn, y_syn = generate_synthetic_data(n_samples=5000, random_seed=42)

    conn = get_db_connection()
    feedback_df = pd.read_sql_query("""
        SELECT age, daily_hours, work_related, platform,
               usage_years, sleep_hours, mental_health,
               predicted_risk as actual_risk
        FROM feedback WHERE feedback = 'like'
    """, conn)
    conn.close()

    if len(feedback_df) == 0:
        return None

    real_dummies = pd.get_dummies(feedback_df['platform'], prefix='platform')
    real_features = feedback_df[['age', 'daily_hours', 'work_related', 'sleep_hours',
                                 'mental_health', 'usage_years']]
    X_real = pd.concat([real_features, real_dummies], axis=1)
    y_real = feedback_df['actual_risk'].map({'Low': 0, 'Medium': 1, 'High': 2})

    # Align columns
    all_columns = set(X_syn.columns).union(set(X_real.columns))
    for col in all_columns:
        if col not in X_syn.columns:
            X_syn[col] = 0
        if col not in X_real.columns:
            X_real[col] = 0
    ordered = sorted(all_columns)
    X_syn = X_syn[ordered]
    X_real = X_real[ordered]

    X_combined = pd.concat([X_syn, X_real], ignore_index=True)
    y_combined = pd.concat([y_syn, y_real], ignore_index=True)

    print(f"Retraining AdaBoost on synthetic ({len(X_syn)}) + {len(X_real)} real feedback")
    return train_and_save_model(X_combined, y_combined, synthetic_flag=False)

# ----------------------------------------------------------------------
# Model loading & prediction
# ----------------------------------------------------------------------
def load_model():
    path = get_model_path()
    if os.path.exists(path):
        try:
            return joblib.load(path)
        except Exception as e:
            print(f"Load error: {e}")
            return None
    return None

def predict_with_model(age, daily_hours, work_related, start_year,
                       primary_platform, sleep_hours, mental_health):
    model_data = load_model()
    if model_data is None:
        return None
    model = model_data['model']
    feature_list = model_data['features']
    current_year = datetime.now().year
    usage_years = current_year - start_year

    feat_dict = {
        'age': age,
        'daily_hours': daily_hours,
        'work_related': work_related,
        'sleep_hours': sleep_hours,
        'mental_health': mental_health,
        'usage_years': usage_years
    }
    for col in feature_list:
        if col.startswith('platform_'):
            platform_name = col.replace('platform_', '')
            feat_dict[col] = 1 if primary_platform == platform_name else 0

    X_pred = pd.DataFrame([feat_dict])[feature_list]
    pred = model.predict(X_pred)[0]
    probs = model.predict_proba(X_pred)[0]
    risk_map = {0: 'Low', 1: 'Medium', 2: 'High'}
    return {
        'overall_risk': risk_map[pred],
        'confidence': max(probs),
        'usage_years': usage_years,
        'daily_hours': daily_hours,
        'work_related': work_related,
        'platform': primary_platform,
        'sleep_hours': sleep_hours,
        'mental_health': mental_health
    }

def analyze_risk_rule_based(age, daily_hours, work_related, start_year,
                            primary_platform, sleep_hours, mental_health):
    # Kept as safety net – should rarely be used after model is ready
    current_year = datetime.now().year
    usage_years = current_year - start_year
    platform_risk_map = {
        'Telegram': 'High', 'YouTube': 'High', 'TikTok': 'High',
        'Instagram': 'High', 'Google': 'High', 'Facebook': 'Medium',
        'LinkedIn': 'Medium', 'Snapchat': 'Medium', 'WhatsApp': 'Low',
        'Twitter': 'Low', 'Other': 'Low'
    }
    platform_risk = platform_risk_map.get(primary_platform, 'Medium')
    if usage_years > 5: experience_risk = 'High'
    elif usage_years > 2: experience_risk = 'Medium'
    else: experience_risk = 'Low'
    if work_related == 1:
        if daily_hours > 5: usage_risk = 'High'
        elif daily_hours > 3: usage_risk = 'Medium'
        else: usage_risk = 'Low'
    else:
        if daily_hours > 3: usage_risk = 'High'
        elif daily_hours > 2: usage_risk = 'Medium'
        else: usage_risk = 'Low'
    if sleep_hours < 6: sleep_risk = 'High'
    elif sleep_hours < 7: sleep_risk = 'Medium'
    else: sleep_risk = 'Low'
    if mental_health < 4: mental_risk = 'High'
    elif mental_health < 7: mental_risk = 'Medium'
    else: mental_risk = 'Low'
    risk_scores = {'High':3, 'Medium':2, 'Low':1}
    work_factor = 0.9 if work_related == 1 else 1.0
    total = (risk_scores[usage_risk]*2 + risk_scores[platform_risk]*1.5 +
             risk_scores[experience_risk] + risk_scores[sleep_risk] + risk_scores[mental_risk]) * work_factor
    avg = total / 6.5
    if avg > 2.3: overall_risk = 'High'
    elif avg > 1.5: overall_risk = 'Medium'
    else: overall_risk = 'Low'
    return {
        'overall_risk': overall_risk,
        'usage_risk': usage_risk,
        'platform_risk': platform_risk,
        'experience_risk': experience_risk,
        'sleep_risk': sleep_risk,
        'mental_risk': mental_risk,
        'usage_years': usage_years,
        'daily_hours': daily_hours,
        'work_related': work_related,
        'platform': primary_platform,
        'sleep_hours': sleep_hours,
        'mental_health': mental_health
    }

def analyze_risk(age, daily_hours, work_related, start_year,
                primary_platform, sleep_hours, mental_health):
    # Prefer model; fallback to rule-based only if model missing
    res = predict_with_model(age, daily_hours, work_related, start_year,
                            primary_platform, sleep_hours, mental_health)
    if res:
        # Add extra fields needed by the UI
        platform_risk_map = {
            'Telegram': 'High', 'YouTube': 'High', 'TikTok': 'High',
            'Instagram': 'High', 'Google': 'High', 'Facebook': 'Medium',
            'LinkedIn': 'Medium', 'Snapchat': 'Medium', 'WhatsApp': 'Low',
            'Twitter': 'Low', 'Other': 'Low'
        }
        res['platform_risk'] = platform_risk_map.get(primary_platform, 'Medium')
        if work_related == 1:
            res['usage_risk'] = 'High' if daily_hours > 5 else 'Medium' if daily_hours > 3 else 'Low'
        else:
            res['usage_risk'] = 'High' if daily_hours > 3 else 'Medium' if daily_hours > 2 else 'Low'
        res['sleep_risk'] = 'High' if sleep_hours < 6 else 'Medium' if sleep_hours < 7 else 'Low'
        res['mental_risk'] = 'High' if mental_health < 4 else 'Medium' if mental_health < 7 else 'Low'
        y = res['usage_years']
        res['experience_risk'] = 'High' if y > 5 else 'Medium' if y > 2 else 'Low'
        return res
    else:
        return analyze_risk_rule_based(age, daily_hours, work_related, start_year,
                                       primary_platform, sleep_hours, mental_health)

# ----------------------------------------------------------------------
# AUTHENTICATION & DATABASE FUNCTIONS
# ----------------------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    conn = get_db_connection()
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
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET last_login=? WHERE username=?", (datetime.now(), username))
    conn.commit()
    conn.close()
    backup_database()

def create_user(username, password, is_admin=False):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        hashed_pw = hash_password(password)
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", 
                 (username, hashed_pw, datetime.now(), 1 if is_admin else 0, None))
        conn.commit()
        log_activity("user_created", username, f"New user created by admin")
        backup_database()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def log_activity(activity_type, username, description, details=None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO activities 
                 (activity_type, username, description, details, ip_address, timestamp)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (activity_type, username, description, details, "web", datetime.now()))
    conn.commit()
    conn.close()
    backup_database()

def log_risk_analysis(username, age, daily_hours, work_related, start_year, platform, sleep_hours, mental_health, risk_result):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO risk_analyses 
                 (username, age, daily_hours, work_related, start_year, platform, sleep_hours, mental_health, risk_result, timestamp)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (username, age, daily_hours, work_related, start_year, platform, sleep_hours, mental_health, risk_result, datetime.now()))
    conn.commit()
    conn.close()
    log_activity("risk_analysis", username, f"Performed risk analysis: {risk_result}", f"Age:{age}, Hours:{daily_hours}, Work:{work_related}, Platform:{platform}")

def get_all_activities(limit=100):
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT * FROM activities ORDER BY timestamp DESC LIMIT {limit}", conn)
    conn.close()
    return df

def get_risk_analyses(limit=100):
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT * FROM risk_analyses ORDER BY timestamp DESC LIMIT {limit}", conn)
    conn.close()
    return df

def get_recent_logins(limit=20):
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT username, last_login FROM users WHERE last_login IS NOT NULL ORDER BY last_login DESC LIMIT {limit}", conn)
    conn.close()
    return df

def save_comment(name, email, comment):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO comments (name, email, comment, status, timestamp)
                 VALUES (?, ?, ?, ?, ?)''',
              (name, email, comment, 'pending', datetime.now()))
    conn.commit()
    conn.close()
    log_activity("comment", name, f"Submitted comment", comment[:50])
    backup_database()

def get_all_comments():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM comments ORDER BY timestamp DESC", conn)
    conn.close()
    return df

def update_comment_reply(comment_id, reply):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''UPDATE comments 
                 SET status='replied', reply=?, replied_at=?
                 WHERE id=?''',
              (reply, datetime.now(), comment_id))
    conn.commit()
    conn.close()
    backup_database()

def save_user_feedback(username, feedback_type, feedback_text):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO user_feedback (username, feedback_type, feedback_text, timestamp)
                 VALUES (?, ?, ?, ?)''',
              (username, feedback_type, feedback_text, datetime.now()))
    conn.commit()
    conn.close()
    log_activity("user_feedback", username, f"Submitted {feedback_type} feedback", feedback_text[:50])

def get_all_user_feedback():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM user_feedback ORDER BY timestamp DESC", conn)
    conn.close()
    return df

def save_model_feedback(data):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO feedback 
                 (username, age, daily_hours, work_related, platform, usage_years, sleep_hours, mental_health, predicted_risk, feedback, timestamp)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data['username'], data['age'], data['daily_hours'], data['work_related'], data['platform'],
               data['usage_years'], data['sleep_hours'], data['mental_health'],
               data['predicted_risk'], data['feedback'], datetime.now()))
    conn.commit()
    conn.close()
    log_activity("model_feedback", data['username'], f"Gave {data['feedback']} feedback on prediction")
    backup_database()

    # ==============================================================
    # RETRAIN AFTER EVERY "LIKE" FEEDBACK (immediate adaptation)
    # ==============================================================
    if data['feedback'] == 'like':
        with st.spinner("📈 Adapting model with your feedback... (one moment)"):
            result = train_model_from_feedback()
            if result:
                st.success(f"✅ Model updated! New accuracy: {result['metrics']['accuracy']:.2%}")
                # Show a small notification (optional)
                st.toast("Model improved with your feedback!", icon="🎯")
            else:
                st.info("ℹ️ Model will update after more feedback.")

def save_usage_entry(username, log_date, app_name, hours, minutes, work_related):
    conn = get_db_connection()
    c = conn.cursor()
    total_minutes = (hours * 60) + minutes
    c.execute('''INSERT INTO usage_tracking 
                 (username, date, app_name, hours, minutes, total_minutes, work_related, timestamp)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (username, log_date, app_name, hours, minutes, total_minutes, work_related, datetime.now()))
    conn.commit()
    conn.close()
    log_activity("usage_log", username, f"Logged {hours}h {minutes}m on {app_name}", f"Work:{work_related}")
    backup_database()

def get_user_usage_by_app(username, days=30):
    conn = get_db_connection()
    cutoff_date = (datetime.now() - timedelta(days=days)).date()
    df = pd.read_sql_query(f"""
        SELECT date, app_name, hours, minutes, total_minutes, work_related 
        FROM usage_tracking 
        WHERE username = '{username}' AND date >= '{cutoff_date}'
        ORDER BY date DESC
    """, conn)
    conn.close()
    return df

def get_all_users():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT username, created_at, is_admin, last_login FROM users ORDER BY created_at DESC", conn)
    conn.close()
    return df

def get_model_metrics():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM model_metrics ORDER BY timestamp DESC LIMIT 1", conn)
    conn.close()
    return df.iloc[0] if not df.empty else None

# ----------------------------------------------------------------------
# DATABASE INITIALIZATION (tables + initial model)
# ----------------------------------------------------------------------
def init_db():
    restore_from_backup()
    conn = get_db_connection()
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, created_at TIMESTAMP, is_admin INTEGER DEFAULT 0, last_login TIMESTAMP)''')
    # Feedback table (model likes/unlikes)
    c.execute('''CREATE TABLE IF NOT EXISTS feedback
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT, age INTEGER, daily_hours REAL, work_related INTEGER,
                  platform TEXT, usage_years REAL, sleep_hours REAL, mental_health INTEGER,
                  predicted_risk TEXT, feedback TEXT, timestamp TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_feedback
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, feedback_type TEXT, feedback_text TEXT, timestamp TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS usage_tracking
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, date DATE,
                  app_name TEXT, hours INTEGER, minutes INTEGER, total_minutes INTEGER,
                  work_related INTEGER, timestamp TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS comments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, comment TEXT,
                  status TEXT DEFAULT 'pending', timestamp TIMESTAMP, replied_at TIMESTAMP, reply TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS activities
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, activity_type TEXT, username TEXT,
                  description TEXT, details TEXT, ip_address TEXT, timestamp TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS risk_analyses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, age INTEGER,
                  daily_hours REAL, work_related INTEGER, start_year INTEGER, platform TEXT,
                  sleep_hours REAL, mental_health INTEGER, risk_result TEXT, timestamp TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS model_metrics
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, accuracy REAL, precision REAL,
                  recall REAL, f1_score REAL, training_samples INTEGER, timestamp TIMESTAMP)''')

    # Create admin user (password: ML@2026)
    admin_exists = c.execute("SELECT * FROM users WHERE username='getaye'").fetchone()
    if not admin_exists:
        hashed_pw = hash_password("ML@2026")
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                 ("getaye", hashed_pw, datetime.now(), 1, None))
        print("✅ Admin user 'getaye' created")

    conn.commit()
    conn.close()
    backup_database()

    # Train initial model if not already present
    if not os.path.exists(get_model_path()):
        with st.spinner("First launch: training initial AdaBoost model (please wait)..."):
            generate_initial_model()
        st.success("✅ Initial AdaBoost model is ready!")

init_db()

# ----------------------------------------------------------------------
# CUSTOM CSS (full original styling)
# ----------------------------------------------------------------------
st.markdown("""
<style>
    .stSelectbox label, .stSelectbox div[data-baseweb="select"] span {
        display: none;
    }
    .sidebar-header {
        background: linear-gradient(135deg, #1E3A8A, #2563EB);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
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
    .developer-info {
        font-size: 1.2rem;
        margin: 0.5rem 0;
        color: #FFD700;
    }
    .algorithm-info {
        font-size: 1rem;
        margin: 0.2rem 0;
        opacity: 0.95;
    }
    .menu-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    .menu-card {
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
    }
    .menu-card:hover {
        transform: translateY(-5px);
        border-color: #2563EB;
        box-shadow: 0 10px 25px rgba(37,99,235,0.2);
    }
    .menu-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    .menu-title {
        font-weight: bold;
        color: #1E3A8A;
        font-size: 1.1rem;
    }
    .feature-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        min-height: 600px;
    }
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
    .recommendations {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #2563EB;
        margin: 1rem 0;
    }
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
    .info-box {
        background: #EFF6FF;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #2563EB;
        margin: 1rem 0;
    }
    .app-entry {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin: 0.5rem 0;
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

# ----------------------------------------------------------------------
# SESSION STATE
# ----------------------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.is_admin = False
    st.session_state.page = "public"
    st.session_state.public_menu = None
    st.session_state.dashboard_menu = "main"
    st.session_state.last_risk_result = None

# ----------------------------------------------------------------------
# LOGIN PAGE HEADER
# ----------------------------------------------------------------------
if not st.session_state.logged_in:
    st.markdown("""
    <div class="main-header">
        <div class="red-title">📱 Social Media Addiction Risk Analyzer</div>
        <div class="developer-info">Developed by Getaye Fiseha</div>
        <div class="algorithm-info">using AdaBoost Algorithm Machine Learning technique</div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------------------
# PUBLIC SECTION (No login)
# ----------------------------------------------------------------------
if not st.session_state.logged_in:
    if st.session_state.public_menu is None:
        st.markdown("## 👋 Welcome to Social Media Addiction Risk Analyzer")
        st.markdown("### Select an option below:")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 About App", key="pub_about", use_container_width=True):
                st.session_state.public_menu = "about"
                st.rerun()
            if st.button("⚡ Quick Test", key="pub_test", use_container_width=True):
                st.session_state.public_menu = "quick_test"
                st.rerun()
        with col2:
            if st.button("💬 Contact Admin", key="pub_contact", use_container_width=True):
                st.session_state.public_menu = "contact"
                st.rerun()
            if st.button("🔐 Login", key="pub_login", use_container_width=True):
                st.session_state.public_menu = "login"
                st.rerun()
        with col3:
            if st.button("✨ Features", key="pub_features", use_container_width=True):
                st.session_state.public_menu = "features"
                st.rerun()
            if st.button("📞 Get Help", key="pub_help", use_container_width=True):
                st.session_state.public_menu = "help"
                st.rerun()
    else:
        if st.button("← Back to Main Menu", key="back_public"):
            st.session_state.public_menu = None
            st.rerun()
        st.markdown("---")
        if st.session_state.public_menu == "about":
            st.markdown("## 📋 About This Application")
            st.markdown("""
            This application uses **Adaptive AdaBoost Machine Learning** to analyze social media addiction risk.
            
            **How it works:**
            - 📊 Analyzes your usage patterns and habits
            - 🧠 Uses machine learning to predict risk levels
            - 💡 Provides personalized recommendations
            - 📈 Tracks your progress over time
            
            **Features available after login:**
            - ✅ Advanced risk assessment with actual ML model
            - ✅ Multi-app usage tracking (log multiple apps per day)
            - ✅ Personalized recommendations
            - ✅ Model feedback to improve accuracy
            - ✅ History tracking with metrics
            """)
        elif st.session_state.public_menu == "quick_test":
            st.markdown("## ⚡ Quick Risk Test")
            with st.form("quick_test_form"):
                col1, col2 = st.columns(2)
                with col1:
                    age = st.number_input("Age", 13, 80, 22)
                    daily_hours = st.slider("Daily Usage (hours)", 0.5, 12.0, 2.5, 0.5)
                    work_related = st.radio("Is this usage work-related?", ["Yes", "No"])
                with col2:
                    start_year = st.number_input("Year started", min_value=2000, max_value=datetime.now().year, value=2018)
                    primary_platform = st.selectbox("Platform", ["TikTok", "Instagram", "Telegram", "YouTube", "Facebook", "Other"])
                col3, col4 = st.columns(2)
                with col3:
                    sleep_hours = st.slider("Sleep (hours/night)", 3.0, 12.0, 7.0, 0.5)
                with col4:
                    mental_health = st.slider("Mental Health Score", 1, 10, 7, 1)
                if st.form_submit_button("Test My Risk", use_container_width=True):
                    work_val = 1 if work_related == "Yes" else 0
                    result = analyze_risk(age, daily_hours, work_val, start_year, primary_platform, sleep_hours, mental_health)
                    if result['overall_risk'] == 'High':
                        st.markdown(f'<div class="risk-high"><h2>⚠️ HIGH ADDICTION RISK</h2></div>', unsafe_allow_html=True)
                    elif result['overall_risk'] == 'Medium':
                        st.markdown(f'<div class="risk-moderate"><h2>⚠️ MODERATE ADDICTION RISK</h2></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="risk-low"><h2>✅ LOW ADDICTION RISK</h2></div>', unsafe_allow_html=True)
                    st.info("📝 Login for detailed analysis and recommendations")
        elif st.session_state.public_menu == "contact":
            st.markdown("## 💬 Contact Admin")
            st.markdown("Send your questions, feedback, or requests to the administrator.")
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
        elif st.session_state.public_menu == "login":
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
                        st.session_state.dashboard_menu = "main"
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
        elif st.session_state.public_menu == "features":
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
                - 📊 Advanced risk assessment with AdaBoost ML
                - 📈 Multi-app usage tracking & analytics
                - 💡 Personalized recommendations
                - 📝 Model feedback (help improve accuracy)
                - 📅 History tracking with metrics
                """)
        elif st.session_state.public_menu == "help":
            st.markdown("## 📞 Get Help")
            st.markdown("""
            **Need assistance?**  
            Please use the **Contact Admin** option to send your questions or concerns.  
            The administrator will respond to your inquiry as soon as possible.  
            **Common topics:** Account issues, Feature requests, Technical support, General questions  
            
            👉 Go to **Contact Admin** from the main menu to send a message.
            """)
            if st.button("Go to Contact Admin"):
                st.session_state.public_menu = "contact"
                st.rerun()
    st.stop()

# ----------------------------------------------------------------------
# LOGGED IN SECTION
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-header">
        <h3>Welcome, {st.session_state.username}!</h3>
        <p>{'👑 Administrator' if st.session_state.is_admin else '👤 Regular User'}</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🏠 Dashboard", key="nav_dashboard", use_container_width=True):
        st.session_state.dashboard_menu = "main"
        st.rerun()
    if st.button("👥 User Management", key="nav_users", use_container_width=True):
        st.session_state.dashboard_menu = "user_management"
        st.rerun()
    st.markdown("---")
    if st.button("🚪 Logout", key="nav_logout", use_container_width=True):
        log_activity("logout", st.session_state.username, "User logged out")
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.is_admin = False
        st.session_state.page = "public"
        backup_database()
        st.rerun()

# ----------------------------------------------------------------------
# DASHBOARD MAIN PAGE
# ----------------------------------------------------------------------
if st.session_state.dashboard_menu == "main":
    st.markdown("## 📋 Dashboard")
    st.markdown(f"Welcome back, {st.session_state.username}!")
    col1, col2, col3 = st.columns(3)
    conn = get_db_connection()
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
    model_data = load_model()
    if model_data:
        st.success(f"✅ AdaBoost Model Active - {model_data['metrics']['training_samples']} training samples, {model_data['metrics']['accuracy']:.1%} accuracy")
    else:
        st.info("ℹ️ Using rule‑based system (collecting feedback to train ML model)")
    st.markdown("### 📱 Features")
    st.markdown("Select a feature to get started:")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 Risk Analyzer", key="feat_analyzer", use_container_width=True):
            st.session_state.dashboard_menu = "analyzer"
            st.rerun()
        if st.button("📈 Usage Analytics", key="feat_analytics", use_container_width=True):
            st.session_state.dashboard_menu = "analytics"
            st.rerun()
    with col2:
        if st.button("💡 Recommendations", key="feat_recommend", use_container_width=True):
            st.session_state.dashboard_menu = "recommendations"
            st.rerun()
        if st.button("👤 My Profile", key="feat_profile", use_container_width=True):
            st.session_state.dashboard_menu = "profile"
            st.rerun()
    with col3:
        if st.button("📝 Submit Feedback", key="feat_feedback", use_container_width=True):
            st.session_state.dashboard_menu = "feedback_form"
            st.rerun()
        if st.button("📊 My Activity", key="feat_activity", use_container_width=True):
            st.session_state.dashboard_menu = "my_activity"
            st.rerun()
    if st.session_state.is_admin:
        st.markdown("### 👑 Admin Features")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💬 Comments", key="feat_comments", use_container_width=True):
                st.session_state.dashboard_menu = "comments"
                st.rerun()
        with col2:
            if st.button("📊 Model Feedback", key="feat_model_feedback", use_container_width=True):
                st.session_state.dashboard_menu = "feedback"
                st.rerun()
        with col3:
            if st.button("📋 Activity Log", key="feat_activity_log", use_container_width=True):
                st.session_state.dashboard_menu = "activity"
                st.rerun()

# ----------------------------------------------------------------------
# RISK ANALYZER
# ----------------------------------------------------------------------
elif st.session_state.dashboard_menu == "analyzer":
    st.markdown("## 📊 Risk Analyzer")
    if st.button("← Back to Dashboard", key="back_analyzer"):
        st.session_state.dashboard_menu = "main"
        st.rerun()
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", 13, 80, 22, key="analyzer_age")
        daily_hours = st.slider("Daily Usage (hours)", 0.5, 15.0, 2.5, 0.5, key="analyzer_hours")
        work_related = st.radio("Is this usage work-related?", ["Yes", "No"], key="analyzer_work")
        start_year = st.number_input("Year started using social media", min_value=2000, max_value=datetime.now().year, value=2018, key="analyzer_year")
    with col2:
        primary_platform = st.selectbox("Primary Platform", ["TikTok", "Instagram", "Telegram", "YouTube", "Facebook", "LinkedIn", "Snapchat", "WhatsApp", "Twitter", "Google", "Other"], key="analyzer_platform")
        sleep_hours = st.slider("Sleep (hours/night)", 3.0, 12.0, 7.0, 0.5, key="analyzer_sleep")
        mental_health = st.slider("Mental Health Score", 1, 10, 7, 1, key="analyzer_mental")
        other_platforms = st.multiselect("Other platforms you use", ["TikTok", "Instagram", "Telegram", "YouTube", "Facebook", "LinkedIn", "Snapchat", "WhatsApp", "Twitter", "Google"])
    if st.button("🔍 Analyze My Risk", type="primary", use_container_width=True):
        work_val = 1 if work_related == "Yes" else 0
        result = analyze_risk(age, daily_hours, work_val, start_year, primary_platform, sleep_hours, mental_health)
        st.session_state.last_risk_result = result
        log_risk_analysis(st.session_state.username, age, daily_hours, work_val, start_year, primary_platform, sleep_hours, mental_health, result['overall_risk'])
        model_data = load_model()
        confidence = result.get('confidence', 0.85)
        if result['overall_risk'] == 'High':
            st.markdown(f'<div class="risk-high"><h2>⚠️ HIGH ADDICTION RISK</h2><p>Confidence: {confidence:.1%}</p></div>', unsafe_allow_html=True)
        elif result['overall_risk'] == 'Medium':
            st.markdown(f'<div class="risk-moderate"><h2>⚠️ MODERATE ADDICTION RISK</h2><p>Confidence: {confidence:.1%}</p></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="risk-low"><h2>✅ LOW ADDICTION RISK</h2><p>Confidence: {confidence:.1%}</p></div>', unsafe_allow_html=True)
        if model_data:
            st.info(f"🤖 Prediction made by AdaBoost ML model (trained on {model_data['metrics']['training_samples']} samples, {model_data['metrics']['accuracy']:.1%} accuracy)")
        st.markdown("### 💡 Personalized Recommendations")
        if result['overall_risk'] == 'High':
            st.markdown("""
            <div class="recommendations">
                <h4>🔴 HIGH RISK - Immediate Action Required:</h4>
                <ul>
                    <li>📱 Reduce personal usage to under 3 hours per day immediately</li>
                    <li>⏰ Set strict app timers (30-minute daily limits for non-work apps)</li>
                    <li>🌙 No phones in bedroom - charge outside at night</li>
                    <li>🎯 Take a 7-day digital detox challenge</li>
                    <li>💼 Separate work and personal devices if possible</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        elif result['overall_risk'] == 'Medium':
            st.markdown("""
            <div class="recommendations">
                <h4>🟡 MODERATE RISK - Take Preventive Measures:</h4>
                <ul>
                    <li>📱 Limit personal usage to 2-3 hours per day</li>
                    <li>⏰ Use focus mode during work/study hours</li>
                    <li>🌙 No phone 1 hour before bed</li>
                    <li>📊 Track your usage weekly</li>
                    <li>💼 Schedule social media breaks between work tasks</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="recommendations">
                <h4>🟢 LOW RISK - Maintain Healthy Habits:</h4>
                <ul>
                    <li>📱 Keep personal usage only when necessary</li>
                    <li>⏰ Continue monitoring your daily usage</li>
                    <li>🌙 Maintain good sleep hygiene</li>
                    <li>🎯 Use social media intentionally, not habitually</li>
                    <li>💼 Maintain work-life balance in digital usage</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("### 🤖 Help Improve the Model")
        st.markdown("""
        <div class="info-box">
            <h4>How Model Feedback Works:</h4>
            <p>When you click "Yes, Accurate" or "No, Inaccurate", you're helping train the machine learning model:</p>
            <ul>
                <li><strong>👍 Yes, Accurate:</strong> Confirms the prediction was correct - reinforces what the model got right</li>
                <li><strong>👎 No, Inaccurate:</strong> Flags an incorrect prediction - helps the model learn from mistakes</li>
            </ul>
            <p><strong>Your feedback is used immediately to improve the model!</strong> (retrains after every "Yes")</p>
        </div>
        """, unsafe_allow_html=True)
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if st.button("👍 Yes, Accurate", key="like", use_container_width=True):
                feedback_data = {
                    'username': st.session_state.username,
                    'age': age, 'daily_hours': daily_hours, 'work_related': work_val, 'platform': primary_platform,
                    'usage_years': result['usage_years'], 'sleep_hours': sleep_hours,
                    'mental_health': mental_health, 'predicted_risk': result['overall_risk'],
                    'feedback': 'like'
                }
                save_model_feedback(feedback_data)
        with col_f2:
            if st.button("👎 No, Inaccurate", key="unlike", use_container_width=True):
                feedback_data = {
                    'username': st.session_state.username,
                    'age': age, 'daily_hours': daily_hours, 'work_related': work_val, 'platform': primary_platform,
                    'usage_years': result['usage_years'], 'sleep_hours': sleep_hours,
                    'mental_health': mental_health, 'predicted_risk': result['overall_risk'],
                    'feedback': 'unlike'
                }
                save_model_feedback(feedback_data)

# ----------------------------------------------------------------------
# RECOMMENDATIONS
# ----------------------------------------------------------------------
elif st.session_state.dashboard_menu == "recommendations":
    st.markdown("## 💡 Personalized Recommendations")
    if st.button("← Back to Dashboard", key="back_recommend"):
        st.session_state.dashboard_menu = "main"
        st.rerun()
    st.markdown("---")
    if st.session_state.last_risk_result:
        result = st.session_state.last_risk_result
        if result['overall_risk'] == 'High':
            st.markdown("""
            <div class="recommendations">
                <h4>🔴 HIGH RISK - Immediate Action Required:</h4>
                <ul>
                    <li>📱 Reduce personal usage to under 3 hours per day immediately</li>
                    <li>⏰ Set strict app timers (30-minute daily limits for non-work apps)</li>
                    <li>🌙 No phones in bedroom - charge outside at night</li>
                    <li>🎯 Take a 7-day digital detox challenge</li>
                    <li>💼 Separate work and personal devices if possible</li>
                    <li>📊 Use screen time tracking apps</li>
                    <li>👥 Join a digital wellness group</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        elif result['overall_risk'] == 'Medium':
            st.markdown("""
            <div class="recommendations">
                <h4>🟡 MODERATE RISK - Take Preventive Measures:</h4>
                <ul>
                    <li>📱 Limit personal usage to 2-3 hours per day</li>
                    <li>⏰ Use focus mode during work/study hours</li>
                    <li>🌙 No phone 1 hour before bed</li>
                    <li>📊 Track your usage weekly</li>
                    <li>💼 Schedule social media breaks between work tasks</li>
                    <li>🎯 Set specific times for checking social media</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="recommendations">
                <h4>🟢 LOW RISK - Maintain Healthy Habits:</h4>
                <ul>
                    <li>📱 Keep personal usage only when necessary</li>
                    <li>⏰ Continue monitoring your daily usage</li>
                    <li>🌙 Maintain good sleep hygiene</li>
                    <li>🎯 Use social media intentionally, not habitually</li>
                    <li>💼 Maintain work-life balance in digital usage</li>
                    <li>👥 Encourage friends to maintain balance too</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Please run a risk analysis first to get personalized recommendations.")
        if st.button("Go to Risk Analyzer"):
            st.session_state.dashboard_menu = "analyzer"
            st.rerun()

# ----------------------------------------------------------------------
# PROFILE
# ----------------------------------------------------------------------
elif st.session_state.dashboard_menu == "profile":
    st.markdown("## 👤 My Profile")
    if st.button("← Back to Dashboard", key="back_profile"):
        st.session_state.dashboard_menu = "main"
        st.rerun()
    st.markdown("---")
    conn = get_db_connection()
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

# ----------------------------------------------------------------------
# FEEDBACK FORM
# ----------------------------------------------------------------------
elif st.session_state.dashboard_menu == "feedback_form":
    st.markdown("## 📝 Submit Feedback")
    if st.button("← Back to Dashboard", key="back_feedback_form"):
        st.session_state.dashboard_menu = "main"
        st.rerun()
    st.markdown("---")
    st.markdown("""
    <div class="info-box">
        <h4>Submit Your Feedback</h4>
        <p>Have suggestions for improvement? Found a bug? Want to request a new feature? Let us know!</p>
    </div>
    """, unsafe_allow_html=True)
    with st.form("feedback_form"):
        feedback_type = st.selectbox("Feedback Type", ["Suggestion", "Bug Report", "Feature Request", "General Comment"])
        feedback_text = st.text_area("Your Feedback")
        if st.form_submit_button("Submit Feedback", use_container_width=True):
            if feedback_text:
                save_user_feedback(st.session_state.username, feedback_type, feedback_text)
                st.success("✅ Thank you for your feedback!")
                st.balloons()
            else:
                st.error("❌ Please enter feedback")

# ----------------------------------------------------------------------
# MY ACTIVITY
# ----------------------------------------------------------------------
elif st.session_state.dashboard_menu == "my_activity":
    st.markdown("## 📊 My Activity")
    if st.button("← Back to Dashboard", key="back_my_activity"):
        st.session_state.dashboard_menu = "main"
        st.rerun()
    st.markdown("---")
    conn = get_db_connection()
    my_activities = pd.read_sql_query(f"SELECT * FROM activities WHERE username='{st.session_state.username}' ORDER BY timestamp DESC LIMIT 50", conn)
    my_risks = pd.read_sql_query(f"SELECT * FROM risk_analyses WHERE username='{st.session_state.username}' ORDER BY timestamp DESC LIMIT 20", conn)
    conn.close()
    tab1, tab2 = st.tabs(["📋 My Activities", "📈 My Risk Analyses"])
    with tab1:
        if not my_activities.empty:
            for _, row in my_activities.iterrows():
                st.markdown(f"""
                <div class="activity-card">
                    <strong>{row['activity_type']}</strong><br>
                    {row['description']}<br>
                    <span class="activity-time">{row['timestamp']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No activities yet")
    with tab2:
        if not my_risks.empty:
            for _, row in my_risks.iterrows():
                st.markdown(f"""
                <div class="activity-card">
                    <strong>Risk: {row['risk_result']}</strong><br>
                    Age: {row['age']}, Hours: {row['daily_hours']}, Work: {'Yes' if row['work_related'] == 1 else 'No'}<br>
                    Platform: {row['platform']}<br>
                    <span class="activity-time">{row['timestamp']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No risk analyses yet")

# ----------------------------------------------------------------------
# USAGE ANALYTICS
# ----------------------------------------------------------------------
elif st.session_state.dashboard_menu == "analytics":
    st.markdown("## 📈 Usage Analytics")
    if st.button("← Back to Dashboard", key="back_analytics"):
        st.session_state.dashboard_menu = "main"
        st.rerun()
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📝 Log Usage", "📊 View Analytics", "📅 History"])
    with tab1:
        st.markdown("### Log Your Daily Usage by App")
        st.markdown("You can log multiple apps for the same day - each entry is separate.")
        with st.form("usage_form"):
            col1, col2 = st.columns(2)
            with col1:
                log_date = st.date_input("Date", datetime.now().date())
                app_name = st.selectbox("App/Platform", ["TikTok", "Instagram", "Telegram", "YouTube", "Facebook", "LinkedIn", "Snapchat", "WhatsApp", "Twitter", "Google", "Other"])
            with col2:
                hours = st.number_input("Hours", 0, 24, 2)
                minutes = st.selectbox("Minutes", [0, 15, 30, 45])
                work_related = st.radio("Was this work-related?", ["Yes", "No"])
            if st.form_submit_button("Save Usage Entry", use_container_width=True):
                work_val = 1 if work_related == "Yes" else 0
                save_usage_entry(st.session_state.username, log_date, app_name, hours, minutes, work_val)
                st.success(f"✅ Logged {hours}h {minutes}m on {app_name}")
                st.balloons()
        st.markdown("---")
        st.markdown("#### Today's Logged Apps")
        today = datetime.now().date()
        conn = get_db_connection()
        today_usage = pd.read_sql_query(f"""
            SELECT app_name, hours, minutes, work_related 
            FROM usage_tracking 
            WHERE username='{st.session_state.username}' AND date='{today}'
            ORDER BY timestamp DESC
        """, conn)
        conn.close()
        if not today_usage.empty:
            for _, row in today_usage.iterrows():
                work_text = "💼 Work" if row['work_related'] == 1 else "🏠 Personal"
                st.markdown(f"""
                <div class="app-entry">
                    <strong>{row['app_name']}</strong>: {row['hours']}h {row['minutes']}m ({work_text})
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No apps logged today")
    with tab2:
        time_range = st.selectbox("Time Range", ["Last 7 days", "Last 30 days", "Last 90 days"])
        days = 7 if "7" in time_range else 30 if "30" in time_range else 90
        usage_df = get_user_usage_by_app(st.session_state.username, days)
        if not usage_df.empty:
            daily_total = usage_df.groupby('date')['total_minutes'].sum().reset_index()
            daily_total['hours'] = daily_total['total_minutes'] / 60
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Days Tracked", len(daily_total))
            with col2:
                avg_minutes = daily_total['total_minutes'].mean()
                st.metric("Daily Average", f"{avg_minutes/60:.1f} hrs")
            with col3:
                total_minutes = daily_total['total_minutes'].sum()
                st.metric("Total Usage", f"{total_minutes/60:.1f} hrs")
            with col4:
                most_used = usage_df.groupby('app_name')['total_minutes'].sum().idxmax()
                st.metric("Most Used App", most_used)
            # Work vs Personal
            work_data = usage_df.groupby('work_related')['total_minutes'].sum().reset_index()
            work_data['type'] = work_data['work_related'].map({0: 'Personal', 1: 'Work'})
            col_a, col_b = st.columns(2)
            with col_a:
                fig1 = px.pie(work_data, values='total_minutes', names='type', title='Work vs Personal Usage')
                st.plotly_chart(fig1, use_container_width=True)
            with col_b:
                fig2 = px.line(daily_total, x='date', y='hours', title='Daily Usage Trend')
                st.plotly_chart(fig2, use_container_width=True)
            # App breakdown
            app_stats = usage_df.groupby('app_name')['total_minutes'].sum().reset_index()
            app_stats['hours'] = app_stats['total_minutes'] / 60
            app_stats = app_stats.sort_values('hours', ascending=False)
            fig3 = px.bar(app_stats, x='app_name', y='hours', title='Usage by App')
            st.plotly_chart(fig3, use_container_width=True)
            # Top days
            st.markdown("#### Top 5 Highest Usage Days")
            top_days = daily_total.nlargest(5, 'total_minutes')[['date', 'hours']]
            top_days['hours'] = top_days['hours'].round(1)
            st.dataframe(top_days, use_container_width=True)
        else:
            st.info("No usage data yet. Start logging your apps!")
    with tab3:
        usage_df = get_user_usage_by_app(st.session_state.username, 365)
        if not usage_df.empty:
            display_df = usage_df.copy()
            display_df['usage'] = display_df['hours'].astype(str) + "h " + display_df['minutes'].astype(str) + "m"
            display_df['type'] = display_df['work_related'].map({0: 'Personal', 1: 'Work'})
            display_df = display_df[['date', 'app_name', 'usage', 'type']].sort_values('date', ascending=False)
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
            st.info("No usage history yet")

# ----------------------------------------------------------------------
# ADMIN: USER MANAGEMENT
# ----------------------------------------------------------------------
elif st.session_state.dashboard_menu == "user_management" and st.session_state.is_admin:
    st.markdown("## 👥 User Management")
    if st.button("← Back to Dashboard", key="back_user_mgt"):
        st.session_state.dashboard_menu = "main"
        st.rerun()
    st.markdown("---")
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

# ----------------------------------------------------------------------
# ADMIN: COMMENTS
# ----------------------------------------------------------------------
elif st.session_state.dashboard_menu == "comments" and st.session_state.is_admin:
    st.markdown("## 💬 Public Comments")
    if st.button("← Back to Dashboard", key="back_comments"):
        st.session_state.dashboard_menu = "main"
        st.rerun()
    st.markdown("---")
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

# ----------------------------------------------------------------------
# ADMIN: ACTIVITY LOG
# ----------------------------------------------------------------------
elif st.session_state.dashboard_menu == "activity" and st.session_state.is_admin:
    st.markdown("## 📋 Activity Log")
    if st.button("← Back to Dashboard", key="back_activity_log"):
        st.session_state.dashboard_menu = "main"
        st.rerun()
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📊 All Activities", "📈 Risk Analyses", "👥 User Logins", "🤖 Model Metrics"])
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
                    Result: {row['risk_result']} | Age: {row['age']}, Hours: {row['daily_hours']}, Work: {'Yes' if row['work_related'] == 1 else 'No'}<br>
                    Platform: {row['platform']}<br>
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
    with tab4:
        conn = get_db_connection()
        metrics_df = pd.read_sql_query("SELECT * FROM model_metrics ORDER BY timestamp DESC", conn)
        conn.close()
        if not metrics_df.empty:
            for _, row in metrics_df.iterrows():
                st.markdown(f"""
                <div class="activity-card">
                    <strong>🤖 Model Training #{_+1}</strong><br>
                    Accuracy: {row['accuracy']:.2%} | Precision: {row['precision']:.2%} | Recall: {row['recall']:.2%} | F1: {row['f1_score']:.2%}<br>
                    Training Samples: {row['training_samples']}<br>
                    <span class="activity-time">{row['timestamp']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No model metrics yet - model hasn't been trained")

# ----------------------------------------------------------------------
# ADMIN: MODEL FEEDBACK (shows all entries, with retrain button)
# ----------------------------------------------------------------------
elif st.session_state.dashboard_menu == "feedback" and st.session_state.is_admin:
    st.markdown("## 📊 Model Feedback Analysis")
    if st.button("← Back to Dashboard", key="back_feedback"):
        st.session_state.dashboard_menu = "main"
        st.rerun()
    st.markdown("---")
    st.markdown("""
    <div class="info-box">
        <h4>How Model Feedback Works:</h4>
        <p>This page shows all the like/unlike feedback received from users after risk analyses.</p>
        <ul>
            <li><strong>👍 Likes:</strong> Predictions users confirmed as accurate - used for training</li>
            <li><strong>👎 Unlikes:</strong> Predictions users flagged as inaccurate - used for error analysis</li>
        </ul>
        <p><strong>The model retrains automatically after every "like" feedback.</strong></p>
    </div>
    """, unsafe_allow_html=True)
    conn = get_db_connection()
    total_feedback = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
    like_count = conn.execute("SELECT COUNT(*) FROM feedback WHERE feedback='like'").fetchone()[0]
    unlike_count = conn.execute("SELECT COUNT(*) FROM feedback WHERE feedback='unlike'").fetchone()[0]
    conn.close()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total Feedback", total_feedback)
    with col2:
        st.metric("👍 Likes", like_count)
    with col3:
        st.metric("👎 Unlikes", unlike_count)

    if total_feedback == 0:
        st.warning("⚠️ No feedback has been collected yet. Ask users to click 'Yes' or 'No' after a risk analysis.")
    else:
        conn = get_db_connection()
        feedback_df = pd.read_sql_query("SELECT * FROM feedback ORDER BY timestamp DESC", conn)
        conn.close()
        st.dataframe(feedback_df, use_container_width=True)

        if st.button("🔄 Retrain Model Now (forced)", use_container_width=True):
            with st.spinner("Retraining AdaBoost model with all available 'like' feedback..."):
                result = train_model_from_feedback()
                if result:
                    st.success(f"✅ Model retrained! New accuracy: {result['metrics']['accuracy']:.2%}")
                else:
                    st.warning("⚠️ Need at least one 'like' feedback to retrain.")

# ----------------------------------------------------------------------
# FOOTER
# ----------------------------------------------------------------------
st.markdown("""
<footer>
    Developed by Getaye Fiseha | Using AdaBoost Algorithm Machine Learning Technique | Addis Ababa University | © 2026
</footer>
""", unsafe_allow_html=True)
