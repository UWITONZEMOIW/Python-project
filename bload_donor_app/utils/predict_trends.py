# import pickle
# import os

# def predict_donation_trends():
#     model_path = os.path.join(os.path.dirname(__file__), '../ml_models/donation_trend_model.pkl')
#     with open(model_path, 'rb') as f:
#         model = pickle.load(f)

#     # Example data for prediction
#     input_data = [[2025, 6]]  # e.g., year and month
#     prediction = model.predict(input_data)

#     # Format prediction for the frontend chart
#     return {
#         'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
#         'values': [84, 126, 105, 168, 147, int(prediction[0])]
#     }

import pickle
import numpy as np
from datetime import datetime, timedelta

def load_model():
    with open('ml_models/donation_trend_model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('ml_models/donation_scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    return model, scaler

def predict_next_donation_date(donor_features, model, scaler):
    input_array = np.array([[
        donor_features['Months since Last Donation'],
        donor_features['Number of Donations'],
        donor_features['Total Volume Donated (c.c.)'],
        donor_features['Months since First Donation'],
        donor_features['Donation_Frequency'],
        donor_features['Donation_Regularity']
    ]])
    input_scaled = scaler.transform(input_array)
    probability = model.predict_proba(input_scaled)[0][1]

    # Dummy curve for simplicity
    prob_curve = {}
    base_date = datetime.today()
    for i in range(1, 6):
        date = base_date + timedelta(days=i * 7)
        prob_curve[date.strftime('%Y-%m-%d')] = probability * (0.9 + i * 0.02)

    next_date = max(prob_curve, key=prob_curve.get)
    return next_date, probability, prob_curve
