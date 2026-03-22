"""
models/user_model.py
────────────────────────────────────────────────────────────────
User database model using SQLite (zero config, works on Render).
In production swap to PostgreSQL by changing DATABASE_URL env var.

Tables:
  users              — core auth table
  student_profiles   — academic profile linked to user
  prediction_history — saved ML predictions per user
"""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.getenv("DATABASE_URL", os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "careerai.db"
))

def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # access columns by name
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_db()
    cur  = conn.cursor()

    # ── users ──────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            email         TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role          TEXT DEFAULT 'student',
            is_verified   INTEGER DEFAULT 0,
            is_active     INTEGER DEFAULT 1,
            avatar_initials TEXT,
            created_at    TEXT DEFAULT (datetime('now')),
            updated_at    TEXT DEFAULT (datetime('now')),
            last_login    TEXT
        )
    """)

    # ── student_profiles ───────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_profiles (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id             INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            age                 INTEGER,
            gender              TEXT,
            location            TEXT,
            education_level     TEXT,
            degree              TEXT,
            stream              TEXT,
            gpa                 REAL,
            math_score          REAL,
            english_score       REAL,
            science_score       REAL,
            social_score        REAL,
            aptitude_score      INTEGER,
            college_credits     INTEGER,
            parent_education    TEXT,
            income_category     TEXT,
            category            TEXT,
            region              TEXT,
            ethnicity           TEXT,
            skills_coding       INTEGER DEFAULT 0,
            skills_design       INTEGER DEFAULT 0,
            skills_communication INTEGER DEFAULT 0,
            skills_analysis     INTEGER DEFAULT 0,
            skills_leadership   INTEGER DEFAULT 0,
            personality_analytical REAL DEFAULT 5.0,
            personality_creative   REAL DEFAULT 5.0,
            personality_social     REAL DEFAULT 5.0,
            preferred_tech         REAL DEFAULT 5.0,
            preferred_business     REAL DEFAULT 5.0,
            preferred_creative     REAL DEFAULT 5.0,
            preferred_industries   TEXT DEFAULT '[]',
            personality_traits     TEXT DEFAULT '[]',
            profile_complete    INTEGER DEFAULT 0,
            updated_at          TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── prediction_history ─────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prediction_history (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER REFERENCES users(id) ON DELETE CASCADE,
            career_1     TEXT,
            prob_1       REAL,
            career_2     TEXT,
            prob_2       REAL,
            career_3     TEXT,
            prob_3       REAL,
            xai_factors  TEXT DEFAULT '[]',
            created_at   TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── saved_scholarships ─────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS saved_scholarships (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER REFERENCES users(id) ON DELETE CASCADE,
            scholarship_id TEXT NOT NULL,
            saved_at       TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, scholarship_id)
        )
    """)

    # ── refresh_tokens ─────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
            token      TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Tables initialized.")


# ── User CRUD ──────────────────────────────────────────────────────────────
class UserModel:

    @staticmethod
    def create(name: str, email: str, password_hash: str, role: str = "student") -> dict | None:
        conn = get_db()
        try:
            initials = "".join(w[0].upper() for w in name.split()[:2])
            cur = conn.execute(
                "INSERT INTO users (name,email,password_hash,role,avatar_initials) VALUES (?,?,?,?,?)",
                (name, email.lower(), password_hash, role, initials)
            )
            user_id = cur.lastrowid
            # Auto-create empty profile
            conn.execute(
                "INSERT INTO student_profiles (user_id) VALUES (?)", (user_id,)
            )
            conn.commit()
            return UserModel.get_by_id(user_id)
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    @staticmethod
    def get_by_email(email: str) -> dict | None:
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM users WHERE email=? AND is_active=1", (email.lower(),)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_by_id(user_id: int) -> dict | None:
        conn = get_db()
        row = conn.execute(
            "SELECT id,name,email,role,is_verified,avatar_initials,created_at,last_login "
            "FROM users WHERE id=?", (user_id,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update_last_login(user_id: int):
        conn = get_db()
        conn.execute(
            "UPDATE users SET last_login=datetime('now') WHERE id=?", (user_id,)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def email_exists(email: str) -> bool:
        conn = get_db()
        row = conn.execute(
            "SELECT id FROM users WHERE email=?", (email.lower(),)
        ).fetchone()
        conn.close()
        return row is not None


# ── Profile CRUD ───────────────────────────────────────────────────────────
class ProfileModel:

    @staticmethod
    def get(user_id: int) -> dict | None:
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM student_profiles WHERE user_id=?", (user_id,)
        ).fetchone()
        conn.close()
        if not row:
            return None
        d = dict(row)
        # Parse JSON fields
        for field in ["preferred_industries", "personality_traits"]:
            try:
                d[field] = json.loads(d[field] or "[]")
            except Exception:
                d[field] = []
        return d

    @staticmethod
    def upsert(user_id: int, data: dict) -> dict:
        conn = get_db()
        # JSON-encode list fields
        for field in ["preferred_industries", "personality_traits"]:
            if field in data and isinstance(data[field], list):
                data[field] = json.dumps(data[field])

        fields = [k for k in data if k != "user_id"]
        set_clause = ", ".join(f"{f}=?" for f in fields)
        values = [data[f] for f in fields] + [user_id]

        # Check profile completion
        required = ["gpa","aptitude_score","degree","education_level","region","gender"]
        is_complete = all(data.get(r) or ProfileModel.get(user_id) and
                         ProfileModel.get(user_id).get(r) for r in required)

        conn.execute(
            f"UPDATE student_profiles SET {set_clause}, "
            f"profile_complete={1 if is_complete else 0}, "
            f"updated_at=datetime('now') WHERE user_id=?",
            values
        )
        conn.commit()
        conn.close()
        return ProfileModel.get(user_id)

    @staticmethod
    def completion_pct(user_id: int) -> int:
        profile = ProfileModel.get(user_id)
        if not profile:
            return 0
        fields = ["gender","age","degree","education_level","region","gpa",
                  "aptitude_score","college_credits","parent_education",
                  "income_category","category"]
        filled = sum(1 for f in fields if profile.get(f))
        return int(filled / len(fields) * 100)


# ── Prediction History ─────────────────────────────────────────────────────
class PredictionModel:

    @staticmethod
    def save(user_id: int, predictions: list, xai_factors: list) -> dict:
        conn = get_db()
        p = predictions
        cur = conn.execute(
            "INSERT INTO prediction_history "
            "(user_id,career_1,prob_1,career_2,prob_2,career_3,prob_3,xai_factors) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (user_id,
             p[0]["career"] if len(p)>0 else None, p[0]["probability"] if len(p)>0 else None,
             p[1]["career"] if len(p)>1 else None, p[1]["probability"] if len(p)>1 else None,
             p[2]["career"] if len(p)>2 else None, p[2]["probability"] if len(p)>2 else None,
             json.dumps(xai_factors))
        )
        conn.commit()
        pred_id = cur.lastrowid
        conn.close()
        return {"id": pred_id, "saved": True}

    @staticmethod
    def get_history(user_id: int, limit: int = 10) -> list:
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM prediction_history WHERE user_id=? "
            "ORDER BY created_at DESC LIMIT ?", (user_id, limit)
        ).fetchall()
        conn.close()
        result = []
        for row in rows:
            d = dict(row)
            try:
                d["xai_factors"] = json.loads(d["xai_factors"] or "[]")
            except Exception:
                d["xai_factors"] = []
            result.append(d)
        return result
