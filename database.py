import sqlite3
import os

# Force database inside backend folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "healix.db")


def get_connection():
    return sqlite3.connect(DATABASE)


def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    # ---------------- USERS TABLE ----------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            mobile TEXT,
            password_hash TEXT NOT NULL,
            reset_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------- PREDICTIONS TABLE ----------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symptoms TEXT NOT NULL,
            predicted_disease TEXT NOT NULL,
            confidence REAL NOT NULL,
            risk_level TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ---------------- HEALTH TRACKER TABLE ----------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_tracker (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        date TEXT,

        height REAL,
        weight REAL,

        age INTEGER,
        gender TEXT,

        bmi REAL,
        bmr REAL,

        steps INTEGER,

        sleep_hours REAL,

        water_intake REAL,

        calories_intake REAL,

        calories_needed REAL,

        health_score INTEGER

        )
    """)

    conn.commit()
    conn.close()


def save_prediction(user_id, symptoms, disease, confidence, risk_level):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO predictions
        (user_id, symptoms, predicted_disease, confidence, risk_level)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, symptoms, disease, confidence, risk_level))

    conn.commit()
    conn.close()


def delete_prediction(prediction_id, user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM predictions
        WHERE id=? AND user_id=?
    """, (prediction_id, user_id))

    conn.commit()
    conn.close()