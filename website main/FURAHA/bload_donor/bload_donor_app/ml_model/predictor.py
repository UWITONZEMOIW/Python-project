# bload_donor_app/ml_model/predictor.py
import pandas as pd # type: ignore
import os
import numpy as np
import joblib


# Load the model and scaler from disk
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, 'blood_donation_model.pkl')
scaler_path = os.path.join(BASE_DIR, 'scaler.pkl')

model = joblib.load(model_path)
scaler = joblib.load(scaler_path)

# List of features used during training (must match order and names)
FEATURES = [
    'Months since Last Donation',
    'Number of Donations',
    'Months since First Donation',
    'Donation_Frequency',
    'Donation_Regularity',
    'Donation_Rate'
]

def predict_donation(months_last, num_donations, months_first):
    """
    Takes donor stats and returns donation probability.
    """
    # Derived features
    donation_frequency = 0 if num_donations <= 1 else months_first / (num_donations - 1)
    donation_regularity = 0 if num_donations <= 2 else (
        np.random.normal(loc=1.0, scale=0.5) *
        (0.9 ** min(num_donations / 5, 3)) *
        min(months_first / 24, 2)
    )
    donation_rate = num_donations / max(months_first, 1)

    # Prepare input as a DataFrame with proper column names
    input_df = pd.DataFrame([[
        months_last,
        num_donations,
        months_first,
        donation_frequency,
        donation_regularity,
        donation_rate
    ]], columns=FEATURES)

    # Scale input and predict
    input_scaled = scaler.transform(input_df)
    probability = model.predict_proba(input_scaled)[0][1]

    return round(probability, 4)

