"""
app.py — AI Student Intelligence Platform
Production-ready Flask backend with CORS, env vars, and health check.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from services.ml_service import ml_service
from routes.api import api

def create_app():
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    # ── CORS ─────────────────────────────────────────────────────────────────
    @app.after_request
    def cors(response):
        origin = os.getenv("ALLOWED_ORIGINS", "*")
        response.headers["Access-Control-Allow-Origin"]  = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        return response

    @app.route("/api/v1/<path:p>", methods=["OPTIONS"])
    def preflight(p): return "", 204

    # ── Routes ────────────────────────────────────────────────────────────────
    app.register_blueprint(api, url_prefix="/api/v1")

    @app.route("/")
    def root():
        return jsonify({
            "name": "AI Student Intelligence Platform API",
            "version": "1.0.0", "status": "running",
            "endpoints": {
                "health":      "GET  /api/v1/health",
                "predict":     "POST /api/v1/predict",
                "careers":     "GET  /api/v1/careers",
                "scholarships":"GET  /api/v1/scholarships",
                "resources":   "GET  /api/v1/resources/<career>",
                "xai":         "GET  /api/v1/xai/global",
            }
        })

    @app.errorhandler(404)
    def e404(e): return jsonify({"status":"error","message":"Not found"}), 404
    @app.errorhandler(500)
    def e500(e): return jsonify({"status":"error","message":"Server error","details":str(e)}), 500

    ml_service.load()
    return app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "production") == "development"
    print(f"\n{'='*50}\n  CareerAI Backend  →  http://0.0.0.0:{port}\n{'='*50}\n")
    create_app().run(host="0.0.0.0", port=port, debug=debug)
