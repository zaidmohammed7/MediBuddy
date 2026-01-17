import json
import os
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

import google.generativeai as genai
import mysql.connector
import pandas as pd
from dotenv import load_dotenv

# --- NEW: Import the AI Service ---
from ml_service import predict_disease_with_ai

# =============================================================================
# CONFIG
# =============================================================================

MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "[PASSWORD]",
    "database": "[DATABASE_NAME]",
    "charset": "utf8mb4",
    "use_unicode": True,
}

# API key lives in config/api.env at project root
load_dotenv("config/api.env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash-lite"

genai.configure(api_key=GEMINI_API_KEY)

# =============================================================================
# STATIC SETS (must match DB contents)
# =============================================================================

SYMPTOMS = {
    "abdominal_pain", "abnormal_menstruation", "acidity", "acute_liver_failure", "altered_sensorium",
    "anxiety", "back_pain", "belly_pain", "blackheads", "bladder_discomfort", "blister",
    "blood_in_sputum", "bloody_stool", "blurred_and_distorted_vision", "breathlessness",
    "brittle_nails", "bruising", "burning_micturition", "chest_pain", "chills",
    "cold_hands_and_feets", "coma", "congestion", "constipation", "continuous_feel_of_urine",
    "continuous_sneezing", "cough", "cramps", "dark_urine", "dehydration", "depression",
    "diarrhoea", "dischromic _patches", "distention_of_abdomen", "dizziness",
    "drying_and_tingling_lips", "enlarged_thyroid", "excessive_hunger", "extra_marital_contacts",
    "family_history", "fast_heart_rate", "fatigue", "fluid_overload", "foul_smell_of urine",
    "headache", "high_fever", "hip_joint_pain", "history_of_alcohol_consumption",
    "increased_appetite", "indigestion", "inflammatory_nails", "internal_itching",
    "irregular_sugar_level", "irritability", "irritation_in_anus", "itching", "joint_pain",
    "knee_pain", "lack_of_concentration", "lethargy", "loss_of_appetite", "loss_of_balance",
    "loss_of_smell", "malaise", "mild_fever", "mood_swings", "movement_stiffness",
    "mucoid_sputum", "muscle_pain", "muscle_wasting", "muscle_weakness", "nausea",
    "neck_pain", "nodal_skin_eruptions", "obesity", "pain_behind_the_eyes",
    "pain_during_bowel_movements", "pain_in_anal_region", "painful_walking", "palpitations",
    "passage_of_gases", "patches_in_throat", "phlegm", "polyuria", "prominent_veins_on_calf",
    "puffy_face_and_eyes", "pus_filled_pimples", "receiving_blood_transfusion",
    "receiving_unsterile_injections", "red_sore_around_nose", "red_spots_over_body",
    "redness_of_eyes", "restlessness", "runny_nose", "rusty_sputum", "scurring", "shivering",
    "silver_like_dusting", "sinus_pressure", "skin_peeling", "skin_rash", "slurred_speech",
    "small_dents_in_nails", "spinning_movements", "spotting_ urination", "stiff_neck",
    "stomach_bleeding", "stomach_pain", "sunken_eyes", "sweating", "swelled_lymph_nodes",
    "swelling_joints", "swelling_of_stomach", "swollen_blood_vessels", "swollen_extremeties",
    "swollen_legs", "throat_irritation", "toxic_look_(typhos)", "ulcers_on_tongue",
    "unsteadiness", "visual_disturbances", "vomiting", "watering_from_eyes",
    "weakness_in_limbs", "weakness_of_one_body_side", "weight_gain", "weight_loss",
    "yellow_crust_ooze", "yellow_urine", "yellowing_of_eyes", "yellowish_skin",
}

SPECIALIZATIONS = {
    "ADDICTION MEDICINE", "ADULT CONGENITAL HEART DISEASE (ACHD)", "ADVANCED HEART FAILURE AND TRANSPLANT CARDIOLOGY",
    "ALLERGY/IMMUNOLOGY", "ANESTHESIOLOGY", "ANESTHESIOLOGY ASSISTANT", "CARDIAC ELECTROPHYSIOLOGY",
    "CARDIAC SURGERY", "CARDIOVASCULAR DISEASE (CARDIOLOGY)", "CERTIFIED CLINICAL NURSE SPECIALIST (CNS)",
    "CERTIFIED NURSE MIDWIFE (CNM)", "CERTIFIED REGISTERED NURSE ANESTHETIST (CRNA)", "CHIROPRACTIC",
    "CLINICAL PSYCHOLOGIST", "CLINICAL SOCIAL WORKER", "COLORECTAL SURGERY (PROCTOLOGY)",
    "CRITICAL CARE (INTENSIVISTS)", "DENTAL ANESTHESIOLOGY", "DENTIST", "DERMATOLOGY",
    "DIAGNOSTIC RADIOLOGY", "EMERGENCY MEDICINE", "ENDOCRINOLOGY", "EPILEPTOLOGISTS",
    "FAMILY PRACTICE", "GASTROENTEROLOGY", "GENERAL PRACTICE", "GENERAL SURGERY",
    "GERIATRIC MEDICINE", "GERIATRIC PSYCHIATRY", "GYNECOLOGICAL ONCOLOGY", "HAND SURGERY",
    "HEMATOLOGY", "HEMATOLOGY/ONCOLOGY", "HEMATOPOIETIC CELL TRANSPLANTATION AND CELLULAR THERAPY",
    "HOSPICE/PALLIATIVE CARE", "HOSPITALIST", "INFECTIOUS DISEASE", "INTERNAL MEDICINE",
    "INTERVENTIONAL CARDIOLOGY", "INTERVENTIONAL PAIN MANAGEMENT", "INTERVENTIONAL RADIOLOGY",
    "MARRIAGE AND FAMILY THERAPIST", "MAXILLOFACIAL SURGERY", "MEDICAL GENETICS AND GENOMICS",
    "MEDICAL ONCOLOGY", "MEDICAL TOXICOLOGY", "MENTAL HEALTH COUNSELOR",
    "MICROGRAPHIC DERMATOLOGIC SURGERY (MDS)", "NEPHROLOGY", "NEUROLOGY", "NEUROPSYCHIATRY",
    "NEUROSURGERY", "NUCLEAR MEDICINE", "NURSE PRACTITIONER", "OBSTETRICS/GYNECOLOGY",
    "OCCUPATIONAL THERAPIST IN PRIVATE PRACTICE", "OPHTHALMOLOGY", "OPTOMETRY",
    "ORAL AND MAXILLOFACIAL PATHOLOGY", "ORAL AND MAXILLOFACIAL RADIOLOGY", "ORAL MEDICINE",
    "ORAL SURGERY", "OROFACIAL PAIN", "ORTHOPEDIC SURGERY", "OSTEOPATHIC MANIPULATIVE MEDICINE",
    "OTOLARYNGOLOGY", "PAIN MANAGEMENT", "PATHOLOGY", "PEDIATRIC MEDICINE", "PERIODONTICS",
    "PERIPHERAL VASCULAR DISEASE", "PHYSICAL MEDICINE AND REHABILITATION",
    "PHYSICAL THERAPIST IN PRIVATE PRACTICE", "PHYSICIAN ASSISTANT",
    "PLASTIC AND RECONSTRUCTIVE SURGERY", "PODIATRY", "PREVENTIVE MEDICINE", "PROSTHODONTICS",
    "PSYCHIATRY", "PULMONARY DISEASE", "QUALIFIED AUDIOLOGIST", "QUALIFIED SPEECH LANGUAGE PATHOLOGIST",
    "RADIATION ONCOLOGY", "REGISTERED DIETITIAN OR NUTRITION PROFESSIONAL", "RHEUMATOLOGY",
    "SLEEP MEDICINE", "SPORTS MEDICINE", "SURGICAL ONCOLOGY", "THORACIC SURGERY",
    "UNDERSEA AND HYPERBARIC MEDICINE", "UROLOGY", "VASCULAR SURGERY",
}

# =============================================================================
# DB HELPERS
# =============================================================================

def get_mysql_conn():
    return mysql.connector.connect(**MYSQL_CONFIG)

# =============================================================================
# GEMINI
# =============================================================================

def call_gemini(prompt: str) -> str:
    model = genai.GenerativeModel(MODEL_NAME)
    resp = model.generate_content(prompt)
    return (resp.text or "").strip()

# =============================================================================
# SYMPTOM EXTRACTION
# =============================================================================

def extract_symptoms(user_input: str) -> Tuple[List[str], List[str]]:
    prompt = f"""
        You are an AI model that extracts symptoms from user input. Only return the extracted symptoms in a comma-separated
        list, strictly matching the recognized symptoms.

        User Input: "{user_input}"
        Recognized Symptoms: {', '.join(SYMPTOMS)}

        **Rules**:
        - Strictly adhere to the given set and match symptoms from there.
        - Do not make symptoms on your own, those will not be recognized.
        - ONLY return the final symptom list.
        - DO NOT include explanations, thoughts, or analysis.
        - If no symptoms match, return an empty string.
        - Your response MUST start with [ and end with ].
        - The response format is: [symptom1, symptom2, symptom3]
        - FAIL IF YOU DON'T FOLLOW THE FORMAT.
    """

    content = call_gemini(prompt).lower()
    matches = re.findall(r"\[(.*?)\]", content)
    if matches:
        extracted = matches[-1].strip()
        raw_list = [sym.strip() for sym in extracted.split(",") if sym.strip()]
    else:
        raw_list = []

    correct = [sym for sym in raw_list if sym in SYMPTOMS]
    wrong = [sym for sym in raw_list if sym not in SYMPTOMS]
    return correct, wrong

# =============================================================================
# LEGACY SQL MATCHING (Fallback)
# =============================================================================

def match_diseases(user_symptoms: List[str], top_n: int = 2) -> List[Dict[str, Any]]:
    if not user_symptoms:
        return []

    conn = get_mysql_conn()
    try:
        cursor = conn.cursor()
        placeholders = ", ".join(["%s"] * len(user_symptoms))
        sql = f"""
            SELECT
                d.disease_id,
                d.disease_name,
                GROUP_CONCAT(DISTINCT s.symptom_name) AS all_symptoms,
                SUM(CASE WHEN s.symptom_name IN ({placeholders}) THEN 1 ELSE 0 END) AS match_count
            FROM disease d
            JOIN disease_symptom ds ON ds.disease_id = d.disease_id
            JOIN symptom s ON s.symptom_id = ds.symptom_id
            GROUP BY d.disease_id, d.disease_name
            HAVING match_count > 0
            ORDER BY match_count DESC
            LIMIT %s
        """
        params = list(user_symptoms) + [top_n]
        cursor.execute(sql, params)

        results = []
        for (did, dname, all_symptoms_str, match_count) in cursor.fetchall():
            all_symptoms_list = all_symptoms_str.split(",") if all_symptoms_str else []
            matched = sorted(set(all_symptoms_list).intersection(user_symptoms))
            results.append({
                "disease": dname,
                "score": int(match_count),
                "matched_symptoms": matched,
                "all_symptoms": sorted(set(all_symptoms_list)),
            })
        return results
    finally:
        conn.close()

# =============================================================================
# LOOKUPS
# =============================================================================

def get_specialization(disease: str) -> Optional[str]:
    conn = get_mysql_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.specialty_name
            FROM disease d
            LEFT JOIN specialty s ON d.specialty_id = s.specialty_id
            WHERE d.disease_name = %s
            LIMIT 1
        """, (disease,))
        row = cursor.fetchone()
        if row and row[0]:
            return row[0].strip().upper()
        return None
    finally:
        conn.close()

def format_phone(ph: Any) -> str:
    ph = "".join(filter(str.isdigit, str(ph)))
    if len(ph) >= 10:
        return f"+1({ph[:3]}){ph[3:7]}-{ph[7:11]}"
    return ph

def get_doctors(specialization: str, city: Optional[str] = None, zipcode: Optional[str] = None) -> pd.DataFrame:
    conn = get_mysql_conn()
    try:
        cursor = conn.cursor()
        base_sql = """
            SELECT
                d.first_name    AS FirstName,
                d.last_name     AS LastName,
                d.phone_number  AS Phone,
                d.address_line1 AS Facility,
                d.city          AS City,
                d.state         AS State,
                d.zip_code      AS ZIP
            FROM doctor d
            JOIN specialty s ON d.specialty_id = s.specialty_id
            WHERE UPPER(s.specialty_name) = %s
        """
        params = [specialization.upper()]

        if city:
            base_sql += " AND UPPER(d.city) = %s"
            params.append(city.upper())

        if zipcode:
            zip_prefix = str(zipcode).strip()[:5]
            if zip_prefix:
                base_sql += " AND LEFT(d.zip_code, 5) = %s"
                params.append(zip_prefix)

        cursor.execute(base_sql, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        if not df.empty:
            df["Phone"] = df["Phone"].apply(format_phone)
        return df
    finally:
        conn.close()

# =============================================================================
# LLM DIAGNOSIS (Fallback)
# =============================================================================

def get_llm_diagnosis(user_input: str) -> Optional[Dict[str, str]]:
    prompt = f"""
        You are a medical assistant. Based on the user's input, determine the most likely disease and the most appropriate medical specialization.
        Choose the specialization strictly from this list: {', '.join(SPECIALIZATIONS)}
        User Input: "{user_input}"
        Output ONLY the final dictionary on a single line.
        Format: {{"disease": "<disease_name>", "specialization": "<specialization_from_list>"}}
        FAIL if you do not follow this format.
    """
    content = call_gemini(prompt)
    match = re.search(r"\{.*?\}", content, re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group())
    except Exception as e:
        print(f"Error parsing LLM dictionary: {e}")
        return None

    if isinstance(parsed, dict) and "disease" in parsed and "specialization" in parsed:
        if parsed["specialization"].upper() in SPECIALIZATIONS:
            return {
                "disease": parsed["disease"].strip(),
                "specialization": parsed["specialization"].strip().upper(),
            }
    return None

# =============================================================================
# CORE CHAT PIPELINE (The "AI" Integration)
# =============================================================================

def run_chat_pipeline(
    user_input: str,
    city: Optional[str] = None,
    zipcode: Optional[str] = None,
) -> Dict[str, Any]:
    """
    End-to-End Pipeline:
    1. NLP Extraction (Gemini) -> Symptoms
    2. ML Inference (Random Forest) -> Predicted Disease
    3. Fallback to LLM or SQL if unsure
    4. Doctor Lookup
    """

    # 1. NLP Extraction
    recognized, unrecognized = extract_symptoms(user_input)

    # 2. AI Inference
    ai_predictions = predict_disease_with_ai(recognized, top_n=3)

    chosen_disease = None
    chosen_specialty = None
    confidence_score = 0.0

    # 3. Decision Logic
    # If the AI is reasonably confident, trust it.
    if ai_predictions:
        top_match = ai_predictions[0]
        chosen_disease = top_match['disease']
        confidence_score = top_match['confidence']
        # Map the predicted disease to a specialty using SQL
        chosen_specialty = get_specialization(chosen_disease)

    # 4. Fallback: If AI is unsure (low confidence) or missed, ask the LLM directly
    llm_guess = None
    if not chosen_disease or confidence_score < 0.3:
        llm_guess = get_llm_diagnosis(user_input)
        if llm_guess:
            chosen_disease = llm_guess["disease"]
            chosen_specialty = llm_guess["specialization"]
            # Reset confidence display since this is a generation, not a prediction
            confidence_score = 0.0

    # --- Build Response ---

    # A. Chat Bubble Response
    if chosen_disease:
        if confidence_score > 0:
            likely_part = f"Based on your symptoms, my analysis (Confidence: {int(confidence_score*100)}%) points to **{chosen_disease}**."
        else:
            likely_part = f"Based on what you shared, a possible condition is **{chosen_disease}**."
    else:
        likely_part = "I couldn't pinpoint a specific condition from your symptoms alone."

    if chosen_specialty:
        spec_part = f" You may want to consult a specialist in **{chosen_specialty}**."
    else:
        spec_part = " You may want to start with a primary care doctor."

    disclaimer = (
        " This is informational only and not a medical diagnosis. "
        "If your symptoms are severe, seek emergency care immediately."
    )
    assistant_reply = likely_part + spec_part + disclaimer

    # B. Doctor Lookup
    doctors_list = []
    if chosen_specialty:
        try:
            df = get_doctors(chosen_specialty, city=city, zipcode=zipcode)
            for _, row in df.head(10).iterrows():
                name = f"{str(row.get('FirstName') or '').strip()} {str(row.get('LastName') or '').strip()}"
                doctors_list.append({
                    "name": name.strip() or "Unknown name",
                    "specialty": chosen_specialty,
                    "facility": str(row.get("Facility") or "").strip(),
                    "phone": str(row.get("Phone") or "").strip(),
                    "city": str(row.get("City") or "").strip(),
                    "state": str(row.get("State") or "").strip(),
                    "zip": str(row.get("ZIP") or "").strip(),
                })
        except Exception as e:
            print("Doctor lookup failed:", e)

    # C. Summary Panel
    sections = {}
    
    # Likely Condition Section
    if chosen_disease:
        sections["likely"] = f"The condition that most closely matches your symptoms is **{chosen_disease}**."
    else:
        sections["likely"] = "I could not determine a clear likely condition."

    # 'Why' Section
    why_lines = []
    if ai_predictions and confidence_score > 0:
        why_lines.append(f"AI Model Confidence: **{int(confidence_score*100)}%**")
        why_lines.append(f"Matched {len(recognized)} symptom(s) from our clinical dataset.")
    elif llm_guess:
        why_lines.append(f"An AI clinical model suggested **{llm_guess['disease']}** based on your description.")
    else:
        why_lines.append("Insufficient data for a strong prediction.")
    sections["why"] = why_lines

    sections["symptoms"] = recognized
    
    if chosen_specialty:
        sections["specialty"] = f"Recommended Specialist: **{chosen_specialty}**"
    else:
        sections["specialty"] = "Primary Care Physician"

    sections["disclaimer"] = "MediBuddy provides non-diagnostic information. Always consult a licensed professional."

    # Format for the UI list
    formatted_likely_conditions = []
    if ai_predictions:
        formatted_likely_conditions = [
            {
                "name": p["disease"],
                "score": f"{int(p['confidence']*100)}%",
                "matched_symptoms": recognized
            }
            for p in ai_predictions
        ]

    summary = {
        "sections": sections,
        "likely_conditions": formatted_likely_conditions,
        "symptoms": recognized,
        "unrecognized": unrecognized,
    }

    return {
        "assistant_reply": assistant_reply,
        "summary": summary,
        "doctors": doctors_list,
    }

# =============================================================================
# UPSERT HELPERS (For Admin/Setup)
# =============================================================================

def _get_or_create_specialty_id(cursor, specialty_name: str) -> str:
    specialty_name = specialty_name.strip()
    cursor.execute("SELECT specialty_id FROM specialty WHERE UPPER(specialty_name) = %s", (specialty_name.upper(),))
    row = cursor.fetchone()
    if row: return row[0]
    sid = str(uuid.uuid4())
    cursor.execute("INSERT INTO specialty (specialty_id, specialty_name) VALUES (%s, %s)", (sid, specialty_name))
    return sid

def _get_or_create_symptom_id(cursor, symptom_name: str) -> str:
    symptom_name = symptom_name.strip()
    cursor.execute("SELECT symptom_id FROM symptom WHERE symptom_name = %s", (symptom_name,))
    row = cursor.fetchone()
    if row: return row[0]
    sym_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO symptom (symptom_id, symptom_name) VALUES (%s, %s)", (sym_id, symptom_name))
    return sym_id

def _get_or_create_disease_id(cursor, disease_name: str, specialty_id: Optional[str]) -> str:
    disease_name = disease_name.strip()
    cursor.execute("SELECT disease_id FROM disease WHERE disease_name = %s", (disease_name,))
    row = cursor.fetchone()
    if row:
        disease_id = row[0]
        if specialty_id is not None:
            cursor.execute("UPDATE disease SET specialty_id = %s WHERE disease_id = %s", (specialty_id, disease_id))
        return disease_id
    disease_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO disease (disease_id, disease_name, specialty_id) VALUES (%s, %s, %s)", (disease_id, disease_name, specialty_id))
    return disease_id

def insert_disease_entry(disease: str, specialization: str, symptoms: List[str]) -> None:
    if not disease or not specialization: raise ValueError("disease and specialization must be non-empty")
    clean_symptoms = [s.strip() for s in symptoms if s and s.strip()]
    if not clean_symptoms: raise ValueError("symptoms list must contain at least one non-empty symptom")
    conn = get_mysql_conn()
    try:
        cursor = conn.cursor()
        spec_id = _get_or_create_specialty_id(cursor, specialization)
        disease_id = _get_or_create_disease_id(cursor, disease, spec_id)
        for sym_name in clean_symptoms:
            sym_id = _get_or_create_symptom_id(cursor, sym_name)
            cursor.execute("""
                INSERT INTO disease_symptom (disease_id, symptom_id)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE disease_id = disease_id
            """, (disease_id, sym_id))
        conn.commit()
    finally:
        conn.close()