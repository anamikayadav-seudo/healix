from flask import Flask, request, jsonify, session
from flask_cors import CORS
import pickle
import pandas as pd
import os
import sqlite3
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path
from database import init_db, save_prediction
import requests
from datetime import datetime
import io
from flask import send_file
from routes.auth_routes import auth_bp
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.platypus import Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle

# ---------------- CREATE APP ----------------
app = Flask(__name__)
app.register_blueprint(auth_bp)
app.secret_key = "healix_secret_key_2026"
CORS(
    app,
    supports_credentials=True,
    origins=["http://localhost:5500"]
)
app.config.update(
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=False
)

# ---------------- LOAD ENV ----------------
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# ---------------- LOAD MODEL ----------------
with open("model/disease_model.pkl", "rb") as f:
    model = pickle.load(f)

# ---------------- LOAD DATA ----------------
data = pd.read_csv("Training.csv")
data = data.loc[:, ~data.columns.str.contains("^Unnamed")]
symptom_columns = data.columns[:-1]

# ---------------- GROQ ----------------
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def generate_ai_text(prompt):

    try:

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",

            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },

            json={
                "model": "meta-llama/llama-3-8b-instruct",

                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        )

        return response.json()["choices"][0]["message"]["content"]

    except Exception as e:

        print("OpenRouter error:", e)

        return "AI suggestions unavailable."
# ---------------- HOME ----------------
# ================= SPECIALIST MAP =================

SPECIALIST_MAP = {

    "malaria": "Infectious Disease Specialist",
    "migraine": "Neurologist",
    "diabetes": "Endocrinologist",
    "hypertension": "Cardiologist",
    "asthma": "Pulmonologist",
    "jaundice": "Hepatologist",
    "uti": "Urologist",
    "skin allergy": "Dermatologist",
    "arthritis": "Orthopedic",
    "depression": "Psychiatrist"

}
@app.route("/")
def home():
    return jsonify({"message": "Healix.AI Backend Running Successfully 🚀"})


# ---------------- GET SYMPTOMS ----------------
@app.route("/symptoms", methods=["GET"])
def get_symptoms():
    return jsonify({"symptoms": list(symptom_columns)})


# ================= AUTH =================

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    mobile = data.get("mobile")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "Required fields missing"}), 400

    password_hash = generate_password_hash(password)

    conn = sqlite3.connect("healix.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (username, email, mobile, password_hash)
            VALUES (?, ?, ?, ?)
        """, (username, email, mobile, password_hash))
        conn.commit()
    except:
        conn.close()
        return jsonify({"error": "Email already exists"}), 400

    conn.close()
    return jsonify({"message": "Registration successful"})


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    conn = sqlite3.connect("healix.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, password_hash FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[1], password):
        session["user_id"] = user[0]
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"error": "Invalid credentials"}), 401


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logged out"})


@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json
    email = data.get("email")
    token = secrets.token_hex(16)

    conn = sqlite3.connect("healix.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET reset_token=? WHERE email=?", (token, email))
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Reset token generated (demo mode)",
        "reset_token": token
    })


@app.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.json
    token = data.get("token")
    new_password = data.get("new_password")

    password_hash = generate_password_hash(new_password)

    conn = sqlite3.connect("healix.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET password_hash=?, reset_token=NULL
        WHERE reset_token=?
    """, (password_hash, token))
    conn.commit()
    conn.close()

    return jsonify({"message": "Password updated"})

@app.route("/check-session", methods=["GET"])
def check_session():
    if "user_id" in session:
        return jsonify({"logged_in": True})
    else:
        return jsonify({"logged_in": False})
# ================= PREDICT =================

@app.route("/predict", methods=["POST"])
def predict():

    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]

    request_data = request.json
    selected_symptoms = request_data.get("symptoms")

    if not selected_symptoms:
        return jsonify({"error": "No symptoms provided"}), 400

    input_vector = [
        1 if symptom in selected_symptoms else 0
        for symptom in symptom_columns
    ]

    prediction = model.predict([input_vector])[0]
    probability = model.predict_proba([input_vector])[0]

    confidence = float(max(probability) * 100)

    # Top 3
    classes = model.classes_
    top_indices = probability.argsort()[-3:][::-1]

    top_predictions = [
        {
            "disease": classes[i],
            "probability": float(probability[i] * 100)
        }
        for i in top_indices
    ]

    # Risk Level
    if confidence > 80:
        risk_level = "HIGH"
    elif confidence > 50:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    # AI Explanation
    prompt = f"""
    Predicted disease: {prediction}
    Confidence: {confidence:.2f}%

    Explain simply:
    - What it is
    - Symptoms
    - Prevention
    - When to see doctor

    Add disclaimer.
    """

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        explanation = response.choices[0].message.content
    except Exception as e:
        explanation = f"AI unavailable: {str(e)}"

    # Save to DB
    save_prediction(
        user_id=user_id,
        symptoms=", ".join(selected_symptoms),
        disease=prediction,
        confidence=confidence,
        risk_level=risk_level
    )

    return jsonify({
        "disease": prediction,
        "confidence": confidence,
        "risk_level": risk_level,
        "top_predictions": top_predictions,
        "explanation": explanation
    })


# ================= HISTORY =================

@app.route("/history", methods=["GET"])
def get_history():

    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]

    conn = sqlite3.connect("healix.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, symptoms, predicted_disease, confidence, risk_level, created_at
        FROM predictions
        WHERE user_id=?
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    history = []
    for row in rows:
        history.append({
            "id": row[0],
            "symptoms": row[1],
            "disease": row[2],
            "confidence": row[3],
            "risk_level": row[4],
            "date": row[5]
    })

    return jsonify(history)

@app.route("/delete-history/<int:prediction_id>", methods=["DELETE"])
def delete_history(prediction_id):

    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]

    conn = sqlite3.connect("healix.db")
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM predictions
        WHERE id=? AND user_id=?
    """, (prediction_id, user_id))

    conn.commit()
    conn.close()

    return jsonify({"message": "Deleted successfully"})
# ---------------- INIT ----------------
from datetime import datetime
init_db()

@app.route("/health-track", methods=["POST"])
def health_track():

    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]

    data = request.json


    height = float(data.get("height"))

    weight = float(data.get("weight"))

    age = int(data.get("age", 25))

    gender = data.get("gender", "female")


    steps = int(data.get("steps"))

    sleep = float(data.get("sleep_hours"))

    water = float(data.get("water_intake"))

    calories_intake = float(data.get("calories_intake"))


    height_m = height / 100

    bmi = weight / (height_m ** 2)


    if bmi < 18.5:

        bmi_status = "Underweight"
        bmi_color = "orange"

    elif bmi <= 24.9:

        bmi_status = "Normal"
        bmi_color = "green"

    elif bmi <= 29.9:

        bmi_status = "Overweight"
        bmi_color = "orange"

    else:

        bmi_status = "Obese"
        bmi_color = "red"


    gender_constant = 5 if gender.lower() == "male" else -161

    bmr = 10 * weight + 6.25 * height - 5 * age + gender_constant

    calories_needed = bmr * 1.55

    bmr_explanation = "Calories required daily for basic body functions."


    score = 0


    if 18.5 <= bmi <= 24.9:
        score += 20
    elif 17 <= bmi <= 29:
        score += 10


    if steps >= 8000:
        score += 20
    elif steps >= 5000:
        score += 10


    if 7 <= sleep <= 9:
        score += 20
    elif 6 <= sleep <= 10:
        score += 10


    if 2 <= water <= 3:
        score += 20
    elif 1.5 <= water <= 3.5:
        score += 10


    if abs(calories_intake - calories_needed) < 200:
        score += 20
    elif abs(calories_intake - calories_needed) < 400:
        score += 10


    if score >= 80:

        health_status = "Excellent"
        health_color = "green"

    elif score >= 50:

        health_status = "Moderate"
        health_color = "orange"

    else:

        health_status = "Needs Improvement"
        health_color = "red"


    alerts = []


    if bmi >= 30:
        alerts.append("High BMI detected")

    if sleep < 5:
        alerts.append("Sleep duration is too low")

    if water < 1.5:
        alerts.append("Low hydration level")

    if steps < 3000:
        alerts.append("Very low physical activity")


    # OpenRouter suggestions

    suggestion_prompt = f"""
    Provide exactly 3 short bullet-point wellness suggestions.
    Each suggestion must be 1 line only.

    BMI: {bmi}
    Steps: {steps}
    Sleep: {sleep}
    Water Intake: {water}
    Calories Intake: {calories_intake}
    Calories Needed: {calories_needed}
    """

    ai_suggestions = generate_ai_text(suggestion_prompt)


    summary_prompt = f"""
    Write exactly 2 short motivational wellness sentences.
    Keep tone supportive and friendly.

    BMI: {bmi}
    Steps: {steps}
    Sleep: {sleep}
    Water: {water}
    Health Score: {score}
    """

    ai_summary = generate_ai_text(summary_prompt)



    # ---------- DATABASE SAVE ----------

    today = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect("healix.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO health_tracker
        (user_id, date, height, weight, age, gender,
         bmi, bmr, steps, sleep_hours,
         water_intake, calories_intake,
         calories_needed, health_score)

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        user_id,
        today,
        height,
        weight,
        age,
        gender,
        bmi,
        bmr,
        steps,
        sleep,
        water,
        calories_intake,
        calories_needed,
        score
    ))

    conn.commit()
    conn.close()


    # ---------- FINAL RESPONSE ----------

    return jsonify({

        "bmi": round(bmi, 2),
        "bmi_status": bmi_status,
        "bmi_color": bmi_color,

        "bmr": round(bmr, 2),
        "bmr_explanation": bmr_explanation,

        "calories_needed": round(calories_needed, 2),

        "health_score": score,
        "health_status": health_status,
        "health_color": health_color,

        "alerts": alerts,

        "ai_suggestions": ai_suggestions,
        "ai_summary": ai_summary
    })


    # ================= SPECIALIST FINDER =================

@app.route("/find-specialist", methods=["POST"])
def find_specialist():

    data = request.json

    disease = data.get("disease", "").lower()
    location = data.get("location")

    if not disease or not location:

        return jsonify({
            "error": "Disease and location required"
        }), 400


    # ---------- STEP 1: FIND SPECIALIST ----------

    specialist = SPECIALIST_MAP.get(disease)


    # fallback to AI if disease not mapped

    if not specialist:

        prompt = f"""
Which medical specialist treats this disease?

Disease: {disease}

Answer ONLY with specialist name.
Example: Cardiologist
"""

        try:

            specialist = generate_ai_text(prompt).strip()

        except:

            specialist = "General Physician"


    # ---------- STEP 2: FIND LOCATION COORDINATES ----------

    geo_url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json"

    geo_response = requests.get(
        geo_url,
        headers={"User-Agent": "HealixAI"}
    ).json()


    if not geo_response:

        return jsonify({

            "recommended_specialist": specialist,
            "hospitals": []

        })


    lat = geo_response[0]["lat"]
    lon = geo_response[0]["lon"]


    # ---------- STEP 3: FIND NEARBY HOSPITALS ----------

    hospital_query = f"""
    [out:json];
    node["amenity"="hospital"](around:5000,{lat},{lon});
    out;
    """


    hospital_response = requests.post(

        "https://overpass-api.de/api/interpreter",

        data=hospital_query,

        headers={"User-Agent": "HealixAI"}

    ).json()


    hospitals = []


    for hospital in hospital_response.get("elements", [])[:6]:

        hospitals.append({

            "name": hospital["tags"].get("name", "Hospital"),

            "latitude": hospital["lat"],
            "longitude": hospital["lon"],

            "address": location

        })


    # ---------- FINAL RESPONSE ----------

    return jsonify({

        "disease": disease,

        "recommended_specialist": specialist,

        "location": location,

        "hospitals": hospitals

    })

@app.route("/download-report")
def download_report():

    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]

    conn = sqlite3.connect("healix.db")
    cursor = conn.cursor()


    # ================= USER DATA =================

    cursor.execute("""
        SELECT username, email, mobile
        FROM users
        WHERE id=?
    """, (user_id,))

    user = cursor.fetchone()


    # ================= PREDICTION =================

    cursor.execute("""
        SELECT symptoms, predicted_disease,
               confidence, risk_level
        FROM predictions
        WHERE user_id=?
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,))

    prediction = cursor.fetchone()


    # ================= HEALTH TRACKER =================

    cursor.execute("""
        SELECT age, gender, bmi, bmr,
               steps, sleep_hours,
               water_intake,
               calories_needed,
               health_score
        FROM health_tracker
        WHERE user_id=?
        ORDER BY date DESC
        LIMIT 1
    """, (user_id,))

    health = cursor.fetchone()

    conn.close()


    if not user or not prediction or not health:
        return jsonify({
            "error": "Not enough report data available"
        })


    # ================= SPECIALIST =================

    disease = prediction[1].lower()

    specialist = SPECIALIST_MAP.get(
        disease,
        "General Physician"
    )


    # ================= PDF BUILD =================

    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle
    )

    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle
    )

    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib import colors
    from flask import send_file
    import io
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(

        buffer,

        rightMargin=50,
        leftMargin=50,
        topMargin=40,
        bottomMargin=40

    )


    styles = getSampleStyleSheet()

    elements = []
    
   
    # ================= TITLE =================
    title_style = ParagraphStyle(
       name="title",
       fontSize=24,
       alignment=TA_CENTER,
       textColor=colors.HexColor("#2c3e50")
    )
    
    subtitle_style = ParagraphStyle(
        name="subtitle",
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    section_style = ParagraphStyle(
        name="section",
        fontSize=16,
        textColor=colors.HexColor("#0077b6")
    )
    # ================= LOGO =================
    logo_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "frontend",
        "assets",
        "logo.png"
    )

    logo = None  # IMPORTANT: always define first

    if os.path.exists(logo_path):
        from reportlab.platypus import Image

        logo = Image(
            logo_path,
            width=120,
            height=50
        )
    #============= HEADER =================

    if logo:
  
        header_table = Table([
            [
                logo,
                Paragraph(
                    "HEALIX.AI HEALTH REPORT",
                    title_style
                )
            ]  
        ])

    else: 

        header_table = Table([
            [
                "",
                Paragraph(
                    "HEALIX.AI HEALTH REPORT",
                    title_style
                )
            ]  
        ])


    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE")
    ]))

    elements.append(header_table)

    elements.append(
        Paragraph(
            "AI Assisted Preventive Health Summary",
            subtitle_style
        )
    )

    elements.append(Spacer(1, 20))
    # ================= PREDICTION =================
    # ================= PATIENT DETAILS =================

    elements.append(
       Paragraph("Patient Details", section_style)
    )

    user_table = Table([

        ["Name", user[0]],
        ["Email", user[1]],
        ["Mobile", user[2]],
        ["Age", health[0]],
        ["Gender", health[1]]
 
    ])

    user_table.setStyle(TableStyle([

        ("GRID",(0,0),(-1,-1),1,colors.grey),
        ("BACKGROUND",(0,0),(1,0),colors.HexColor("#e3f2fd"))

    ]))

    elements.append(user_table)

    elements.append(Spacer(1, 20))
# ================= DISEASE PREDICTION =================

    elements.append(
        Paragraph("Disease Prediction", section_style)
    )
    risk_color = colors.green

    if prediction[3] == "MODERATE":
        risk_color = colors.orange

    elif prediction[3] == "HIGH":
        risk_color = colors.red


    prediction_table = Table([

        ["Symptoms", prediction[0]],

        ["Predicted Disease",
         prediction[1]],

        ["Confidence",
         f"{prediction[2]:.2f}%"],

        ["Risk Level",
         prediction[3]]

    ])


    prediction_table.setStyle(TableStyle([

        ("GRID",(0,0),(-1,-1),1,
         colors.grey),

        ("TEXTCOLOR",(1,3),(1,3),
         risk_color)

    ]))


    elements.append(prediction_table)

    elements.append(Spacer(1, 20))


    # ================= HEALTH METRICS =================

    elements.append(
        Paragraph("Health Metrics", section_style)
    )


    metrics_table = Table([

        ["BMI",
         round(health[2],2)],

        ["BMR",
         round(health[3],2)],

        ["Steps",
         health[4]],

        ["Sleep Hours",
         health[5]],

        ["Water Intake",
         health[6]],

        ["Calories Needed",
         round(health[7],2)],

        ["Health Score",
         health[8]]

    ])


    metrics_table.setStyle(TableStyle([

        ("GRID",(0,0),(-1,-1),1,
         colors.grey)

    ]))


    elements.append(metrics_table)

    elements.append(Spacer(1, 20))


    # ================= SPECIALIST =================

    elements.append(
        Paragraph("Recommended Specialist",
                  section_style)
    )


    elements.append(
        Paragraph(
            specialist,
            styles["Normal"]
        )
    )


    elements.append(Spacer(1, 20))

    elements.append(Spacer(1,20))

    elements.append(

        Paragraph(

            "Generated by Healix.AI Digital Health Assistant",

            styles["Italic"]

        )

    )
    # ================= DISCLAIMER =================

    disclaimer_style = ParagraphStyle(

        name="footer",

        fontSize=9,

        alignment=TA_CENTER,

        textColor=colors.grey

    )


    elements.append(

        Paragraph(

            "⚠ This report is AI-generated and intended for educational use only. "
            "Please consult a qualified medical professional for diagnosis.",

            disclaimer_style

        )

    )


    doc.build(elements)

    buffer.seek(0)


    return send_file(

        buffer,

        as_attachment=True,

        download_name="Healix_Report.pdf",

        mimetype="application/pdf"

    )
  
if __name__ == "__main__":
    app.run(debug=True)