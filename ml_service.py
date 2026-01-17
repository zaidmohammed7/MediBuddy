import joblib
import os
import numpy as np

# Load model artifacts once when the server starts
# We use try/except so the app doesn't crash if you haven't run train_model.py yet
try:
    MODEL = joblib.load('model_forest.pkl')
    ENCODER = joblib.load('model_encoder.pkl')
    MODEL_LOADED = True
    print("AI Model loaded successfully.")
except Exception as e:
    print(f"AI Model not found: {e}. Run train_model.py first.")
    MODEL = None
    ENCODER = None
    MODEL_LOADED = False

def predict_disease_with_ai(symptom_list, top_n=3):
    """
    Takes a list of strings ['fever', 'cough']
    Returns a list of dicts [{'disease': 'Flu', 'confidence': 0.85}, ...]
    """
    if not MODEL_LOADED or not symptom_list:
        return []

    # 1. Transform input to vector (Feature Engineering)
    # The encoder expects a list of lists, e.g. [['fever', 'cough']]
    vector = ENCODER.transform([symptom_list])

    # 2. Get probabilities
    probs = MODEL.predict_proba(vector)[0]
    
    # 3. Map probabilities to class names
    classes = MODEL.classes_
    
    # Zip them together
    results = []
    for i, disease_name in enumerate(classes):
        score = probs[i]
        if score > 0.05: # Filter out very low probability
            results.append({
                "disease": disease_name,
                "confidence": float(round(score, 2))
            })
            
    # 4. Sort by confidence
    results.sort(key=lambda x: x['confidence'], reverse=True)
    
    return results[:top_n]