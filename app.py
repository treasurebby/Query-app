# app.py
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import sqlite3
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

# Database setup
DB_NAME = "queries.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()

@app.route("/")
def index():
    # Load past queries
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM queries ORDER BY id DESC")
        history = cursor.fetchall()
    return render_template("index.html", history=history)

@app.route("/ask", methods=["POST"])
def ask():
    user_question = request.json.get("question", "").strip()
    
    if not user_question:
        return jsonify({"error": "Please type a question!"})

    try:
        # Get answer from Gemini
        response = model.generate_content(user_question)
        ai_answer = response.text

        # Save to database
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute(
                "INSERT INTO queries (question, answer, timestamp) VALUES (?, ?, ?)",
                (user_question, ai_answer, timestamp)
            )
            conn.commit()

        return jsonify({"answer": ai_answer})

    except Exception as e:
        return jsonify({"error": f"AI Error: {str(e)}"})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)