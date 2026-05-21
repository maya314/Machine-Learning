"""
train_model.py
Run this script to generate a synthetic diabetes dataset and train + save the model.
Usage: python train_model.py
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import pickle
import os

# -----------------------------------------------------------
# Step 1: Generate a synthetic Pima Indians-like dataset
# -----------------------------------------------------------
np.random.seed(42)
n = 768

data = {
    'Pregnancies':            np.random.randint(0, 17, n),
    'Glucose':                np.random.randint(44, 200, n),
    'BloodPressure':          np.random.randint(24, 122, n),
    'SkinThickness':          np.random.randint(0, 99, n),
    'Insulin':                np.random.randint(0, 846, n),
    'BMI':                    np.round(np.random.uniform(18.0, 67.1, n), 1),
    'DiabetesPedigreeFunction': np.round(np.random.uniform(0.078, 2.42, n), 3),
    'Age':                    np.random.randint(21, 81, n),
}

# Realistic outcome based on glucose + BMI
glucose = data['Glucose']
bmi     = data['BMI']
age     = data['Age']
outcome = ((glucose > 140) | (bmi > 35) | (age > 50)).astype(int)
# Add noise
flip = np.random.rand(n) < 0.15
outcome = np.where(flip, 1 - outcome, outcome)
data['Outcome'] = outcome

df = pd.DataFrame(data)
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path   = os.path.join(script_dir, 'diabetes.csv')
df.to_csv(csv_path, index=False)
print(f"✅ Dataset saved to {csv_path}  ({n} rows)")

# -----------------------------------------------------------
# Step 2: Preprocess
# -----------------------------------------------------------
# Columns where 0 is medically impossible — replace with median
zero_cols = ['Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI']
for col in zero_cols:
    df[col] = df[col].replace(0, np.nan)
    df[col] = df[col].fillna(df[col].median())

X = df.drop('Outcome', axis=1)
y = df['Outcome']

# -----------------------------------------------------------
# Step 3: Split
# -----------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# -----------------------------------------------------------
# Step 4: Scale
# -----------------------------------------------------------
scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

# -----------------------------------------------------------
# Step 5: Train Logistic Regression
# -----------------------------------------------------------
model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X_train_sc, y_train)

y_pred = model.predict(X_test_sc)
acc    = accuracy_score(y_test, y_pred)
print(f"✅ Model Accuracy: {acc * 100:.2f}%")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['Not Diabetic', 'Diabetic']))

# -----------------------------------------------------------
# Step 6: Save model + scaler
# -----------------------------------------------------------
pkl_path = os.path.join(script_dir, 'model.pkl')
with open(pkl_path, 'wb') as f:
    pickle.dump({'model': model, 'scaler': scaler}, f)
print(f"✅ Model saved to {pkl_path}")
