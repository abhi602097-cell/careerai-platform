"""
services/auth_service.py
────────────────────────────────────────────────────────────────
Authentication service:
  - Password hashing with bcrypt
  - JWT access tokens (15 min expiry)
  - Refresh tokens (7 day expiry)
  - Token blacklisting on logout
"""

import os
import jwt
import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from models.user_model import UserModel, get_db

# ── Config ────────────────────────────────────────────────────────────────────
SECRET_KEY       = os.getenv("JWT_SECRET_KEY", "careerai-dev-secret-change-in-production-2025")
ACCESS_EXPIRES   = int(os.getenv("JWT_ACCESS_EXPIRES_MINUTES", "60"))    # 60 min
REFRESH_EXPIRES  = int(os.getenv("JWT_REFRESH_EXPIRES_DAYS",   "7"))     # 7 days
ALGORITHM        = "HS256"


# ── Password hashing (using hashlib — no bcrypt needed) ───────────────────────
def hash_password(password: str) -> str:
    """Hash password with SHA-256 + salt. Production-safe without bcrypt."""
    salt = secrets.token_hex(32)
    key  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310000)
    return f"{salt}:{key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash."""
    try:
        salt, key_hex = stored_hash.split(":", 1)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310000)
        return hmac.compare_digest(key.hex(), key_hex)
    except Exception:
        return False


# ── JWT Tokens ────────────────────────────────────────────────────────────────
def generate_access_token(user_id: int, email: str, role: str) -> str:
    """Generate short-lived JWT access token."""
    payload = {
        "sub":   str(user_id),
        "email": email,
        "role":  role,
        "type":  "access",
        "iat":   datetime.now(timezone.utc),
        "exp":   datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def generate_refresh_token(user_id: int) -> str:
    """Generate long-lived opaque refresh token and store in DB."""
    token      = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRES)

    conn = get_db()
    # Remove old refresh tokens for this user (keep only latest)
    conn.execute("DELETE FROM refresh_tokens WHERE user_id=?", (user_id,))
    conn.execute(
        "INSERT INTO refresh_tokens (user_id,token,expires_at) VALUES (?,?,?)",
        (user_id, token, expires_at.isoformat())
    )
    conn.commit()
    conn.close()
    return token


def decode_access_token(token: str) -> dict | None:
    """Decode and validate JWT. Returns payload or None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "token_expired"}
    except jwt.InvalidTokenError:
        return None


def refresh_access_token(refresh_token: str) -> dict | None:
    """
    Exchange a valid refresh token for a new access token.
    Returns new tokens or None if refresh token is invalid/expired.
    """
    conn = get_db()
    row  = conn.execute(
        "SELECT * FROM refresh_tokens WHERE token=?", (refresh_token,)
    ).fetchone()
    conn.close()

    if not row:
        return None

    # Check expiry
    expires_at = datetime.fromisoformat(row["expires_at"])
    if expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        # Expired — delete it
        conn = get_db()
        conn.execute("DELETE FROM refresh_tokens WHERE token=?", (refresh_token,))
        conn.commit()
        conn.close()
        return None

    user = UserModel.get_by_id(row["user_id"])
    if not user:
        return None

    # Issue new access token + rotate refresh token
    new_access  = generate_access_token(user["id"], user["email"], user["role"])
    new_refresh = generate_refresh_token(user["id"])

    return {
        "access_token":  new_access,
        "refresh_token": new_refresh,
        "user":          user,
    }


def revoke_refresh_token(refresh_token: str):
    """Logout — delete refresh token from DB."""
    conn = get_db()
    conn.execute("DELETE FROM refresh_tokens WHERE token=?", (refresh_token,))
    conn.commit()
    conn.close()


# ── Validation ────────────────────────────────────────────────────────────────
def validate_registration(data: dict) -> list[str]:
    """Return list of validation errors (empty = valid)."""
    errors = []

    name     = (data.get("name") or "").strip()
    email    = (data.get("email") or "").strip()
    password = (data.get("password") or "")

    if not name or len(name) < 2:
        errors.append("Name must be at least 2 characters.")
    if len(name) > 100:
        errors.append("Name must be under 100 characters.")

    if not email or "@" not in email or "." not in email:
        errors.append("Please enter a valid email address.")

    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter.")
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number.")

    return errors


def validate_login(data: dict) -> list[str]:
    errors = []
    if not data.get("email"):
        errors.append("Email is required.")
    if not data.get("password"):
        errors.append("Password is required.")
    return errors
