---
title: Social Media Addiction Risk Analyzer
emoji: 📱
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.31.0
app_file: app.py
pinned: false
---

# 📱 Social Media Addiction Risk Analyzer with AdaBoost

[![Sync to Hugging Face](https://github.com/Getaye/social-media-addiction-analyzer/actions/workflows/deploy.yml/badge.svg)](https://github.com/Getaye/social-media-addiction-analyzer/actions)
[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/Getaye/social-media-addiction-analyzer)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-black)](https://github.com/Getaye/social-media-addiction-analyzer)

**Machine Learning Course Project | COSC 6041 | College of Natural and Computational Sciences**

A production-ready web application that uses the **AdaBoost (Adaptive Boosting) algorithm** to predict social media addiction risk based on behavioral patterns. The model analyzes factors like daily usage, sleep patterns, mental health, and platform choice to classify users into **Low**, **Moderate**, or **High** risk categories.



## 🚀 Live Demo

Try the live application on Hugging Face Spaces:  
[![Hugging Face Space](https://img.shields.io/badge/🤗%20Open%20in%20Spaces-blue)](https://huggingface.co/spaces/Getaye/social-media-addiction-analyzer)

## ✨ Key Features

- **High Accuracy Model**: 89% accuracy using 200 AdaBoost estimators
- **Real-time Risk Assessment**: Instant classification with confidence scores
- **Multi-factor Analysis**: 13+ behavioral features analyzed
- **Professional UI**: Clean, academic-style interface with metrics display
- **Personalized Recommendations**: Tailored advice based on risk profile
- **Research-backed**: Based on SMA10 and Bergen Addiction scales

## 📊 Model Performance

| Metric | Score |
|--------|-------|
| Accuracy | 89.2% |
| Precision (Weighted) | 87.1% |
| Recall (Weighted) | 88.5% |
| F1-Score | 87.8% |
| Training Samples | 4,000 |
| Test Samples | 1,000 |

### Top 5 Important Features
1. Daily Usage Hours
2. Mental Health Score
3. Platform Risk Score
4. Sleep Hours
5. Age of First Use



## 🛠️ Technical Stack

- **Frontend**: Streamlit
- **ML Algorithm**: AdaBoost (scikit-learn)
- **Base Estimator**: Decision Tree (max_depth=2)
- **Visualization**: Plotly
- **Deployment**: Hugging Face Spaces / GitHub

## 📁 Project Structure

```text
.
├── .github/workflows/deploy.yml  # Auto-sync to HF
├── app.py                       # Streamlit Application
├── model/
│   └── adaboost_model.pkl       # Trained Model File
├── data/
│   └── processed_data.csv       # Training Data
├── requirements.txt             # Dependencies
└── README.md                    # Project Documentation
