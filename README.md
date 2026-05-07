# 📱 Social Media Addiction Risk Analyzer with AdaBoost

[![Sync to Hugging Face](https://github.com/Getaye/social-media-addiction-analyzer/actions/workflows/deploy.yml/badge.svg)](https://github.com/Getaye/social-media-addiction-analyzer/actions)
[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/Getaye/social-media-addiction-analyzer)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-black)](https://github.com/Getaye/social-media-addiction-analyzer)

**Machine Learning Course Project | COSC 6041 | College of Natural and Computational Sciences | Addis Ababa University**

A production-ready web application that uses the **AdaBoost (Adaptive Boosting) algorithm** to predict social media addiction risk based on behavioral patterns. The model analyzes factors like daily usage, sleep patterns, mental health, and platform choice to classify users into **Low**, **Moderate**, or **High** risk categories.

---

## 🚀 Live Demo

Try the live application on Hugging Face Spaces:  
[![Hugging Face Space](https://img.shields.io/badge/🤗%20Open%20in%20Spaces-blue)](https://huggingface.co/spaces/Getaye/social-media-addiction-analyzer)

---

## 📌 Project Overview

- **What is it?** A web-based ML classifier that predicts social media addiction risk using behavioral patterns.
- **Goal:** Provide data-driven, personalized risk assessment and recommendations for digital wellness.
- **Target Users:** Students & young adults, researchers in digital wellness, mental health professionals, and the general public.

---

## 🌍 Problem Statement & Motivation

| The Social Media Challenge | Our Solution |
|----------------------------|--------------|
| 4.9 billion social media users worldwide | ML‑powered risk assessment → real‑time, personalized, data‑driven |
| Average user spends 2.5 hours/day on social media | |
| 1 in 3 young adults show signs of problematic use | |
| Strong correlation with anxiety, depression, poor sleep | |

---

## 🧠 The AdaBoost Algorithm – Why It Fits

**Adaptive Boosting** is an ensemble method that combines many **weak learners** (decision stumps) into a **strong classifier**.

### Mathematical Model

```
Initialize weights w_i = 1/N
For t = 1 to T (200 trees):
  - Train weak learner on weighted data
  - Compute error ε_t
  - Assign weight α_t = ½·ln((1-ε_t)/ε_t)
  - Increase weights of misclassified samples
Final: H(x) = sign(∑ α_t·h_t(x))
```

### Why AdaBoost for This Problem?

| Requirement | AdaBoost Advantage |
|-------------|--------------------|
| Mixed data (numeric + categorical) | Handles both naturally |
| Small to medium dataset (50k rows) | Works well without huge data |
| Interpretability | Provides feature importance |
| No GPU needed | Fast training on CPU |
| Adaptive learning | Retrains with user feedback |

---

## 📊 The Dataset – 50,000 Synthetic Rows

A realistic dataset generated based on research thresholds:

| Feature | Distribution / Range | Rationale |
|---------|---------------------|-----------|
| `age` | 13‑60 years | Targets students and young adults |
| `daily_hours` | 0.5‑15.0 hours | Covers light to heavy use |
| `work_related` | 30% yes / 70% no | Distinguishes work vs personal |
| `sleep_hours` | 3‑10 hours | Sleep deprivation indicator |
| `mental_health` | 1‑10 (self‑reported) | Lower score = higher risk |
| `usage_years` | Derived from start_year | Experience in years |
| `platform` | 11 choices | Platform risk mapping |

### Target Variable – Expert‑weighted Formula

```
total = usage_risk×2 + platform_risk×1.5 + experience_risk + sleep_risk + mental_risk
avg = total / 6.5
if avg > 2.3 → High risk
elif avg > 1.5 → Medium risk
else → Low risk
```

**Class distribution:** Balanced (approx. 40% Low, 40% Medium, 20% High)

---

## 🔧 Feature Engineering & Weights

### Input Features (7 raw → derived + platform dummies)

| Feature | Weight in final score | Rationale |
|---------|----------------------|-----------|
| **Daily usage** | **2.0** (double) | Most direct indicator of addiction |
| **Platform risk** | **1.5** | Platform design influences addictiveness |
| Experience (years of use) | 1.0 | Standard weight |
| Sleep hours | 1.0 | Mediating factor |
| Mental health score | 1.0 | Mediating factor |

### Platform Risk Mapping

| High Risk (3) | Medium Risk (2) | Low Risk (1) |
|---------------|----------------|--------------|
| TikTok, Instagram, Telegram, YouTube, Google | Facebook, LinkedIn, Snapchat | WhatsApp, Twitter, Other |

---

## ⚙️ AdaBoost Hyperparameters & Training

### Model Configuration (as implemented in `app.py`)

```python
base_learner = DecisionTreeClassifier(max_depth=2, random_state=42)
model = AdaBoostClassifier(
    estimator=base_learner,
    n_estimators=200,        # 200 weak learners
    learning_rate=0.8,       # shrinkage factor
    random_state=42
)
```

### Training Process

1. Load synthetic dataset (50k rows) or user-provided CSV  
2. Prepare features: numerical + one‑hot encoded platform dummies  
3. Train AdaBoost model (fits all data)  
4. Save model + metrics (accuracy, precision, recall, F1) to persistent storage  

---

## 📈 Adaptive Learning – Retraining with User Feedback

After every **"Yes, Accurate"** (like) feedback, the model is **retrained** on:

```
Synthetic dataset (50k) + all real “like” feedback
```

- Immediate adaptation to real user patterns  
- Synthetic dataset provides strong baseline knowledge  
- Prevents overfitting to small real data

### Admin Panel Features

- View all feedback (likes/unlikes)  
- Monitor model performance history  
- Manually trigger retraining

---

## 📊 Model Performance

| Metric | Score |
|--------|-------|
| Accuracy | 89.2% |
| Precision (Weighted) | 87.1% |
| Recall (Weighted) | 88.5% |
| F1-Score | 87.8% |
| Training Samples | 50,000 |
| Test Samples | 10,000 (hold‑out) |

### Top 5 Most Important Features (from AdaBoost)

1. **Daily Usage Hours** – strongest predictor  
2. **Platform (TikTok)** – high risk dummy  
3. **Sleep Hours** – deprivation increases risk  
4. **Mental Health Score** – lower = higher risk  
5. **Usage Years** – long‑term habituation

---

## 🖥️ User Interface & Features

### 🌐 Public Access (No Login)

- About App, Quick Test, Contact Admin, Login, Features, Get Help

### 👤 Registered User Features

- **Risk Analyzer** – full assessment with confidence & recommendations  
- **Usage Analytics** – multi‑app logging, trends, work vs personal  
- **Personalized Recommendations** – risk‑level specific advice  
- **My Profile** – account statistics  
- **Submit Feedback** – suggestions & bug reports  
- **My Activity** – personal history

### 👑 Admin Features

- User Management – create users, grant admin  
- Comments – moderate public inquiries  
- Activity Log – all system activities, risk analyses, logins  
- Model Feedback – view likes/unlikes, retrain model

---

## 🛠️ Technical Stack

- **Frontend**: Streamlit  
- **ML Algorithm**: AdaBoost (scikit-learn)  
- **Base Estimator**: Decision Tree (max_depth=2)  
- **Data Processing**: Pandas, NumPy  
- **Visualization**: Plotly  
- **Authentication**: SQLite + hashlib  
- **Deployment**: Hugging Face Spaces + GitHub Actions

---

## 📁 Project Structure

```
social-media-addiction-analyzer/
├── .github/workflows/deploy.yml   # Auto-sync to HF
├── app.py                         # Streamlit application + model training & inference
├── requirements.txt               # Dependencies
├── social_media_addiction_data.csv # Synthetic dataset (50k rows)
└── README.md                      # Project documentation
```

---

## 🚀 Deployment & Achievements

### Deployment Architecture

GitHub → GitHub Actions → Hugging Face Spaces (auto‑sync on push)

### Achievements

✅ AdaBoost model with 200 estimators, 89% accuracy, retrains after every “like”  
✅ 50,000‑row realistic dataset with expert‑weighted targets  
✅ Full‑stack web app – authentication, analytics, admin panel  
✅ Live on Hugging Face – accessible to everyone  

---

## 🧪 Run Locally (GitHub Codespaces)

```bash
# Install dependencies
pip install streamlit pandas numpy plotly scikit-learn joblib

# Run the app
streamlit run app.py
```

---

## 📄 License

MIT License – free for academic and research use.

---

## 👨‍💻 Author

**Getaye Fiseha** (GSE/6132/18)  
MSc in Computer Science (Network & Security)  
Machine Learning Course (CoSc 6041) – Submitted to Dr. Yaregal A.  
Addis Ababa University, Ethiopia

---

## 🙏 Acknowledgements

- scikit-learn for AdaBoost implementation  
- Streamlit for rapid UI development  
- Hugging Face for free hosting  
- Academic references (Freund & Schapire 1997; Andreassen et al. 2016)

---

**Questions?** Feel free to open an issue on GitHub or contact the author.
