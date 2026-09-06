"""
Phase 1 — Input & Topic Decomposition
Flask application entry point.
"""

import os
from flask import Flask
from flask_cors import CORS
from redis import Redis
from rq import Queue
from dotenv import load_dotenv

load_dotenv()

from routes.input_routes import input_bp
from routes.session_routes import session_bp


def create_app():
    app = Flask(__name__)

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS(app, origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")])

    # ── Redis / RQ ────────────────────────────────────────────────────────────
    app.redis = Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=0,
    )
    app.task_queue = Queue("phase1", connection=app.redis)

    # ── Blueprints ────────────────────────────────────────────────────────────
    app.register_blueprint(input_bp, url_prefix="/api")
    app.register_blueprint(session_bp, url_prefix="/api")

    @app.get("/health")
    def health():
        return {"status": "ok", "phase": 1}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
