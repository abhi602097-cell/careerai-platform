"""
routes/auth_routes.py
────────────────────────────────────────────────────────────────
All authentication + user profile API routes.

Public endpoints:
  POST /api/v1/auth/register       Register new student
  POST /api/v1/auth/login          Login + get tokens
  POST /api/v1/auth/refresh        Refresh access token
  POST /api/v1/auth/logout         Logout + revoke tokens

Protected endpoints (require JWT):
  GET  /api/v1/auth/me             Get current user info
  PUT  /api/v1/auth/profile        Update student profile
  GET  /api/v1/auth/profile        Get student profile
  GET  /api/v1/auth/history        Prediction history
  GET  /api/v1/auth/dashboard      Dashboard summary data
  POST /api/v1/auth/save-scholarship  Save a scholarship
  GET  /api/v1/auth/saved-scholarships  Get saved scholarships
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timezone

from services.auth_service import (
    hash_password, verify_password,
    generate_access_token, generate_refresh_token,
    refresh_access_token, revoke_refresh_token,
    validate_registration, validate_login,
)
from models.user_model import (
    UserModel, ProfileModel, PredictionModel, get_db
)
from middleware.auth_middleware import require_auth, require_role

auth = Blueprint("auth", __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────
def ok(data, message="Success", status=200):
    return jsonify({"status":"success","message":message,"data":data,
                    "timestamp": datetime.now(timezone.utc).isoformat()}), status

def err(message, status=400, code=None):
    body = {"status":"error","message":message,
            "timestamp": datetime.now(timezone.utc).isoformat()}
    if code: body["code"] = code
    return jsonify(body), status


# ── REGISTER ──────────────────────────────────────────────────────────────────
@auth.route("/register", methods=["POST"])
def register():
    """
    Register a new student account.
    Body: { name, email, password, role? }
    """
    data = request.get_json(silent=True) or {}

    # Validate
    errors = validate_registration(data)
    if errors:
        return err(" | ".join(errors), 422)

    email = data["email"].strip().lower()
    name  = data["name"].strip()

    # Check duplicate
    if UserModel.email_exists(email):
        return err("An account with this email already exists.", 409, "EMAIL_EXISTS")

    # Hash password + create user
    password_hash = hash_password(data["password"])
    role = data.get("role", "student")
    if role not in ("student", "counselor"):
        role = "student"

    user = UserModel.create(name, email, password_hash, role)
    if not user:
        return err("Registration failed. Please try again.", 500)

    # Generate tokens
    access_token  = generate_access_token(user["id"], user["email"], user["role"])
    refresh_token = generate_refresh_token(user["id"])

    return ok({
        "user":          user,
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "token_type":    "Bearer",
        "expires_in":    3600,
    }, "Account created successfully!", 201)


# ── LOGIN ─────────────────────────────────────────────────────────────────────
@auth.route("/login", methods=["POST"])
def login():
    """
    Login with email + password.
    Body: { email, password }
    """
    data   = request.get_json(silent=True) or {}
    errors = validate_login(data)
    if errors:
        return err(" | ".join(errors), 422)

    email = data["email"].strip().lower()
    user  = UserModel.get_by_email(email)

    # Generic error message (don't reveal if email exists)
    INVALID = "Invalid email or password."
    if not user:
        return err(INVALID, 401, "INVALID_CREDENTIALS")

    if not verify_password(data["password"], user["password_hash"]):
        return err(INVALID, 401, "INVALID_CREDENTIALS")

    if not user.get("is_active", 1):
        return err("Your account has been deactivated. Contact support.", 403)

    # Update last login
    UserModel.update_last_login(user["id"])

    # Get profile completion
    completion = ProfileModel.completion_pct(user["id"])

    # Generate tokens
    access_token  = generate_access_token(user["id"], user["email"], user["role"])
    refresh_token = generate_refresh_token(user["id"])

    # Safe user object (no password_hash)
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}

    return ok({
        "user":               safe_user,
        "access_token":       access_token,
        "refresh_token":      refresh_token,
        "token_type":         "Bearer",
        "expires_in":         3600,
        "profile_completion": completion,
    }, f"Welcome back, {user['name'].split()[0]}!")


# ── REFRESH TOKEN ─────────────────────────────────────────────────────────────
@auth.route("/refresh", methods=["POST"])
def refresh():
    """
    Exchange a refresh token for new access + refresh tokens.
    Body: { refresh_token }
    """
    data          = request.get_json(silent=True) or {}
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return err("Refresh token is required.", 400)

    result = refresh_access_token(refresh_token)
    if not result:
        return err("Invalid or expired refresh token. Please log in again.", 401, "REFRESH_FAILED")

    return ok({
        "access_token":  result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type":    "Bearer",
        "expires_in":    3600,
        "user":          result["user"],
    }, "Token refreshed successfully.")


# ── LOGOUT ────────────────────────────────────────────────────────────────────
@auth.route("/logout", methods=["POST"])
def logout():
    """
    Logout — revoke refresh token.
    Body: { refresh_token }
    """
    data = request.get_json(silent=True) or {}
    refresh_token = data.get("refresh_token")
    if refresh_token:
        revoke_refresh_token(refresh_token)
    return ok({}, "Logged out successfully.")


# ── GET CURRENT USER ──────────────────────────────────────────────────────────
@auth.route("/me", methods=["GET"])
@require_auth
def get_me():
    """Get current authenticated user info."""
    user = UserModel.get_by_id(g.user_id)
    if not user:
        return err("User not found.", 404)

    completion = ProfileModel.completion_pct(g.user_id)
    user["profile_completion"] = completion
    return ok(user, "User info retrieved.")


# ── GET PROFILE ───────────────────────────────────────────────────────────────
@auth.route("/profile", methods=["GET"])
@require_auth
def get_profile():
    """Get student academic profile."""
    profile = ProfileModel.get(g.user_id)
    if not profile:
        return err("Profile not found.", 404)

    completion = ProfileModel.completion_pct(g.user_id)
    profile["completion_pct"] = completion
    return ok(profile, "Profile retrieved.")


# ── UPDATE PROFILE ────────────────────────────────────────────────────────────
@auth.route("/profile", methods=["PUT"])
@require_auth
def update_profile():
    """
    Update student academic profile.
    Accepts partial updates — only provided fields are updated.
    """
    data = request.get_json(silent=True) or {}

    # Whitelist allowed fields
    ALLOWED = {
        "age","gender","location","education_level","degree","stream",
        "gpa","math_score","english_score","science_score","social_score",
        "aptitude_score","college_credits","parent_education",
        "income_category","category","region","ethnicity",
        "skills_coding","skills_design","skills_communication",
        "skills_analysis","skills_leadership",
        "personality_analytical","personality_creative","personality_social",
        "preferred_tech","preferred_business","preferred_creative",
        "preferred_industries","personality_traits",
    }
    update_data = {k: v for k, v in data.items() if k in ALLOWED}

    if not update_data:
        return err("No valid fields provided for update.", 400)

    # Validate GPA range
    if "gpa" in update_data:
        try:
            gpa = float(update_data["gpa"])
            if not (0 <= gpa <= 4.0):
                return err("GPA must be between 0.0 and 4.0", 422)
        except (TypeError, ValueError):
            return err("GPA must be a number.", 422)

    profile    = ProfileModel.upsert(g.user_id, update_data)
    completion = ProfileModel.completion_pct(g.user_id)
    profile["completion_pct"] = completion

    return ok(profile, "Profile updated successfully.")


# ── PREDICTION HISTORY ────────────────────────────────────────────────────────
@auth.route("/history", methods=["GET"])
@require_auth
def prediction_history():
    """Get user's ML prediction history."""
    limit   = min(int(request.args.get("limit", 10)), 50)
    history = PredictionModel.get_history(g.user_id, limit)
    return ok({
        "history": history,
        "total":   len(history),
    }, f"{len(history)} predictions found.")


# ── SAVE PREDICTION ───────────────────────────────────────────────────────────
@auth.route("/save-prediction", methods=["POST"])
@require_auth
def save_prediction():
    """
    Save a prediction result to user's history.
    Body: { predictions: [...], explanation: {...} }
    """
    data        = request.get_json(silent=True) or {}
    predictions = data.get("predictions", [])
    explanation = data.get("explanation", {})
    xai_factors = explanation.get("factors", [])

    if not predictions:
        return err("No predictions provided.", 400)

    result = PredictionModel.save(g.user_id, predictions, xai_factors)
    return ok(result, "Prediction saved to your history.")


# ── DASHBOARD SUMMARY ─────────────────────────────────────────────────────────
@auth.route("/dashboard", methods=["GET"])
@require_auth
def dashboard():
    """
    Return dashboard summary data for the logged-in student.
    Includes: user info, profile completion, latest prediction, stats.
    """
    user       = UserModel.get_by_id(g.user_id)
    profile    = ProfileModel.get(g.user_id)
    history    = PredictionModel.get_history(g.user_id, 1)
    completion = ProfileModel.completion_pct(g.user_id)

    latest_prediction = history[0] if history else None

    return ok({
        "user":               {k: v for k, v in user.items() if k != "password_hash"},
        "profile_completion": completion,
        "profile":            profile,
        "latest_prediction":  latest_prediction,
        "total_predictions":  len(PredictionModel.get_history(g.user_id, 100)),
        "stats": {
            "profile_complete": completion == 100,
            "has_predictions":  latest_prediction is not None,
            "member_since":     user.get("created_at", ""),
        }
    }, "Dashboard data loaded.")


# ── SAVE SCHOLARSHIP ──────────────────────────────────────────────────────────
@auth.route("/save-scholarship", methods=["POST"])
@require_auth
def save_scholarship():
    """Save a scholarship to user's bookmarks."""
    data           = request.get_json(silent=True) or {}
    scholarship_id = data.get("scholarship_id")

    if not scholarship_id:
        return err("scholarship_id is required.", 400)

    conn = get_db()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO saved_scholarships (user_id, scholarship_id) VALUES (?,?)",
            (g.user_id, scholarship_id)
        )
        conn.commit()
    finally:
        conn.close()

    return ok({"saved": True, "scholarship_id": scholarship_id}, "Scholarship saved.")


# ── GET SAVED SCHOLARSHIPS ────────────────────────────────────────────────────
@auth.route("/saved-scholarships", methods=["GET"])
@require_auth
def saved_scholarships():
    """Get user's saved scholarships."""
    conn = get_db()
    rows = conn.execute(
        "SELECT scholarship_id, saved_at FROM saved_scholarships WHERE user_id=? ORDER BY saved_at DESC",
        (g.user_id,)
    ).fetchall()
    conn.close()

    return ok({
        "saved": [dict(r) for r in rows],
        "total": len(rows),
    }, f"{len(rows)} saved scholarships.")
