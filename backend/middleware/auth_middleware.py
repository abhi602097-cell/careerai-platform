"""
middleware/auth_middleware.py
────────────────────────────────────────────────────────────────
JWT authentication middleware.
Use @require_auth on any route that needs a logged-in user.
Use @require_role("admin") for role-based access control.
"""

from functools import wraps
from flask import request, jsonify, g
from services.auth_service import decode_access_token
from models.user_model import UserModel
from datetime import datetime, timezone


def _extract_token() -> str | None:
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    # Also check cookie as fallback
    return request.cookies.get("access_token")


def require_auth(f):
    """
    Decorator: protect a route with JWT authentication.
    Injects g.user_id, g.user_email, g.user_role into Flask context.

    Usage:
        @api.route("/profile")
        @require_auth
        def get_profile():
            user_id = g.user_id
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()

        if not token:
            return jsonify({
                "status": "error",
                "message": "Authentication required. Please log in.",
                "code": "NO_TOKEN"
            }), 401

        payload = decode_access_token(token)

        if not payload:
            return jsonify({
                "status": "error",
                "message": "Invalid token. Please log in again.",
                "code": "INVALID_TOKEN"
            }), 401

        if payload.get("error") == "token_expired":
            return jsonify({
                "status": "error",
                "message": "Session expired. Please refresh your token.",
                "code": "TOKEN_EXPIRED"
            }), 401

        # Inject user info into Flask request context
        g.user_id    = int(payload["sub"])
        g.user_email = payload["email"]
        g.user_role  = payload["role"]

        return f(*args, **kwargs)
    return decorated


def require_role(*roles):
    """
    Decorator: require specific role(s).
    Must be used AFTER @require_auth.

    Usage:
        @api.route("/admin/users")
        @require_auth
        @require_role("admin")
        def admin_users():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, "user_role"):
                return jsonify({
                    "status": "error",
                    "message": "Authentication required.",
                    "code": "NO_AUTH"
                }), 401
            if g.user_role not in roles:
                return jsonify({
                    "status": "error",
                    "message": f"Access denied. Required role: {', '.join(roles)}",
                    "code": "FORBIDDEN"
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def optional_auth(f):
    """
    Decorator: attach user if token present, but don't block if not.
    Sets g.user_id = None if no valid token.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        g.user_id    = None
        g.user_email = None
        g.user_role  = None

        if token:
            payload = decode_access_token(token)
            if payload and not payload.get("error"):
                g.user_id    = int(payload["sub"])
                g.user_email = payload["email"]
                g.user_role  = payload["role"]

        return f(*args, **kwargs)
    return decorated
