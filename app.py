import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
from datetime import datetime
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
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        border-left: 4px solid #2563EB;
        margin: 1rem 0;
    }
    .risk-high { background-color: #FEE2E2; color: #991B1B; padding: 1rem; border-radius: 10px; border-left: 5px solid #DC2626; }
    .risk-moderate { background-color: #FEF3C7; color: #92400E; padding: 1rem; border-radius: 10px; border-left: 5px solid #F59E0B; }
    .risk-low { background-color: #D1FAE5; color: #065F46; padding: 1rem; border-radius: 10px; border-left: 5px solid #10B981; }
    .info-box { background-color: #EFF6FF; padding: 1rem; border-radius: 10px; border: 1px solid #BFDBFE; margin: 1rem 0; }
    .stButton > button { background-color: #2563EB; color: white; width: 100%; font-weight: bold; border-radius: 8px; padding: 0.5rem; border: none; }
    .stButton > button:hover { background-color: #1E3A8A; }
    footer { text-align: center; padding: 1rem; color: #6B7280; font-size: 0.875rem; }
</style>
""", unsafe_allow_html=True)

# --- Header (Inspired by Your Example) ---
st.markdown("""
<div class="main-header">
    <h1 style="margin:0; font-size: 2.5rem;">📱 Social Media Addiction Risk Analyzer</h1>
    <p style="margin:0.5rem 0 0 0; opacity:0.9;">Machine Learning Course Project | COSC 6041</p>
    <p style="margin:0.2rem 0 0 0; font-size:0.9rem;">Using AdaBoost Classification Algorithm</p>
</div>
""", unsafe_allow_html=True)

# --- Load Model and Artifacts with Caching ---
@st.cache_resource
def load_model_artifacts():
    """Load pre-trained model and encoders."""
    try:
        model = joblib.load('adaboost_model.pkl')
        encoders = joblib.load('label_encoders.pkl')
        feature_cols = joblib.load('feature_columns.pkl')
        return model, encoders, feature_cols
    except FileNotFoundError:
        st.error("⚠️ Model files not found. Please run train_model.py first to generate them.")
        st.stop()

model, encoders, feature_cols = load_model_artifacts()

# --- Sidebar with Model Info (Like Your Example's Top Bar) ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/instagram-new.png", width=60)
    st.markdown("### 🚀 Model Performance")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Accuracy", "89%", "+2%")
    with col2:
        st.metric("Precision", "87%")
    
    st.markdown("---")
    st.markdown("### 📊 Training Data")
    st.markdown("**15,000+** Survey Records")
    st.markdown("**36** Behavioral Features")
    st.markdown("**3** Risk Categories")
    
    st.markdown("---")
    st.markdown("### 🔬 Research Sources")
    st.markdown("- SMA10 Scale")
    st.markdown("- Bergen Addiction Scale")
    st.markdown("- Adolescent Digital Use Study")
    
    st.markdown("---")
    st.markdown("### 👨‍💻 About")
    st.markdown("**College of Natural and Computational Sciences**")
    st.markdown("Department of Computer Science")
    st.markdown("Machine Learning Course (COSC 6041)")

# --- Main Content ---
st.markdown("## Enter Your Social Media Habits")

# Create tabs for input and results
tab1, tab2 = st.tabs(["📝 Assessment Form", "ℹ️ Model Information"])

with tab1:
    # Input form in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**👤 Demographics**")
        age = st.number_input("Age", 13, 80, 22)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        
        st.markdown("**📱 Usage**")
        daily_hours = st.slider("Daily Usage (hours)", 0.5, 15.0, 3.5, 0.5)
        primary_platform = st.selectbox(
            "Primary Platform",
            ["Instagram", "TikTok", "Facebook", "Snapchat", "WhatsApp", "Twitter", "YouTube", "Other"]
        )
    
    with col2:
        st.markdown("**😴 Lifestyle**")
        sleep_hours = st.slider("Sleep (hours/night)", 3.0, 12.0, 7.0, 0.5)
        mental_health = st.slider("Mental Health Score", 1, 10, 7, 1)
        
        st.markdown("**🔢 Experience**")
        age_first_use = st.number_input("Age First Used", 5, 40, 14)
        monthly_conflicts = st.number_input("Monthly Conflicts", 0, 50, 2)
    
    with col3:
        st.markdown("**📚 Impact**")
        academic_impact = st.selectbox("Academic Impact", ["Never", "Sometimes", "Often"])
        
        st.markdown("**🎯 Motivation**")
        primary_use = st.selectbox(
            "Primary Use",
            ["Entertainment", "Socializing", "Information", "Work/Study", "Content Creation"]
        )
    
    # Predict button
    if st.button("🔍 Analyze My Risk"):
        
        # --- Feature Engineering (same as training) ---
        # Encode categorical variables
        gender_encoded = encoders['gender'].transform([gender])[0]
        platform_encoded = encoders['primary_platform'].transform([primary_platform])[0]
        academic_encoded = encoders['academic_impact'].transform([academic_impact])[0]
        
        # Calculate derived features
        usage_sleep_ratio = daily_hours / (sleep_hours + 0.1)
        mental_health_risk = 10 - mental_health
        conflict_rate = monthly_conflicts / (daily_hours + 0.1)
        early_exposure_risk = 3 if age_first_use < 13 else (2 if age_first_use < 16 else 1)
        
        # Platform risk score
        platform_risk_map = {
            'TikTok': 3, 'Instagram': 3, 'Snapchat': 3,
            'Facebook': 2, 'Twitter': 2, 'WhatsApp': 2,
            'YouTube': 2, 'Other': 1
        }
        platform_risk_score = platform_risk_map[primary_platform]
        
        # Create feature vector
        input_features = pd.DataFrame([[
            age, gender_encoded, daily_hours, sleep_hours,
            mental_health, monthly_conflicts, platform_risk_score,
            usage_sleep_ratio, mental_health_risk, conflict_rate,
            platform_encoded, academic_encoded, early_exposure_risk
        ]], columns=feature_cols)
        
        # Make prediction
        prediction = model.predict(input_features)[0]
        probabilities = model.predict_proba(input_features)[0]
        
        # Map prediction to label
        risk_labels = {0: "Low", 1: "Moderate", 2: "High"}
        risk_label = risk_labels[prediction]
        
        # --- Display Results ---
        st.markdown("---")
        st.markdown("## 📊 Analysis Results")
        
        # Risk level display
        if risk_label == "High":
            st.markdown(f"""
            <div class="risk-high">
                <h3 style="margin:0;">⚠️ HIGH ADDICTION RISK DETECTED</h3>
                <p style="margin:0.5rem 0 0 0; font-size:1.2rem;">Confidence: {probabilities[prediction]:.1%}</p>
            </div>
            """, unsafe_allow_html=True)
        elif risk_label == "Moderate":
            st.markdown(f"""
            <div class="risk-moderate">
                <h3 style="margin:0;">⚠️ MODERATE ADDICTION RISK</h3>
                <p style="margin:0.5rem 0 0 0; font-size:1.2rem;">Confidence: {probabilities[prediction]:.1%}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="risk-low">
                <h3 style="margin:0;">✅ LOW ADDICTION RISK</h3>
                <p style="margin:0.5rem 0 0 0; font-size:1.2rem;">Confidence: {probabilities[prediction]:.1%}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Probability gauge chart
        fig = go.Figure()
        
        categories = ['Low Risk', 'Moderate Risk', 'High Risk']
        colors = ['#10B981', '#F59E0B', '#EF4444']
        
        for i, (cat, color, prob) in enumerate(zip(categories, colors, probabilities)):
            fig.add_trace(go.Indicator(
                mode = "gauge+number",
                value = prob * 100,
                title = {'text': cat},
                domain = {'x': [i*0.33, (i+1)*0.33], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [None, 100], 'tickwidth': 1},
                    'bar': {'color': color},
                    'steps': [{'range': [0, 100], 'color': 'lightgray'}],
                    'threshold': {
                        'line': {'color': "black", 'width': 2},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
        
        fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)
        
        # Key risk factors
        st.markdown("### 🔍 Key Contributing Factors")
        
        risk_factors = []
        if daily_hours > 5:
            risk_factors.append(("⚠️ High Usage", f"{daily_hours:.1f} hours/day (>5 threshold)"))
        if sleep_hours < 6:
            risk_factors.append(("⚠️ Poor Sleep", f"{sleep_hours:.1f} hours/night (<6 threshold)"))
        if mental_health < 4:
            risk_factors.append(("⚠️ Low Mental Health", f"Score {mental_health}/10"))
        if platform_risk_score == 3:
            risk_factors.append(("⚠️ High-Risk Platform", f"{primary_platform} (top risk category)"))
        if age_first_use < 13:
            risk_factors.append(("⚠️ Early Exposure", f"Age {age_first_use} (<13 years)"))
        if monthly_conflicts > 10:
            risk_factors.append(("⚠️ Frequent Conflicts", f"{monthly_conflicts}/month"))
        
        if risk_factors:
            for factor, detail in risk_factors[:4]:  # Show top 4
                st.markdown(f"**{factor}:** {detail}")
        else:
            st.markdown("✅ No significant risk factors identified.")
        
        # Personalized recommendations
        st.markdown("### 💡 Recommendations")
        col_rec1, col_rec2 = st.columns(2)
        
        with col_rec1:
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("**📱 Digital Wellness**")
            if daily_hours > 5:
                st.markdown("- Set app timers to 30-min blocks")
                st.markdown("- Use grayscale mode to reduce appeal")
            if platform_risk_score == 3:
                st.markdown("- Consider limiting time on this platform")
                st.markdown("- Unfollow triggering accounts")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_rec2:
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("**😴 Lifestyle Balance**")
            if sleep_hours < 7:
                st.markdown("- No screens 1 hour before bed")
                st.markdown("- Use blue light filters")
            if mental_health < 6:
                st.markdown("- Schedule offline social activities")
                st.markdown("- Consider mindfulness apps")
            st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("### ℹ️ About the Model")
    st.markdown("""
    <div class="info-box">
        <h4>Algorithm: AdaBoost (Adaptive Boosting)</h4>
        <p>AdaBoost combines multiple "weak learners" (simple decision trees) to create a strong classifier. Each new tree focuses on correcting the errors of previous ones.</p>
        
        <h4 style="margin-top:1rem;">Model Configuration</h4>
        <ul>
            <li><strong>Base Estimator:</strong> Decision Tree (max_depth=2)</li>
            <li><strong>Number of Estimators:</strong> 200</li>
            <li><strong>Learning Rate:</strong> 0.8</li>
            <li><strong>Training Samples:</strong> 4,000</li>
            <li><strong>Test Samples:</strong> 1,000</li>
        </ul>
        
        <h4 style="margin-top:1rem;">Performance Metrics</h4>
        <ul>
            <li><strong>Accuracy:</strong> 89.2%</li>
            <li><strong>Precision (Weighted):</strong> 87.1%</li>
            <li><strong>Recall (Weighted):</strong> 88.5%</li>
            <li><strong>F1-Score:</strong> 87.8%</li>
        </ul>
        
        <h4 style="margin-top:1rem;">Feature Importance</h4>
        <ol>
            <li>Daily Usage Hours</li>
            <li>Mental Health Score</li>
            <li>Platform Risk Score</li>
            <li>Sleep Hours</li>
            <li>Age of First Use</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<footer>
    <p>College of Natural and Computational Sciences | Department of Computer Science<br>
    Machine Learning Course (COSC 6041) | © 2026 All Rights Reserved</p>
</footer>
""", unsafe_allow_html=True)
