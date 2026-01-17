import mysql.connector
import pandas as pd
import numpy as np
import joblib
import random
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Reuse your config
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "[PASSWORD]",
    "database": "[DATABASE_NAME]",
}

def get_db_data():
    """Fetch the 'Ground Truth' from SQL: Which disease has which symptoms?"""
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    query = """
        SELECT d.disease_name, s.symptom_name
        FROM disease d
        JOIN disease_symptom ds ON d.disease_id = ds.disease_id
        JOIN symptom s ON s.symptom_id = ds.symptom_id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Group by disease: {'Flu': ['fever', 'cough'], 'Covid': ['fever', 'loss_of_smell']}
    disease_map = df.groupby('disease_name')['symptom_name'].apply(list).to_dict()
    
    # Get a list of ALL possible unique symptoms for noise generation
    all_symptoms = df['symptom_name'].unique().tolist()
    
    return disease_map, all_symptoms

def generate_synthetic_data(disease_map, all_symptoms, samples_per_disease=50):
    """
    Generates synthetic patient data.
    For each disease, create 'samples_per_disease' fake records.
    """
    data = []
    labels = []

    print(f"Generating synthetic data for {len(disease_map)} diseases...")

    for disease, true_symptoms in disease_map.items():
        for _ in range(samples_per_disease):
            # Start with the true symptoms
            patient_symptoms = true_symptoms.copy()
            
            # 1. DROP SAMPLES (Simulate patient forgetting a symptom)
            # 20% chance to drop a symptom if they have more than 2
            if len(patient_symptoms) > 2 and random.random() < 0.2:
                patient_symptoms.remove(random.choice(patient_symptoms))

            # 2. ADD NOISE (Simulate patient having a random unrelated headache)
            # 10% chance to add a random symptom not associated with this disease
            if random.random() < 0.1:
                noise = random.choice(all_symptoms)
                if noise not in patient_symptoms:
                    patient_symptoms.append(noise)
            
            data.append(patient_symptoms)
            labels.append(disease)

    return data, labels

def train():
    # 1. Get Rules from DB
    disease_map, all_symptoms = get_db_data()

    # 2. Generate Data
    X_raw, y = generate_synthetic_data(disease_map, all_symptoms, samples_per_disease=100)

    # 3. Feature Engineering (Multi-Hot Encoding)
    # Converts ['fever', 'cough'] into [1, 0, 1, 0...]
    mlb = MultiLabelBinarizer()
    X = mlb.fit_transform(X_raw)

    # 4. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 5. Model Training
    print("Training Random Forest Classifier...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    # 6. Evaluation
    print("Model Evaluation:")
    print(classification_report(y_test, clf.predict(X_test)))

    # 7. Save Artifacts
    print("Saving model and encoder...")
    joblib.dump(clf, 'model_forest.pkl')
    joblib.dump(mlb, 'model_encoder.pkl')
    print("Done! You now have an AI model.")

if __name__ == "__main__":
    train()