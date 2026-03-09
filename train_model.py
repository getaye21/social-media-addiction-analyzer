# train_model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder
import joblib
import warnings
warnings.filterwarnings('ignore')

print("=" * 50)
print("Training Social Media Addiction Model")
print("=" * 50)

# --- 1. Load and Prepare Dataset ---
# Using a synthetic dataset that mirrors real-world patterns from research
# (In a real scenario, you'd load 'social_media_usage.csv' here)
np.random.seed(42)
n_samples = 5000

print(f"\n📊 Generating {n_samples} sample records based on research patterns...")

data = {
    'age': np.random.randint(13, 50, n_samples),
    'gender': np.random.choice(['Male', 'Female', 'Other'], n_samples),
    'daily_usage_hours': np.random.uniform(0.5, 15.0, n_samples),
    'primary_platform': np.random.choice(
        ['Instagram', 'TikTok', 'Facebook', 'Snapchat', 'WhatsApp', 'Twitter', 'YouTube', 'Other'], 
        n_samples
    ),
    'sleep_hours': np.random.uniform(3.0, 10.0, n_samples),
    'mental_health_score': np.random.randint(1, 11, n_samples),
    'monthly_conflicts': np.random.poisson(3, n_samples),
    'academic_impact': np.random.choice(['Never', 'Sometimes', 'Often'], n_samples),
    'age_of_first_use': np.random.randint(8, 30, n_samples),
}
df = pd.DataFrame(data)

# --- 2. Feature Engineering (based on research) ---
print("🛠️  Engineering features...")

# Encode categorical features
le_dict = {}
for col in ['gender', 'primary_platform', 'academic_impact']:
    le = LabelEncoder()
    df[f'{col}_encoded'] = le.fit_transform(df[col])
    le_dict[col] = le

# Create risk indicators
df['usage_sleep_ratio'] = df['daily_usage_hours'] / (df['sleep_hours'] + 0.1)
df['mental_health_risk'] = 10 - df['mental_health_score']
df['conflict_rate'] = df['monthly_conflicts'] / (df['daily_usage_hours'] + 0.1)
df['early_exposure_risk'] = np.where(df['age_of_first_use'] < 13, 3, 
                                      np.where(df['age_of_first_use'] < 16, 2, 1))

# Platform risk mapping (based on research)
platform_risk_map = {
    'TikTok': 3, 'Instagram': 3, 'Snapchat': 3,
    'Facebook': 2, 'Twitter': 2, 'WhatsApp': 2,
    'YouTube': 2, 'Other': 1
}
df['platform_risk_score'] = df['primary_platform'].map(platform_risk_map)

# --- 3. Create Target Variable (Addiction Level) ---
print("🎯 Creating target labels (Low/Moderate/High)...")

# Calculate a composite addiction score
addiction_score = (
    df['daily_usage_hours'] * 0.30 +
    df['platform_risk_score'] * 0.20 +
    (10 - df['sleep_hours']) * 0.15 +
    (10 - df['mental_health_score']) * 0.20 +
    df['monthly_conflicts'] * 0.10 +
    df['early_exposure_risk'] * 0.05
)

# Normalize score to 0-10 range
addiction_score = (addiction_score - addiction_score.min()) / (addiction_score.max() - addiction_score.min()) * 10

# Create 3 classes
df['addiction_level'] = pd.cut(
    addiction_score, 
    bins=[0, 4, 7, 10], 
    labels=['Low', 'Moderate', 'High']
)
df['target'] = df['addiction_level'].map({'Low': 0, 'Moderate': 1, 'High': 2})

print(f"\n   Class Distribution:")
print(df['addiction_level'].value_counts(normalize=True).map(lambda x: f"{x:.1%}"))

# --- 4. Prepare Features for Model ---
feature_columns = [
    'age', 'gender_encoded', 'daily_usage_hours', 'sleep_hours',
    'mental_health_score', 'monthly_conflicts', 'platform_risk_score',
    'usage_sleep_ratio', 'mental_health_risk', 'conflict_rate',
    'primary_platform_encoded', 'academic_impact_encoded', 'early_exposure_risk'
]

X = df[feature_columns]
y = df['target']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"\n📦 Training set: {X_train.shape[0]} samples")
print(f"🧪 Test set: {X_test.shape[0]} samples")

# --- 5. Train AdaBoost Model ---
print("\n🤖 Training AdaBoost Classifier...")

base_estimator = DecisionTreeClassifier(max_depth=2, random_state=42)  # Slightly deeper stumps
model = AdaBoostClassifier(
    estimator=base_estimator,
    n_estimators=200,
    learning_rate=0.8,
    random_state=42,
    algorithm='SAMME'
)

model.fit(X_train, y_train)

# --- 6. Evaluate Model ---
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"\n✅ Test Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")

# Per-class metrics
print("\n📈 Classification Report:")
print(classification_report(y_test, y_pred, target_names=['Low', 'Moderate', 'High']))

# --- 7. Save Model and Artifacts ---
print("\n💾 Saving model and encoders...")
joblib.dump(model, 'adaboost_model.pkl')
joblib.dump(le_dict, 'label_encoders.pkl')
joblib.dump(feature_columns, 'feature_columns.pkl')

print("\n" + "=" * 50)
print("✅ Training Complete! Files saved:")
print("   - adaboost_model.pkl")
print("   - label_encoders.pkl")
print("   - feature_columns.pkl")
print("=" * 50)

# Optional: Show feature importance
importance = pd.DataFrame({
    'feature': feature_columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)
print("\n🔝 Top 5 Most Important Features:")
print(importance.head(5).to_string(index=False))
