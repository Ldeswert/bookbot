"""Database module for the Spanish language learning app.

Uses SQLite (stdlib) for persistence. Seeds vocabulary on first run.
Implements SM-2 spaced repetition for flashcards.
"""

import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = os.environ.get("DB_PATH", "language_app.db")

SEED_WORDS = [
    # Greetings
    ("hola", "hello", "Greetings"),
    ("adiós", "goodbye", "Greetings"),
    ("buenos días", "good morning", "Greetings"),
    ("buenas tardes", "good afternoon", "Greetings"),
    ("buenas noches", "good night", "Greetings"),
    ("por favor", "please", "Greetings"),
    ("gracias", "thank you", "Greetings"),
    ("de nada", "you're welcome", "Greetings"),
    ("perdón", "excuse me", "Greetings"),
    ("sí", "yes", "Greetings"),
    ("no", "no", "Greetings"),
    # Numbers
    ("uno", "one", "Numbers"),
    ("dos", "two", "Numbers"),
    ("tres", "three", "Numbers"),
    ("cuatro", "four", "Numbers"),
    ("cinco", "five", "Numbers"),
    ("seis", "six", "Numbers"),
    ("siete", "seven", "Numbers"),
    ("ocho", "eight", "Numbers"),
    ("nueve", "nine", "Numbers"),
    ("diez", "ten", "Numbers"),
    # Food
    ("pan", "bread", "Food"),
    ("agua", "water", "Food"),
    ("leche", "milk", "Food"),
    ("café", "coffee", "Food"),
    ("manzana", "apple", "Food"),
    ("pollo", "chicken", "Food"),
    ("arroz", "rice", "Food"),
    ("queso", "cheese", "Food"),
    ("huevo", "egg", "Food"),
    ("pescado", "fish", "Food"),
    # Family
    ("madre", "mother", "Family"),
    ("padre", "father", "Family"),
    ("hermano", "brother", "Family"),
    ("hermana", "sister", "Family"),
    ("hijo", "son", "Family"),
    ("hija", "daughter", "Family"),
    ("abuela", "grandmother", "Family"),
    ("abuelo", "grandfather", "Family"),
    ("tío", "uncle", "Family"),
    ("tía", "aunt", "Family"),
    # Colors
    ("rojo", "red", "Colors"),
    ("azul", "blue", "Colors"),
    ("verde", "green", "Colors"),
    ("amarillo", "yellow", "Colors"),
    ("negro", "black", "Colors"),
    ("blanco", "white", "Colors"),
    ("naranja", "orange", "Colors"),
    ("morado", "purple", "Colors"),
    ("rosa", "pink", "Colors"),
    ("gris", "gray", "Colors"),
    # Animals
    ("perro", "dog", "Animals"),
    ("gato", "cat", "Animals"),
    ("caballo", "horse", "Animals"),
    ("pájaro", "bird", "Animals"),
    ("pez", "fish", "Animals"),
    ("león", "lion", "Animals"),
    ("ratón", "mouse", "Animals"),
    ("vaca", "cow", "Animals"),
    ("cerdo", "pig", "Animals"),
    ("conejo", "rabbit", "Animals"),
    # Travel
    ("tren", "train", "Travel"),
    ("coche", "car", "Travel"),
    ("avión", "airplane", "Travel"),
    ("hotel", "hotel", "Travel"),
    ("mapa", "map", "Travel"),
    ("billete", "ticket", "Travel"),
    ("maleta", "suitcase", "Travel"),
    ("pasaporte", "passport", "Travel"),
    ("estación", "station", "Travel"),
    ("ciudad", "city", "Travel"),
    # Verbs
    ("comer", "to eat", "Verbs"),
    ("beber", "to drink", "Verbs"),
    ("hablar", "to speak", "Verbs"),
    ("aprender", "to learn", "Verbs"),
    ("vivir", "to live", "Verbs"),
    ("trabajar", "to work", "Verbs"),
    ("estudiar", "to study", "Verbs"),
    ("caminar", "to walk", "Verbs"),
    ("leer", "to read", "Verbs"),
    ("escribir", "to write", "Verbs"),
    # Common
    ("casa", "house", "Common"),
    ("escuela", "school", "Common"),
    ("trabajo", "work", "Common"),
    ("amigo", "friend", "Common"),
    ("tiempo", "time", "Common"),
    ("día", "day", "Common"),
    ("noche", "night", "Common"),
    ("hombre", "man", "Common"),
    ("mujer", "woman", "Common"),
    ("niño", "child", "Common"),
]

JOURNEY_STEPS = [
    ("Greetings", "Essential greetings & polite expressions"),
    ("Numbers", "Count from 1 to 10"),
    ("Food", "Common foods & drinks"),
    ("Family", "Family members"),
    ("Colors", "Basic colors"),
    ("Animals", "Common animals"),
    ("Travel", "Travel & transportation"),
    ("Verbs", "Essential action verbs"),
    ("Common", "Everyday vocabulary"),
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spanish TEXT NOT NULL,
            english TEXT NOT NULL,
            category TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS flashcard_state (
            word_id INTEGER PRIMARY KEY,
            repetitions INTEGER DEFAULT 0,
            ease_factor REAL DEFAULT 2.5,
            interval INTEGER DEFAULT 0,
            next_review TEXT,
            last_reviewed TEXT,
            FOREIGN KEY (word_id) REFERENCES words(id)
        );

        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            completed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    if c.execute("SELECT COUNT(*) FROM words").fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO words (spanish, english, category) VALUES (?, ?, ?)",
            SEED_WORDS,
        )
    conn.commit()
    conn.close()


# ---- Flashcards (SM-2 spaced repetition) ----

def get_due_flashcards():
    conn = get_db()
    rows = conn.execute(
        """
        SELECT w.id, w.spanish, w.english, w.category,
               fs.repetitions, fs.ease_factor, fs.interval
        FROM words w
        LEFT JOIN flashcard_state fs ON w.id = fs.word_id
        WHERE fs.next_review IS NULL OR fs.next_review <= datetime('now')
        ORDER BY COALESCE(fs.next_review, '0000-00-00')
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def sm2_update(quality, repetitions, ease_factor, interval):
    """SM-2 algorithm. quality: 0-5 (0-2 = wrong, 3-5 = correct)."""
    if quality >= 3:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * ease_factor)
        repetitions += 1
    else:
        repetitions = 0
        interval = 1

    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if ease_factor < 1.3:
        ease_factor = 1.3

    next_review = (datetime.now() + timedelta(days=interval)).isoformat()
    return repetitions, ease_factor, interval, next_review


def record_flashcard_review(word_id, quality):
    conn = get_db()
    row = conn.execute(
        "SELECT repetitions, ease_factor, interval FROM flashcard_state WHERE word_id = ?",
        (word_id,),
    ).fetchone()
    if row:
        repetitions, ease_factor, interval = row["repetitions"], row["ease_factor"], row["interval"]
    else:
        repetitions, ease_factor, interval = 0, 2.5, 0

    repetitions, ease_factor, interval, next_review = sm2_update(
        quality, repetitions, ease_factor, interval
    )

    conn.execute(
        """
        INSERT INTO flashcard_state (word_id, repetitions, ease_factor, interval, next_review, last_reviewed)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(word_id) DO UPDATE SET
            repetitions = excluded.repetitions,
            ease_factor = excluded.ease_factor,
            interval = excluded.interval,
            next_review = excluded.next_review,
            last_reviewed = excluded.last_reviewed
        """,
        (word_id, repetitions, ease_factor, interval, next_review, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


# ---- Quiz ----

def generate_quiz(num_questions=10):
    conn = get_db()
    all_words = conn.execute("SELECT * FROM words").fetchall()
    conn.close()
    all_words = [dict(w) for w in all_words]
    if len(all_words) < 4:
        return []

    sample = random.sample(all_words, min(num_questions, len(all_words)))
    questions = []
    for word in sample:
        show_spanish = random.choice([True, False])
        if show_spanish:
            prompt = word["spanish"]
            answer = word["english"]
            wrong_pool = [w["english"] for w in all_words if w["id"] != word["id"]]
        else:
            prompt = word["english"]
            answer = word["spanish"]
            wrong_pool = [w["spanish"] for w in all_words if w["id"] != word["id"]]

        wrong = random.sample(wrong_pool, 3)
        options = wrong + [answer]
        random.shuffle(options)
        questions.append({
            "word_id": word["id"],
            "prompt": prompt,
            "answer": answer,
            "options": options,
            "show_spanish": show_spanish,
        })
    return questions


def record_quiz_result(score, total):
    conn = get_db()
    conn.execute(
        "INSERT INTO quiz_results (score, total, completed_at) VALUES (?, ?, ?)",
        (score, total, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_quiz_history(limit=10):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM quiz_results ORDER BY completed_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---- Matching ----

def get_matching_words(num=6):
    conn = get_db()
    rows = conn.execute("SELECT * FROM words ORDER BY RANDOM() LIMIT ?", (num,)).fetchall()
    conn.close()
    words = [dict(r) for r in rows]
    spanish = [{"id": w["id"], "text": w["spanish"]} for w in words]
    english = [{"id": w["id"], "text": w["english"]} for w in words]
    random.shuffle(english)
    return {"spanish": spanish, "english": english}


# ---- Chat ----

def get_chat_history(limit=30):
    conn = get_db()
    rows = conn.execute(
        "SELECT role, content FROM chat_messages ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return list(reversed([dict(r) for r in rows]))


def add_chat_message(role, content):
    conn = get_db()
    conn.execute(
        "INSERT INTO chat_messages (role, content, created_at) VALUES (?, ?, ?)",
        (role, content, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def clear_chat():
    conn = get_db()
    conn.execute("DELETE FROM chat_messages")
    conn.commit()
    conn.close()


# ---- Stats ----

def get_stats():
    conn = get_db()
    total_words = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    due_count = conn.execute(
        """
        SELECT COUNT(*) FROM words w
        LEFT JOIN flashcard_state fs ON w.id = fs.word_id
        WHERE fs.next_review IS NULL OR fs.next_review <= datetime('now')
        """
    ).fetchone()[0]
    learned = conn.execute(
        "SELECT COUNT(*) FROM flashcard_state WHERE repetitions >= 3"
    ).fetchone()[0]
    quiz_results = conn.execute(
        "SELECT score, total, completed_at FROM quiz_results ORDER BY completed_at DESC LIMIT 5"
    ).fetchall()
    chat_count = conn.execute("SELECT COUNT(*) FROM chat_messages").fetchone()[0]
    conn.close()
    return {
        "total_words": total_words,
        "due_count": due_count,
        "learned": learned,
        "quiz_history": [dict(r) for r in quiz_results],
        "chat_count": chat_count,
    }


# ---- Journey ----

def get_journey():
    conn = get_db()
    steps = []
    for i, (category, description) in enumerate(JOURNEY_STEPS):
        total = conn.execute(
            "SELECT COUNT(*) FROM words WHERE category = ?", (category,)
        ).fetchone()[0]
        learned = conn.execute(
            """SELECT COUNT(*) FROM flashcard_state fs
               JOIN words w ON w.id = fs.word_id
               WHERE w.category = ? AND fs.repetitions >= 3""",
            (category,),
        ).fetchone()[0]
        due = conn.execute(
            """SELECT COUNT(*) FROM words w
               LEFT JOIN flashcard_state fs ON w.id = fs.word_id
               WHERE w.category = ? AND (fs.next_review IS NULL OR fs.next_review <= datetime('now'))""",
            (category,),
        ).fetchone()[0]
        steps.append({
            "step": i + 1,
            "category": category,
            "description": description,
            "total": total,
            "learned": learned,
            "due": due,
        })
    conn.close()
    return steps
