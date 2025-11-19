# app.py - PERFECT FOR LOCAL + RENDER
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import sqlite3
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
app = Flask(__name__)

# Gemini setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

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

# Always init DB on startup (for Render)
init_db()

@app.route("/")
def index():
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM queries ORDER BY id DESC")
        history = cursor.fetchall()
    return render_template("index.html", history=history)

@app.route("/ask", methods=["POST"])
def ask():
    user_question = request.json.get("question", "").strip()
    if not user_question:
        return jsonify({"error": "Empty question!"})

    try:
        response = model.generate_content(user_question)
        ai_answer = response.text

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.execute(
                "INSERT INTO queries (question, answer, timestamp) VALUES (?, ?, ?)",
                (user_question, ai_answer, timestamp)
            )
            conn.commit()
            new_id = cursor.lastrowid

        return jsonify({"answer": ai_answer, "id": new_id})
    except Exception as e:
        return jsonify({"error": f"AI Error: {str(e)}"})

@app.route("/edit", methods=["POST"])
def edit():
    data = request.json
    id = data["id"]
    new_question = data["question"].strip()
    if not new_question:
        return jsonify({"error": "Question cannot be empty"})

    try:
        response = model.generate_content(new_question)
        new_answer = response.text

        with sqlite3.connect(DB_NAME) as conn:
            conn.execute(
                "UPDATE queries SET question=?, answer=?, timestamp=? WHERE id=?",
                (new_question, new_answer, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), id)
            )
            conn.commit()
        return jsonify({"success": True, "new_answer": new_answer})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/delete/<int:id>", methods=["DELETE"])
def delete(id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM queries WHERE id=?", (id,))
        conn.commit()
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)