from flask import Blueprint, request, jsonify, session
import sqlite3
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
import os

# create blueprint
auth_bp = Blueprint("auth", __name__)

# database path
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "healix.db")


# database connection helper
def get_connection():
    return sqlite3.connect(DATABASE)


# ================= REGISTER =================

@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.json

    username = data.get("username")
    email = data.get("email")
    mobile = data.get("mobile")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "Required fields missing"}), 400

    password_hash = generate_password_hash(password)

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO users (username, email, mobile, password_hash)
            VALUES (?, ?, ?, ?)
        """, (username, email, mobile, password_hash))

        conn.commit()

    except sqlite3.IntegrityError:

        conn.close()
        return jsonify({"error": "Email already exists"}), 400

    conn.close()

    return jsonify({"message": "Registration successful"})


# ================= LOGIN =================

@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.json

    email = data.get("email")
    password = data.get("password")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, username, password_hash FROM users WHERE email=?",
        (email,)
    )

    user = cursor.fetchone()
    print("LOGIN USER ROW:", user)

    conn.close()

    if user and check_password_hash(user[2], password):

        session["user_id"] = user[0]
        session["username"] = user[1]

        return jsonify({
            "success": True,
            "username": user[1]
        })

    return jsonify({
        "success": False,
        "error": "Invalid credentials"
    }), 401


# ================= LOGOUT =================

@auth_bp.route("/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    })


# ================= CHECK SESSION =================

@auth_bp.route("/check-session", methods=["GET"])
def check_session():

    if "user_id" in session:

        return jsonify({
            "logged_in": True,
            "username": session.get("username")
        })

    return jsonify({
        "logged_in": False,
        "username": None
    })


# ================= FORGOT PASSWORD =================

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():

    data = request.json
    email = data.get("email")

    token = secrets.token_hex(16)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET reset_token=? WHERE email=?",
        (token, email)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Reset token generated (demo mode)",
        "reset_token": token
    })


# ================= RESET PASSWORD =================

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():

    data = request.json

    token = data.get("token")
    new_password = data.get("new_password")

    if not token or not new_password:
        return jsonify({
            "error": "Token and password required"
        }), 400

    password_hash = generate_password_hash(new_password)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET password_hash=?, reset_token=NULL
        WHERE reset_token=?
    """, (password_hash, token))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Password updated successfully"
    })