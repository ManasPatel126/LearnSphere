import os
import redis
from rq import Queue
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import text

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Route for @login_required
login_manager.login_message_category = 'info'
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # If the app is running behind a proxy (like on Render), fix the WSGI environment
    if os.environ.get('RENDER'):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Set DEV_MODE from environment
    app.config['DEV_MODE'] = os.environ.get('DEV_MODE', 'False').lower() == 'true'
    if app.config['DEV_MODE']:
        print("\033[93m⚠️  Running in DEV_MODE - API calls will be stubbed!\033[0m")

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Initialize Redis connection for RQ
    try:
        redis_url = os.environ.get('REDIS_URL')
        if not redis_url:
            raise ValueError("REDIS_URL not set, worker queue will not be available.")
        # ssl_cert_reqs=None is important for managed services like Upstash/Render Redis
        app.redis = redis.from_url(redis_url, ssl_cert_reqs=None)
        app.logger.info("Redis connection for RQ initialized successfully.")
    except Exception as e:
        app.logger.error(f"Failed to initialize Redis connection: {e}")
        app.redis = None

    # Import and register blueprints
    from web_app.main_routes import bp as main_bp
    app.register_blueprint(main_bp)

    from web_app.auth_routes import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from web_app.api_endpoints import api_bp
    app.register_blueprint(api_bp)

    # Import models here to ensure they are registered with SQLAlchemy
    from web_app import models
    
    # Health endpoint for keep-alive (prevents Supabase auto-pause)
    @app.route('/health')
    def health():
        try:
            with app.app_context():
                with db.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            return {"status": "ok", "db": "connected"}, 200
        except Exception as e:
            return {"status": "error", "db": str(e)}, 500

    # Google OAuth blueprint (Flask-Dance)
    from web_app.google_oauth import google_bp, bp as google_auth_bp
    # Register Flask-Dance blueprint at /login/google
    app.register_blueprint(google_bp, url_prefix="/login")
    # Register our auth blueprint for callbacks and helper routes under /auth
    app.register_blueprint(google_auth_bp, url_prefix="/auth")
    
    # Flask-Dance will use session storage by default
    # This works better for our use case since we create the user in our callback

    return app
