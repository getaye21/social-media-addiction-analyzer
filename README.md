# 📱 Social Media Addiction Risk Analyzer with AdaBoost

[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/yourusername/social-media-addiction-analyzer)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-black)](https://github.com/yourusername/social-media-addiction-analyzer)

**Machine Learning Course Project | COSC 6041 | College of Natural and Computational Sciences**

A production-ready web application that uses the **AdaBoost (Adaptive Boosting) algorithm** to predict social media addiction risk based on behavioral patterns. The model analyzes factors like daily usage, sleep patterns, mental health, and platform choice to classify users into **Low**, **Moderate**, or **High** risk categories.

![Demo Screenshot](screenshot.png) *(Add a screenshot of your app here)*

## 🚀 Live Demo

Try the live application on Hugging Face Spaces:  
[![Hugging Face Space](https://img.shields.io/badge/🤗%20Open%20in%20Spaces-blue)](https://huggingface.co/spaces/yourusername/social-media-addiction-analyzer)

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
