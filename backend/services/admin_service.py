"""
services/admin_service.py
────────────────────────────────────────────────────────────────
Admin service layer — analytics, user management, content CRUD.
All reads/writes go through here, keeping routes thin.
"""

import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta, timezone
from models.user_model import get_db


# ═══════════════════════════════════════════════════════════════════════════
# PLATFORM ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════

class AnalyticsService:

    @staticmethod
    def overview() -> dict:
        """Top-level KPIs for the admin dashboard header cards."""
        conn = get_db()

        total_users = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role='student'"
        ).fetchone()[0]

        total_predictions = conn.execute(
            "SELECT COUNT(*) FROM prediction_history"
        ).fetchone()[0]

        profiles_complete = conn.execute(
            "SELECT COUNT(*) FROM student_profiles WHERE profile_complete=1"
        ).fetchone()[0]

        new_today = conn.execute(
            "SELECT COUNT(*) FROM users WHERE date(created_at)=date('now')"
        ).fetchone()[0]

        new_this_week = conn.execute(
            "SELECT COUNT(*) FROM users WHERE created_at >= datetime('now','-7 days')"
        ).fetchone()[0]

        active_this_week = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM prediction_history "
            "WHERE created_at >= datetime('now','-7 days')"
        ).fetchone()[0]

        avg_completion = conn.execute(
            "SELECT AVG(CAST(profile_complete AS REAL)*100) FROM student_profiles"
        ).fetchone()[0] or 0

        conn.close()
        return {
            "total_students":      total_users,
            "total_predictions":   total_predictions,
            "profiles_complete":   profiles_complete,
            "new_today":           new_today,
            "new_this_week":       new_this_week,
            "active_this_week":    active_this_week,
            "avg_profile_completion": round(avg_completion, 1),
        }

    @staticmethod
    def registrations_over_time(days: int = 30) -> list:
        """Daily registration counts for the trend chart."""
        conn = get_db()
        rows = conn.execute("""
            SELECT date(created_at) as day, COUNT(*) as count
            FROM users
            WHERE created_at >= datetime('now', ?)
            GROUP BY date(created_at)
            ORDER BY day ASC
        """, (f"-{days} days",)).fetchall()
        conn.close()

        # Fill missing days with 0
        result = {}
        for i in range(days):
            day = (datetime.now(timezone.utc) - timedelta(days=days-1-i)).strftime("%Y-%m-%d")
            result[day] = 0
        for row in rows:
            result[row["day"]] = row["count"]

        return [{"date": k, "count": v} for k, v in result.items()]

    @staticmethod
    def top_predicted_careers(limit: int = 10) -> list:
        """Most frequently predicted careers across all students."""
        conn = get_db()
        rows = conn.execute("""
            SELECT career_1 as career, COUNT(*) as count
            FROM prediction_history WHERE career_1 IS NOT NULL
            GROUP BY career_1
            UNION ALL
            SELECT career_2, COUNT(*) FROM prediction_history WHERE career_2 IS NOT NULL GROUP BY career_2
            UNION ALL
            SELECT career_3, COUNT(*) FROM prediction_history WHERE career_3 IS NOT NULL GROUP BY career_3
        """).fetchall()
        conn.close()

        # Aggregate
        agg = {}
        for row in rows:
            agg[row["career"]] = agg.get(row["career"], 0) + row["count"]

        sorted_careers = sorted(agg.items(), key=lambda x: x[1], reverse=True)[:limit]
        total = sum(v for _, v in sorted_careers)
        return [
            {"career": k, "count": v, "pct": round(v/total*100, 1) if total else 0}
            for k, v in sorted_careers
        ]

    @staticmethod
    def region_distribution() -> list:
        """Student count per region for geo chart."""
        conn = get_db()
        rows = conn.execute("""
            SELECT region, COUNT(*) as count
            FROM student_profiles
            WHERE region IS NOT NULL
            GROUP BY region ORDER BY count DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def degree_distribution() -> list:
        """Student count per degree."""
        conn = get_db()
        rows = conn.execute("""
            SELECT degree, COUNT(*) as count
            FROM student_profiles
            WHERE degree IS NOT NULL
            GROUP BY degree ORDER BY count DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def predictions_over_time(days: int = 30) -> list:
        """Daily prediction counts."""
        conn = get_db()
        rows = conn.execute("""
            SELECT date(created_at) as day, COUNT(*) as count
            FROM prediction_history
            WHERE created_at >= datetime('now', ?)
            GROUP BY date(created_at) ORDER BY day ASC
        """, (f"-{days} days",)).fetchall()
        conn.close()

        result = {}
        for i in range(days):
            day = (datetime.now(timezone.utc) - timedelta(days=days-1-i)).strftime("%Y-%m-%d")
            result[day] = 0
        for row in rows:
            result[row["day"]] = row["count"]
        return [{"date": k, "count": v} for k, v in result.items()]

    @staticmethod
    def gpa_distribution() -> list:
        """GPA distribution in buckets."""
        conn = get_db()
        rows = conn.execute("""
            SELECT
              CASE
                WHEN gpa < 2.0 THEN 'Below 2.0'
                WHEN gpa < 2.5 THEN '2.0 – 2.5'
                WHEN gpa < 3.0 THEN '2.5 – 3.0'
                WHEN gpa < 3.5 THEN '3.0 – 3.5'
                ELSE '3.5 – 4.0'
              END as bucket,
              COUNT(*) as count
            FROM student_profiles WHERE gpa IS NOT NULL
            GROUP BY bucket ORDER BY bucket
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════
# USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

class UserManagementService:

    @staticmethod
    def list_users(page: int = 1, per_page: int = 20,
                   search: str = "", role: str = "") -> dict:
        """Paginated user list with optional search + role filter."""
        conn   = get_db()
        offset = (page - 1) * per_page
        where  = ["1=1"]
        params = []

        if search:
            where.append("(u.name LIKE ? OR u.email LIKE ?)")
            params += [f"%{search}%", f"%{search}%"]
        if role:
            where.append("u.role=?")
            params.append(role)

        where_clause = " AND ".join(where)

        total = conn.execute(
            f"SELECT COUNT(*) FROM users u WHERE {where_clause}", params
        ).fetchone()[0]

        rows = conn.execute(f"""
            SELECT u.id, u.name, u.email, u.role, u.is_active,
                   u.avatar_initials, u.created_at, u.last_login,
                   p.profile_complete, p.degree, p.region,
                   p.gpa, p.aptitude_score,
                   (SELECT COUNT(*) FROM prediction_history ph WHERE ph.user_id=u.id) as pred_count
            FROM users u
            LEFT JOIN student_profiles p ON p.user_id=u.id
            WHERE {where_clause}
            ORDER BY u.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, offset]).fetchall()
        conn.close()

        return {
            "users":      [dict(r) for r in rows],
            "total":      total,
            "page":       page,
            "per_page":   per_page,
            "total_pages": max(1, -(-total // per_page)),
        }

    @staticmethod
    def get_user_detail(user_id: int) -> dict | None:
        """Full user detail including profile + prediction history."""
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE id=?", (user_id,)
        ).fetchone()

        if not user:
            conn.close()
            return None

        profile = conn.execute(
            "SELECT * FROM student_profiles WHERE user_id=?", (user_id,)
        ).fetchone()

        history = conn.execute(
            "SELECT * FROM prediction_history WHERE user_id=? ORDER BY created_at DESC LIMIT 5",
            (user_id,)
        ).fetchall()

        conn.close()

        return {
            "user":    {k: v for k, v in dict(user).items() if k != "password_hash"},
            "profile": dict(profile) if profile else {},
            "history": [dict(h) for h in history],
        }

    @staticmethod
    def toggle_user_active(user_id: int) -> dict:
        """Enable or disable a user account."""
        conn = get_db()
        current = conn.execute(
            "SELECT is_active FROM users WHERE id=?", (user_id,)
        ).fetchone()

        if not current:
            conn.close()
            return {"error": "User not found"}

        new_status = 0 if current["is_active"] else 1
        conn.execute(
            "UPDATE users SET is_active=? WHERE id=?", (new_status, user_id)
        )
        conn.commit()
        conn.close()
        return {"user_id": user_id, "is_active": bool(new_status)}

    @staticmethod
    def change_user_role(user_id: int, new_role: str) -> dict:
        """Change a user's role."""
        if new_role not in ("student", "counselor", "admin"):
            return {"error": "Invalid role"}
        conn = get_db()
        conn.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
        conn.commit()
        conn.close()
        return {"user_id": user_id, "role": new_role}

    @staticmethod
    def delete_user(user_id: int) -> dict:
        """Soft delete — deactivate + anonymize PII."""
        conn = get_db()
        conn.execute(
            "UPDATE users SET is_active=0, name='[Deleted]', email=? WHERE id=?",
            (f"deleted_{user_id}@careerai.com", user_id)
        )
        conn.commit()
        conn.close()
        return {"deleted": True, "user_id": user_id}


# ═══════════════════════════════════════════════════════════════════════════
# CONTENT MANAGEMENT (Scholarships)
# ═══════════════════════════════════════════════════════════════════════════

class ContentService:
    """
    In production this would write to the DB.
    For now it manages scholarships in-memory + config.
    Swap with full DB CRUD when PostgreSQL is integrated.
    """

    @staticmethod
    def get_platform_stats() -> dict:
        """Quick stats for content management tab."""
        conn = get_db()
        saved_count = conn.execute(
            "SELECT COUNT(*) FROM saved_scholarships"
        ).fetchone()[0]
        conn.close()

        return {
            "saved_scholarships": saved_count,
            "total_scholarships": 15,   # from config
            "total_careers":      16,   # from config
            "total_resources":    40,   # from config
        }

    @staticmethod
    def recent_activity(limit: int = 10) -> list:
        """Recent platform activity feed."""
        conn = get_db()
        rows = conn.execute("""
            SELECT 'new_user' as type, name as detail, created_at as ts
            FROM users ORDER BY created_at DESC LIMIT 5
        """).fetchall()

        preds = conn.execute("""
            SELECT 'prediction' as type,
                   career_1 || ' predicted' as detail,
                   created_at as ts
            FROM prediction_history ORDER BY created_at DESC LIMIT 5
        """).fetchall()
        conn.close()

        activity = [dict(r) for r in rows] + [dict(r) for r in preds]
        activity.sort(key=lambda x: x["ts"] or "", reverse=True)
        return activity[:limit]
