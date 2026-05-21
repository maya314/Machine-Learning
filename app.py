"""
app.py  —  Flask Backend for BMI Categorizer & Diabetes Predictor
Includes: Signup, Login, Session management, Prediction
-----------------------------------------------------------------
Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

from flask import Flask, render_template, request, redirect, url_for, session
import pickle
import numpy as np
import os
import json
import hashlib

# ── Create the Flask application ──────────────────────────────
app = Flask(__name__)
app.secret_key = 'medpredict_secret_key_2024'   # needed for session cookies

# ── Simple file-based user storage (no database needed) ───────
USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')

def load_users():
    """Load all registered users from users.json file."""
    if not os.path.exists(USERS_FILE):
        return {}                     # empty dict if file doesn't exist yet
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    """Save all users to users.json file."""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    """Convert plain password to a secure hash (SHA-256)."""
    return hashlib.sha256(password.encode()).hexdigest()

# ── Load the trained model and scaler from model.pkl ──────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model.pkl')

with open(MODEL_PATH, 'rb') as f:
    saved = pickle.load(f)

model  = saved['model']
scaler = saved['scaler']


# ── BMI helper ────────────────────────────────────────────────
def calculate_bmi(weight_kg, height_cm):
    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m ** 2), 2)
    if bmi < 18.5:   category = "Underweight"
    elif bmi < 25.0: category = "Normal Weight"
    elif bmi < 30.0: category = "Overweight"
    else:            category = "Obese"
    return bmi, category


# ── Route: Auth page (Login + Signup) — GET ───────────────────
@app.route('/')
def auth():
    """Show the login/signup page if not logged in."""
    if 'username' in session:
        return redirect(url_for('dashboard'))   # already logged in → go to app
    return render_template('auth.html')


# ── Route: Signup — POST ──────────────────────────────────────
@app.route('/signup', methods=['POST'])
def signup():
    name     = request.form.get('name', '').strip()
    email    = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm  = request.form.get('confirm', '')

    users = load_users()

    # Validation
    if not name or not email or not password:
        return render_template('auth.html', signup_error='All fields are required.', active='signup')
    if password != confirm:
        return render_template('auth.html', signup_error='Passwords do not match.', active='signup')
    if len(password) < 6:
        return render_template('auth.html', signup_error='Password must be at least 6 characters.', active='signup')
    if email in users:
        return render_template('auth.html', signup_error='Email already registered. Please log in.', active='signup')

    # Save new user
    users[email] = {
        'name':     name,
        'email':    email,
        'password': hash_password(password)
    }
    save_users(users)

    # Auto-login after signup
    session['username'] = name
    session['email']    = email
    return redirect(url_for('dashboard'))


# ── Route: Login — POST ───────────────────────────────────────
@app.route('/login', methods=['POST'])
def login():
    email    = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    users = load_users()

    if email not in users:
        return render_template('auth.html', login_error='Email not found. Please sign up.', active='login')
    if users[email]['password'] != hash_password(password):
        return render_template('auth.html', login_error='Incorrect password. Try again.', active='login')

    # Successful login — save to session
    session['username'] = users[email]['name']
    session['email']    = email
    return redirect(url_for('dashboard'))


# ── Route: Logout ─────────────────────────────────────────────
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth'))


# ── Route: Dashboard (main predictor page) ────────────────────
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('auth'))
    return render_template('index.html', username=session['username'])


# ── Route: Predict — POST ─────────────────────────────────────
@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        return redirect(url_for('auth'))
    try:
        weight         = float(request.form['weight'])
        height         = float(request.form['height'])
        pregnancies    = float(request.form['pregnancies'])
        glucose        = float(request.form['glucose'])
        blood_pressure = float(request.form['blood_pressure'])
        skin_thickness = float(request.form['skin_thickness'])
        insulin        = float(request.form['insulin'])
        dpf            = float(request.form['dpf'])
        age            = float(request.form['age'])

        bmi, bmi_category = calculate_bmi(weight, height)

        features        = np.array([[pregnancies, glucose, blood_pressure,
                                      skin_thickness, insulin, bmi, dpf, age]])
        features_scaled = scaler.transform(features)
        prediction      = model.predict(features_scaled)[0]
        probability     = model.predict_proba(features_scaled)[0]

        result      = "Diabetic" if prediction == 1 else "Not Diabetic"
        confidence  = round(probability[prediction] * 100, 1)
        is_diabetic = (prediction == 1)

        return render_template(
            'index.html',
            username=session['username'],
            bmi=bmi,
            bmi_category=bmi_category,
            result=result,
            confidence=confidence,
            is_diabetic=is_diabetic,
            show_results=True
        )
    except Exception as e:
        return render_template('index.html', username=session['username'], error=str(e))


# ── Run ───────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5000)
