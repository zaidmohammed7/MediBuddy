from __future__ import annotations

import traceback
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, request

from chatbot import (
    extract_symptoms,
    get_doctors,
    get_llm_diagnosis,
    get_specialization,
    match_diseases,
)

app = Flask(__name__)


# ---------------------------------------------------------------------
# Core chatbot pipeline
# ---------------------------------------------------------------------


def run_chat_pipeline(
    user_input: str,
    city: Optional[str] = None,
    zipcode: Optional[str] = None,
) -> Dict[str, Any]:
    """
    One end-to-end turn of the MediBuddy chatbot:
    - extract symptoms
    - match diseases from DB
    - get DB specialty
    - combine with LLM guess
    - fetch doctors if we have a specialty
    """

    # 1) Extract symptoms
    recognized, unrecognized = extract_symptoms(user_input)

    # 2) Match diseases from DB
    disease_matches = match_diseases(recognized, top_n=3)

    # 3) LLM diagnosis suggestion
    llm_guess = get_llm_diagnosis(user_input)

    chosen_disease: Optional[str] = None
    chosen_specialty: Optional[str] = None

    # Prefer DB match first
    if disease_matches:
        top = disease_matches[0]
        chosen_disease = top["disease"]
        db_spec = get_specialization(chosen_disease)
        chosen_specialty = db_spec

    # Mix in LLM view
    if llm_guess:
        llm_dis = llm_guess["disease"]
        llm_spec = llm_guess["specialization"]
        if chosen_disease is None:
            chosen_disease = llm_dis
        if chosen_specialty is None:
            chosen_specialty = llm_spec

    # ------------- Build assistant reply (chat bubble) -------------

    if chosen_disease:
        likely_part = (
            f"Based on what you shared, a possible condition is **{chosen_disease}**."
        )
    else:
        likely_part = (
            "I couldn’t pinpoint a specific condition from your symptoms alone."
        )

    if chosen_specialty:
        spec_part = (
            f" A good type of clinician to talk to would be a specialist in **{chosen_specialty}**."
        )
    else:
        spec_part = (
            " You may want to start with a primary care or family medicine doctor."
        )

    disclaimer = (
        " This is informational only and not a medical diagnosis. "
        "If your symptoms are severe (e.g., chest pain, difficulty breathing, confusion, heavy bleeding), "
        "seek emergency care immediately."
    )

    assistant_reply = likely_part + spec_part + disclaimer

    # ------------- Doctor lookup -------------

    doctors: List[Dict[str, Any]] = []
    if chosen_specialty:
        try:
            df = get_doctors(chosen_specialty, city=city, zipcode=zipcode)
            for _, row in df.head(10).iterrows():
                name = (
                    f"{str(row.get('FirstName') or '').strip()} "
                    f"{str(row.get('LastName') or '').strip()}"
                ).strip() or "Unknown name"

                doctors.append(
                    {
                        "name": name,
                        "specialty": chosen_specialty,
                        "facility": str(row.get("Facility") or "").strip(),
                        "phone": str(row.get("Phone") or "").strip(),
                        "city": str(row.get("City") or "").strip(),
                        "state": str(row.get("State") or "").strip(),
                        "zip": str(row.get("ZIP") or "").strip(),
                    }
                )
        except Exception as e:
            # Log doctor lookup issues to server logs; don't break the chat.
            print("Doctor lookup failed:", e)

    # ------------- Structured summary for the right panel -------------

    sections: Dict[str, Any] = {}

    # 1. Most likely condition
    if chosen_disease:
        sections["likely"] = (
            f"The condition that most closely matches your symptoms is **{chosen_disease}**."
        )
    else:
        sections["likely"] = (
            "I could not determine a clear likely condition from your symptoms."
        )

    # 2. Why this may fit (DB + LLM reasoning)
    why_lines: List[str] = []

    if disease_matches:
        top_match = disease_matches[0]
        why_lines.append(
            f"Your symptoms matched {top_match['score']} symptom(s) commonly associated with "
            f"**{top_match['disease']}** in medical datasets."
        )

    if llm_guess:
        why_lines.append(
            f"An AI clinical model also suggested **{llm_guess['disease']}**, "
            f"which is typically handled by {llm_guess['specialization']}."
        )

    if not why_lines:
        why_lines.append(
            "There was not enough structured or AI-supported evidence to identify a specific condition."
        )

    sections["why"] = why_lines

    # 3. Recognized symptoms
    sections["symptoms"] = recognized

    # 4. Suggested specialty
    if chosen_specialty:
        sections["specialty"] = (
            f"Based on the suspected condition, you may want to consult a specialist in **{chosen_specialty}**."
        )
    else:
        sections["specialty"] = (
            "Since I could not determine a specific specialty, you may want to start with a primary care physician."
        )

    # 5. Safety / disclaimer
    sections["disclaimer"] = (
        "MediBuddy provides non-diagnostic information. "
        "Always consult a licensed professional for medical advice. "
        "If you experience severe symptoms such as chest pain, difficulty breathing, confusion, or heavy bleeding, "
        "seek emergency medical care immediately."
    )

    likely_conditions: List[Dict[str, Any]] = []
    if disease_matches:
        likely_conditions = [
            {
                "name": m["disease"],
                "score": m["score"],
                "matched_symptoms": m["matched_symptoms"],
            }
            for m in disease_matches
        ]

    summary = {
        "sections": sections,
        "likely_conditions": likely_conditions,
        "symptoms": recognized,
        "unrecognized": unrecognized,
    }

    return {
        "assistant_reply": assistant_reply,
        "summary": summary,
        "doctors": doctors,
    }


# ---------------------------------------------------------------------
# Page routes (dummy HTML screens)
# ---------------------------------------------------------------------


@app.route("/")
def index() -> str:
    """Dashboard / homepage."""
    return render_template("index.html", active_page="dashboard")


@app.route("/login")
def login() -> str:
    return render_template("login.html")


@app.route("/signup")
def signup() -> str:
    return render_template("signup.html")


@app.route("/prescriptions")
def prescriptions() -> str:
    return render_template("prescriptions.html", active_page="prescriptions")


@app.route("/reminders")
def reminders() -> str:
    return render_template("reminders.html", active_page="reminders")


@app.route("/settings")
def settings() -> str:
    return render_template("settings.html", active_page="settings")


@app.route("/chatbot", methods=["GET", "POST"])
def chatbot() -> Any:
    # GET -> render page
    if request.method == "GET":
        return render_template("chatbot.html", active_page="chatbot")

    # POST -> AJAX from chatbot UI
    data = request.get_json(force=True) or {}
    user_input = (data.get("message") or "").strip()
    city = (data.get("city") or "").strip() or None
    zipcode = (data.get("zipcode") or "").strip() or None

    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    try:
        result = run_chat_pipeline(user_input, city=city, zipcode=zipcode)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "details": str(e),
                }
            ),
            500,
        )


if __name__ == "__main__":
    app.run(debug=True)
