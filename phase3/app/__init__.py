from flask import Flask
from app.config import settings
from app.routes import bp as roadmap_bp


def create_app() -> Flask:
    settings.validate()
    app = Flask(__name__)
    app.register_blueprint(roadmap_bp)
    return app
