from __future__ import annotations

import traceback
from typing import Any, Dict, List, Optional
import os
import uuid
import datetime
import calendar

from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import mysql.connector

# --- UPDATED IMPORT ---
# We now import the full pipeline from chatbot.py instead of individual functions
from chatbot import run_chat_pipeline

app = Flask(__name__)

load_dotenv("config/api.env")

app.secret_key = os.getenv("FLAS_SECRET_KEY", "dev-secret")


def get_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="[PASSWORD]",
            database="[DATABASE_NAME]",
        )
        return conn
    except Exception as e:
        print("DB CONNECT ERROR:", repr(e))
        raise


def get_current_user_id() -> str:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM user LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        raise RuntimeError("No users in table")
    
    return row[0]


# ---------------------------------------------------------------------
# Page routes
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


@app.route("/prescriptions", methods=["GET"])
def prescriptions() -> str:
    """List prescriptions for the demo user + load available drugs."""
    conn = get_db()

    current_user_id = get_current_user_id()

    # prescriptions
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT p.rx_id,
               p.frequency,
               p.qty_on_hand,
               p.refills,
               p.rx_text,
               d.name AS drug_name
        FROM prescription p
        JOIN drug d ON p.drug_id = d.drug_id
        WHERE p.user_id = %s
        """,
        (current_user_id,),
    )
    prescriptions = cur.fetchall()
    cur.close()

    # drugs for dropdown + management
    cur2 = conn.cursor(dictionary=True)
    cur2.execute("SELECT drug_id, name, rxnorm_code FROM drug ORDER BY name")
    drugs = cur2.fetchall()
    cur2.close()

    conn.close()

    # To update UI with the prescription count
    prescription_count = len(prescriptions)

    return render_template(
        "prescriptions.html",
        active_page="prescriptions",
        prescriptions=prescriptions,
        drugs=drugs,
        prescription_count=prescription_count,
    )


@app.route("/drugs/create", methods=["POST"])
def create_drug():
    """CREATE: add a new drug to the drug table."""
    name = request.form["drug_name"].strip()
    rxnorm_code = request.form.get("rxnorm_code", "").strip() or None

    if not name:
        return redirect(url_for("prescriptions"))

    drug_id = str(uuid.uuid4())

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO drug (drug_id, rxnorm_code, name)
        VALUES (%s, %s, %s)
        """,
        (drug_id, rxnorm_code, name),
    )
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("prescriptions"))


@app.route("/drugs/<drug_id>/delete", methods=["POST"])
def delete_drug(drug_id: str):
    """DELETE: remove a drug."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM drug WHERE drug_id = %s", (drug_id,))
        conn.commit()
    except Exception as e:
        print("DRUG DELETE ERROR:", repr(e))
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("prescriptions"))


@app.route("/prescriptions/create", methods=["POST"])
def create_prescription():
    drug_id = request.form["drug_id"]
    frequency = request.form["frequency"]
    qty_on_hand = int(request.form["qty_on_hand"])
    refills = int(request.form["refills"])
    rx_text = request.form.get("rx_text", "")

    rx_id = str(uuid.uuid4())

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    current_user_id = get_current_user_id()

    try:
        conn.start_transaction(isolation_level="READ COMMITTED")

        # First advanced query check
        cur.execute ("""
            SELECT u.user_id, d.drug_id
            FROM user AS u
            JOIN drug AS d ON d.drug_id = %s
            WHERE u.user_id = %s
            """, (drug_id, current_user_id),)
        rows = cur.fetchone()
        if rows is None:
            raise ValueError("User/drug doesn't exist")
        
        cur.execute("""
            INSERT INTO prescription
                    (rx_id, user_id, drug_id, frequency, qty_on_hand, refills, rx_text)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (rx_id, current_user_id, drug_id, frequency, qty_on_hand, refills, rx_text),)
    
        # Second advanced query
        cur.execute ("""
            SELECT user_id, COUNT(*) AS total_prescriptions
            FROM prescription
            WHERE user_id = %s
            GROUP BY user_id
            """, (current_user_id,),)
        count_row = cur.fetchone()

        if count_row is None:
            raise RuntimeError("Failed to count prescriptions")

        # Updates the UI 
        total_prescriptions = count_row["total_prescriptions"]
        session["prescription_count"] = total_prescriptions

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("create_prescription error:", e)
    
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("prescriptions"))


@app.route("/prescriptions/<rx_id>/update", methods=["POST"])
def update_prescription(rx_id: str):
    """UPDATE: edit an existing prescription."""
    frequency = request.form["frequency"]
    qty_on_hand = int(request.form["qty_on_hand"])
    refills = int(request.form["refills"])
    rx_text = request.form.get("rx_text", "")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE prescription
        SET frequency = %s,
            qty_on_hand = %s,
            refills = %s,
            rx_text = %s
        WHERE rx_id = %s
        """,
        (frequency, qty_on_hand, refills, rx_text, rx_id),
    )
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("prescriptions"))


@app.route("/prescriptions/<rx_id>/delete", methods=["POST"])
def delete_prescription(rx_id: str):
    """DELETE: remove a prescription."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM prescription WHERE rx_id = %s", (rx_id,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("prescriptions"))


@app.route("/reminders", methods=["GET"])
def reminders() -> str:
    """List reminders with a monthly calendar view."""
    conn = get_db()

    current_user_id = get_current_user_id()

    # Get reminders joined with drug info
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT r.reminder_id, r.remind_time, r.override_frequency,
               d.name AS drug_name, p.frequency AS default_frequency
        FROM reminder r
        JOIN prescription p ON r.rx_id = p.rx_id
        JOIN drug d ON p.drug_id = d.drug_id
        WHERE r.user_id = %s
        ORDER BY r.remind_time ASC
        """,
        (current_user_id,),
    )
    reminders_data = cur.fetchall()
    cur.close()

    # Get user prescriptions for the 'add' dropdown
    cur2 = conn.cursor(dictionary=True)
    cur2.execute(
        """
        SELECT p.rx_id, d.name AS drug_name 
        FROM prescription p
        JOIN drug d ON p.drug_id = d.drug_id
        WHERE p.user_id = %s
        ORDER BY d.name
        """,
        (current_user_id,),
    )
    user_prescriptions = cur2.fetchall()
    cur2.close()
    conn.close()

    # Calendar Setup
    today = datetime.date.today()
    try:
        month = int(request.args.get("month", today.month))
        year = int(request.args.get("year", today.year))
    except (ValueError, TypeError):
        month, year = today.month, today.year

    # Navigation links
    if month == 1:
        prev_m, prev_y = 12, year - 1
    else:
        prev_m, prev_y = month - 1, year

    if month == 12:
        next_m, next_y = 1, year + 1
    else:
        next_m, next_y = month + 1, year

    # Map reminders for O(1) lookup during grid construction
    reminders_map = {}
    for r in reminders_data:
        if r["remind_time"]:
            d_str = r["remind_time"].strftime("%Y-%m-%d")
            reminders_map.setdefault(d_str, []).append(r)

    # Build the calendar grid
    start_weekday = datetime.date(year, month, 1).weekday()
    start_col = (start_weekday + 1) % 7
    _, days_in_month = calendar.monthrange(year, month)

    calendar_weeks = []
    current_week = [None] * start_col 

    for day in range(1, days_in_month + 1):
        d_str = datetime.date(year, month, day).strftime("%Y-%m-%d")
        
        current_week.append({
            "day": day,
            "date_str": d_str,
            "reminders": reminders_map.get(d_str, [])
        })

        if len(current_week) == 7:
            calendar_weeks.append(current_week)
            current_week = []

    if current_week:
        while len(current_week) < 7:
            current_week.append(None)
        calendar_weeks.append(current_week)

    return render_template(
        "reminders.html",
        active_page="reminders",
        reminders=reminders_data,
        prescriptions=user_prescriptions,
        calendar_weeks=calendar_weeks,
        current_month_name=datetime.date(year, month, 1).strftime("%B %Y"),
        prev_month=prev_m,
        prev_year=prev_y,
        next_month=next_m,
        next_year=next_y,
        current_month=month,
        current_year=year,
    )


@app.route("/reminders/create", methods=["POST"])
def create_reminder():
    rx_id = request.form["rx_id"]
    date_str = request.form.get("remind_date")
    time_str = request.form.get("remind_time")

    current_user_id = get_current_user_id()

    if not date_str:
        date_str = datetime.date.today().strftime("%Y-%m-%d")
    
    full_ts = f"{date_str} {time_str}:00"
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO reminder (reminder_id, user_id, rx_id, remind_time)
        VALUES (%s, %s, %s, %s)
        """,
        (str(uuid.uuid4()), current_user_id, rx_id, full_ts),
    )
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("reminders"))


@app.route("/reminders/<reminder_id>/delete", methods=["POST"])
def delete_reminder(reminder_id: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM reminder WHERE reminder_id = %s", (reminder_id,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("reminders"))


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
        # Calls the function in chatbot.py which now includes the AI pipeline
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