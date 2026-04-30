from flask import Flask, request, jsonify,send_from_directory,render_template, session, redirect
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "some-random-secret-key-123"  # Set secret key here
CORS(app, supports_credentials=True)  # Add supports_credentials

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.before_request
def create_tables():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            company_name TEXT
        )
    """)
    db.commit()
    db.close()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.json

    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")
    company_name = data.get("company_name")

    if not full_name or not email or not password or not role:
        return jsonify({"error": "Missing fields"}), 400

    password_hash = generate_password_hash(password)

    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (full_name, email, password_hash, role, company_name) VALUES (?, ?, ?, ?, ?)",
            (full_name, email, password_hash, role, company_name)
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 409
    finally:
        db.close()

    return jsonify({"message": "Signup successful"}), 201

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")
    
    # Get user data from database to ensure we have the latest
    user_id = session.get("user_id")
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()
    
    if not user:
        session.clear()
        return redirect("/")
    
    # Render the appropriate dashboard based on role
    role = user["role"]
    full_name = user["full_name"]
    
    if role == "learner":
        return render_template("learner.html", full_name=full_name)
    elif role == "expert":
        return render_template("expert.html", full_name=full_name)
    elif role == "company":
        return render_template("company.html", full_name=full_name)
    elif role == "innovator":
        return render_template("innovator.html", full_name=full_name)
    else:
        return render_template("learner.html", full_name=full_name)

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing credentials"}), 400

    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    ).fetchone()
    db.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid login"}), 401

    # Set session data
    session["user_id"] = user["id"]
    session["full_name"] = user["full_name"]
    session["role"] = user["role"]
    session["email"] = user["email"]

    return jsonify({
        "message": "Login successful",
        "role": user["role"],
        "full_name": user["full_name"]
    }), 200

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)