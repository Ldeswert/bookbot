"""Flask backend for the Spanish language learning app.

Serves the SPA and provides JSON APIs for flashcards, quizzes, matching,
AI conversations, and stats.
"""

import os
from flask import Flask, request, jsonify, render_template
import db

app = Flask(__name__, static_folder="static", template_folder="templates")
db.init_db()


@app.route("/")
def index():
    return render_template("index.html")


# ---- Flashcards ----

@app.route("/api/flashcards/due")
def get_due_flashcards():
    cards = db.get_due_flashcards()
    return jsonify(cards)


@app.route("/api/flashcards/review", methods=["POST"])
def review_flashcard():
    data = request.json
    word_id = data["word_id"]
    quality = data["quality"]  # 0-5
    db.record_flashcard_review(word_id, quality)
    return jsonify({"ok": True})


# ---- Quiz ----

@app.route("/api/quiz")
def get_quiz():
    questions = db.generate_quiz(10)
    return jsonify(questions)


@app.route("/api/quiz/result", methods=["POST"])
def save_quiz_result():
    data = request.json
    db.record_quiz_result(data["score"], data["total"])
    return jsonify({"ok": True})


# ---- Matching ----

@app.route("/api/matching")
def get_matching():
    words = db.get_matching_words(6)
    return jsonify(words)


# ---- Chat ----

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return jsonify({
            "error": "OpenAI API key not configured. Set your OPENAI_API_KEY to use AI conversations."
        }), 400

    history = db.get_chat_history(limit=10)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a friendly Spanish language tutor. The learner is an English "
                "speaker studying Spanish. Respond primarily in simple Spanish. After each "
                "response, include an English translation in parentheses for any new or "
                "unfamiliar words. Keep sentences short and simple. Gently correct mistakes. "
                "Be encouraging and conversational."
            ),
        }
    ]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    db.add_chat_message("user", message)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=300,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        db.add_chat_message("assistant", reply)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": f"AI request failed: {str(e)}"}), 500


@app.route("/api/chat/history")
def get_chat_history():
    return jsonify(db.get_chat_history())


@app.route("/api/chat/clear", methods=["POST"])
def clear_chat():
    db.clear_chat()
    return jsonify({"ok": True})


# ---- Stats ----

@app.route("/api/stats")
def get_stats():
    return jsonify(db.get_stats())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
