"""
routes/admin_routes.py
────────────────────────────────────────────────────────────────
Admin API routes — all protected by @require_auth + @require_role("admin")

Endpoints:
  GET  /api/v1/admin/stats              Platform overview stats
  GET  /api/v1/admin/users              All users (paginated)
  GET  /api/v1/admin/users/<id>         Single user + profile + history
  PUT  /api/v1/admin/users/<id>         Update user (role, status)
  DELETE /api/v1/admin/users/<id>       Deactivate user
  GET  /api/v1/admin/predictions        All predictions + analytics
  GET  /api/v1/admin/careers            Manage career knowledge
  POST /api/v1/admin/careers            Add new career
  PUT  /api/v1/admin/careers/<name>     Update career
  GET  /api/v1/admin/scholarships       Manage scholarships
  POST /api/v1/admin/scholarships       Add new scholarship
  PUT  /api/v1/admin/scholarships/<id>  Update scholarship
  DELETE /api/v1/admin/scholarships/<id> Deactivate scholarship
  GET  /api/v1/admin/analytics          Detailed analytics data
  GET  /api/v1/admin/logs               Recent activity log
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timezone, timedelta
from models.user_model import get_db, UserModel, ProfileModel, PredictionModel
from middleware.auth_middleware import require_auth, require_role
from config import CAREER_KNOWLEDGE, SCHOLARSHIPS

admin = Blueprint("admin", __name__)

# ── Helpers ───────────────────────────────────────────────────────────────────
def ok(data, message="Success", status=200):
    return jsonify({"status":"success","message":message,"data":data,
                    "timestamp":datetime.now(timezone.utc).isoformat()}), status

def err(message, status=400):
    return jsonify({"status":"error","message":message,
                    "timestamp":datetime.now(timezone.utc).isoformat()}), status

def admin_only(f):
    """Shortcut decorator: require_auth + require_role("admin")."""
    from functools import wraps
    @require_auth
    @require_role("admin")
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper


# ── PLATFORM STATS ────────────────────────────────────────────────────────────
@admin.route("/stats", methods=["GET"])
@require_auth
@require_role("admin")
def platform_stats():
    """Overview stats for the admin dashboard header cards."""
    conn = get_db()

    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    active_users = conn.execute("SELECT COUNT(*) FROM users WHERE is_active=1").fetchone()[0]
    students = conn.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
    counselors = conn.execute("SELECT COUNT(*) FROM users WHERE role='counselor'").fetchone()[0]
    admins = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]

    total_predictions = conn.execute("SELECT COUNT(*) FROM prediction_history").fetchone()[0]

    # New users this week
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    new_this_week = conn.execute(
        "SELECT COUNT(*) FROM users WHERE created_at >= ?", (week_ago,)
    ).fetchone()[0]

    # Predictions this week
    preds_this_week = conn.execute(
        "SELECT COUNT(*) FROM prediction_history WHERE created_at >= ?", (week_ago,)
    ).fetchone()[0]

    # Profile completion average
    avg_completion = conn.execute(
        "SELECT AVG(profile_complete) FROM student_profiles"
    ).fetchone()[0] or 0

    # Most predicted career
    top_career = conn.execute(
        "SELECT career_1, COUNT(*) as cnt FROM prediction_history "
        "GROUP BY career_1 ORDER BY cnt DESC LIMIT 1"
    ).fetchone()

    # Registrations last 7 days (for sparkline)
    daily_regs = []
    for i in range(6, -1, -1):
        day_start = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
        day_end   = (datetime.now(timezone.utc) - timedelta(days=i-1)).strftime("%Y-%m-%d")
        cnt = conn.execute(
            "SELECT COUNT(*) FROM users WHERE created_at >= ? AND created_at < ?",
            (day_start, day_end)
        ).fetchone()[0]
        daily_regs.append({"date": day_start, "count": cnt})

    # Predictions last 7 days
    daily_preds = []
    for i in range(6, -1, -1):
        day_start = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
        day_end   = (datetime.now(timezone.utc) - timedelta(days=i-1)).strftime("%Y-%m-%d")
        cnt = conn.execute(
            "SELECT COUNT(*) FROM prediction_history WHERE created_at >= ? AND created_at < ?",
            (day_start, day_end)
        ).fetchone()[0]
        daily_preds.append({"date": day_start, "count": cnt})

    conn.close()

    return ok({
        "users": {
            "total":        total_users,
            "active":       active_users,
            "students":     students,
            "counselors":   counselors,
            "admins":       admins,
            "new_this_week":new_this_week,
        },
        "predictions": {
            "total":          total_predictions,
            "this_week":      preds_this_week,
            "top_career":     top_career[0] if top_career else "N/A",
            "top_career_count":top_career[1] if top_career else 0,
        },
        "platform": {
            "total_careers":      len(CAREER_KNOWLEDGE),
            "total_scholarships": len(SCHOLARSHIPS),
            "avg_profile_completion": round(float(avg_completion) * 100, 1),
        },
        "charts": {
            "daily_registrations": daily_regs,
            "daily_predictions":   daily_preds,
        }
    }, "Platform stats loaded.")


# ── USER MANAGEMENT ───────────────────────────────────────────────────────────
@admin.route("/users", methods=["GET"])
@require_auth
@require_role("admin")
def list_users():
    """List all users with pagination + search + filter."""
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    search   = request.args.get("search", "").strip()
    role_f   = request.args.get("role", "")
    offset   = (page - 1) * per_page

    conn = get_db()
    where_clauses = []
    params = []

    if search:
        where_clauses.append("(u.name LIKE ? OR u.email LIKE ?)")
        params += [f"%{search}%", f"%{search}%"]
    if role_f:
        where_clauses.append("u.role = ?")
        params.append(role_f)

    where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    total = conn.execute(
        f"SELECT COUNT(*) FROM users u {where}", params
    ).fetchone()[0]

    rows = conn.execute(f"""
        SELECT u.id, u.name, u.email, u.role, u.is_active, u.is_verified,
               u.avatar_initials, u.created_at, u.last_login,
               sp.gpa, sp.education_level, sp.region, sp.profile_complete,
               (SELECT COUNT(*) FROM prediction_history ph WHERE ph.user_id=u.id) as pred_count
        FROM users u
        LEFT JOIN student_profiles sp ON sp.user_id=u.id
        {where}
        ORDER BY u.created_at DESC
        LIMIT ? OFFSET ?
    """, params + [per_page, offset]).fetchall()

    conn.close()

    return ok({
        "users":      [dict(r) for r in rows],
        "total":      total,
        "page":       page,
        "per_page":   per_page,
        "total_pages":  (total + per_page - 1) // per_page,
    }, f"{total} users found.")


@admin.route("/users/<int:user_id>", methods=["GET"])
@require_auth
@require_role("admin")
def get_user(user_id):
    """Get single user — full profile + prediction history."""
    user    = UserModel.get_by_id(user_id)
    if not user: return err("User not found.", 404)

    profile    = ProfileModel.get(user_id)
    history    = PredictionModel.get_history(user_id, 5)
    completion = ProfileModel.completion_pct(user_id)

    conn = get_db()
    saved_count = conn.execute(
        "SELECT COUNT(*) FROM saved_scholarships WHERE user_id=?", (user_id,)
    ).fetchone()[0]
    conn.close()

    return ok({
        "user":          user,
        "profile":       profile,
        "history":       history,
        "completion":    completion,
        "saved_scholarships": saved_count,
    }, "User details loaded.")


@admin.route("/users/<int:user_id>", methods=["PUT"])
@require_auth
@require_role("admin")
def update_user(user_id):
    """Update user role or active status."""
    data = request.get_json(silent=True) or {}
    ALLOWED = {"role", "is_active", "is_verified"}
    update  = {k: v for k, v in data.items() if k in ALLOWED}

    if not update:
        return err("No valid fields provided.", 400)

    # Prevent admin from removing their own admin role
    if g.user_id == user_id and "role" in update and update["role"] != "admin":
        return err("Cannot remove your own admin role.", 403)

    conn = get_db()
    set_clause = ", ".join(f"{k}=?" for k in update)
    conn.execute(
        f"UPDATE users SET {set_clause}, updated_at=datetime('now') WHERE id=?",
        list(update.values()) + [user_id]
    )
    conn.commit()
    conn.close()

    return ok({"user_id": user_id, "updated": update}, "User updated.")


@admin.route("/users/<int:user_id>", methods=["DELETE"])
@require_auth
@require_role("admin")
def deactivate_user(user_id):
    """Soft-delete: deactivate a user account."""
    if g.user_id == user_id:
        return err("Cannot deactivate your own account.", 403)

    conn = get_db()
    conn.execute("UPDATE users SET is_active=0 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    return ok({"user_id": user_id, "deactivated": True}, "User deactivated.")


# ── PREDICTIONS ANALYTICS ─────────────────────────────────────────────────────
@admin.route("/predictions", methods=["GET"])
@require_auth
@require_role("admin")
def all_predictions():
    """All predictions with career distribution analytics."""
    conn = get_db()

    # Career distribution
    career_dist = conn.execute("""
        SELECT career_1 as career, COUNT(*) as count
        FROM prediction_history
        WHERE career_1 IS NOT NULL
        GROUP BY career_1
        ORDER BY count DESC
        LIMIT 15
    """).fetchall()

    # Recent predictions
    recent = conn.execute("""
        SELECT ph.id, ph.career_1, ph.prob_1, ph.career_2, ph.prob_2,
               ph.career_3, ph.prob_3, ph.created_at,
               u.name as user_name, u.email as user_email
        FROM prediction_history ph
        JOIN users u ON u.id = ph.user_id
        ORDER BY ph.created_at DESC
        LIMIT 50
    """).fetchall()

    # Average probabilities
    avg_prob = conn.execute(
        "SELECT AVG(prob_1) FROM prediction_history WHERE prob_1 IS NOT NULL"
    ).fetchone()[0] or 0

    conn.close()

    return ok({
        "career_distribution": [dict(r) for r in career_dist],
        "recent_predictions":  [dict(r) for r in recent],
        "avg_top_probability": round(float(avg_prob), 2),
    }, "Predictions analytics loaded.")


# ── CAREER MANAGEMENT ─────────────────────────────────────────────────────────
@admin.route("/careers", methods=["GET"])
@require_auth
@require_role("admin")
def list_careers_admin():
    """List all careers with edit capability."""
    careers = [
        {
            "name":         name,
            "job_demand":   data.get("job_demand"),
            "skills_count": len(data.get("required_skills", [])),
            "tools_count":  len(data.get("tools", [])),
            "salary_entry": data.get("salary", {}).get("entry"),
            "salary_senior":data.get("salary", {}).get("senior"),
            "roadmap_steps":len(data.get("roadmap", [])),
        }
        for name, data in CAREER_KNOWLEDGE.items()
    ]
    return ok({"careers": careers, "total": len(careers)}, f"{len(careers)} careers.")


# ── SCHOLARSHIP MANAGEMENT ────────────────────────────────────────────────────
@admin.route("/scholarships", methods=["GET"])
@require_auth
@require_role("admin")
def list_scholarships_admin():
    """List all scholarships with save counts."""
    conn = get_db()
    result = []
    for s in SCHOLARSHIPS:
        count = conn.execute(
            "SELECT COUNT(*) FROM saved_scholarships WHERE scholarship_id=?", (s["id"],)
        ).fetchone()[0]
        result.append({**s, "saved_by_users": count})
    conn.close()

    return ok({"scholarships": result, "total": len(result)},
              f"{len(result)} scholarships.")


# ── ANALYTICS ─────────────────────────────────────────────────────────────────
@admin.route("/analytics", methods=["GET"])
@require_auth
@require_role("admin")
def analytics():
    """Detailed analytics: degrees, regions, career distribution."""
    conn = get_db()

    # Degree distribution
    degree_dist = conn.execute("""
        SELECT degree, COUNT(*) as count
        FROM student_profiles
        WHERE degree IS NOT NULL
        GROUP BY degree ORDER BY count DESC
    """).fetchall()

    # Region distribution
    region_dist = conn.execute("""
        SELECT region, COUNT(*) as count
        FROM student_profiles
        WHERE region IS NOT NULL
        GROUP BY region ORDER BY count DESC LIMIT 10
    """).fetchall()

    # GPA distribution buckets
    gpa_dist = conn.execute("""
        SELECT
          CASE
            WHEN gpa < 2.0 THEN 'Below 2.0'
            WHEN gpa < 2.5 THEN '2.0 – 2.5'
            WHEN gpa < 3.0 THEN '2.5 – 3.0'
            WHEN gpa < 3.5 THEN '3.0 – 3.5'
            ELSE '3.5 – 4.0'
          END as bucket,
          COUNT(*) as count
        FROM student_profiles
        WHERE gpa IS NOT NULL
        GROUP BY bucket ORDER BY bucket
    """).fetchall()

    # Category distribution
    cat_dist = conn.execute("""
        SELECT category, COUNT(*) as count
        FROM student_profiles
        WHERE category IS NOT NULL
        GROUP BY category ORDER BY count DESC
    """).fetchall()

    # Top careers
    top_careers = conn.execute("""
        SELECT career_1 as career, COUNT(*) as count
        FROM prediction_history WHERE career_1 IS NOT NULL
        GROUP BY career_1 ORDER BY count DESC LIMIT 10
    """).fetchall()

    # Monthly signups (last 6 months)
    monthly = []
    for i in range(5, -1, -1):
        d     = datetime.now(timezone.utc) - timedelta(days=i*30)
        month = d.strftime("%Y-%m")
        cnt   = conn.execute(
            "SELECT COUNT(*) FROM users WHERE strftime('%Y-%m',created_at)=?", (month,)
        ).fetchone()[0]
        monthly.append({"month": d.strftime("%b %Y"), "count": cnt})

    conn.close()

    return ok({
        "degree_distribution":  [dict(r) for r in degree_dist],
        "region_distribution":  [dict(r) for r in region_dist],
        "gpa_distribution":     [dict(r) for r in gpa_dist],
        "category_distribution":[dict(r) for r in cat_dist],
        "top_careers":          [dict(r) for r in top_careers],
        "monthly_signups":      monthly,
    }, "Analytics loaded.")


# ── ACTIVITY LOG ──────────────────────────────────────────────────────────────
@admin.route("/logs", methods=["GET"])
@require_auth
@require_role("admin")
def activity_logs():
    """Recent platform activity — latest registrations + predictions."""
    conn = get_db()

    # Recent registrations
    reg = conn.execute("""
        SELECT 'registration' as type, name as subject, email as detail,
               created_at as timestamp FROM users
        ORDER BY created_at DESC LIMIT 15
    """).fetchall()

    # Recent predictions
    pred = conn.execute("""
        SELECT 'prediction' as type, u.name as subject,
               ph.career_1 as detail, ph.created_at as timestamp
        FROM prediction_history ph
        JOIN users u ON u.id=ph.user_id
        ORDER BY ph.created_at DESC LIMIT 15
    """).fetchall()

    # Merge and sort
    logs = sorted(
        [dict(r) for r in reg] + [dict(r) for r in pred],
        key=lambda x: x["timestamp"], reverse=True
    )[:25]

    conn.close()
    return ok({"logs": logs, "total": len(logs)}, "Activity logs loaded.")
