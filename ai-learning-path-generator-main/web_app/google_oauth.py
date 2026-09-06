import os
from flask import Blueprint, redirect, url_for, flash, current_app, session, request
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import login_user
from web_app.models import User
from web_app import db
import logging
from flask_dance.consumer.storage.session import SessionStorage

# Ensure local development can use HTTP for OAuth exchanges
if os.getenv("FLASK_ENV", "development") == "development" and not os.getenv("RENDER"):
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('google_oauth')

# Log environment variables only in debug mode
if os.getenv("DEBUG") == "True" and os.getenv("LOG_ENV_VARS") == "True":
    for key in os.environ:
        if 'SECRET' not in key and 'KEY' not in key:
            logger.info(f"ENV: {key}={os.environ.get(key)}")

# Create a very basic blueprint for Google OAuth
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ],
    redirect_to="google_auth.google_callback",
    redirect_url="/auth/google/authorized",
    storage=SessionStorage()
)


# Create a separate blueprint for our callback route
bp = Blueprint("google_auth", __name__)

# Add login helpers that point to the Flask-Dance blueprint
@bp.route("/login")
def login():
    return redirect(url_for("google.login"))


@bp.route("/google")
def start_google_login():
    """Route used by the UI to start Google OAuth."""
    return redirect(url_for("google.login"))

@bp.route("/google/authorized")
@bp.route("/callback/google")
@bp.route("/google-callback")
def google_callback():
    """Handle the callback from Google OAuth"""
    # Log important debug info
    logger.info(f"Google OAuth callback received at {request.path}")
    logger.info(f"Full request URL: {request.url}")
    logger.info(f"Request args: {request.args}")
    logger.info(f"Is Google authorized? {google.authorized}")
    
    # If this route is hit directly without going through OAuth flow
    if not google.authorized:
        logger.error("Not authorized. Redirecting to login.")
        flash("Please try logging in again.", "info")
        return redirect(url_for("auth.login"))

    # Get user info from Google
    try:
        resp = google.get("/oauth2/v2/userinfo")
        if not resp.ok:
            logger.error(f"Failed to fetch user info: {resp.text}")
            flash("Failed to fetch user info from Google.", "danger")
            return redirect(url_for("auth.login"))

        info = resp.json()
        logger.info(f"Successfully retrieved user info")
        
        email = info.get("email")
        if not email:
            logger.error("Google account does not have an email.")
            flash("Google account does not have an email.", "danger")
            return redirect(url_for("auth.login"))

        # Find or create user
        user = User.query.filter_by(email=email).first()
        if not user:
            logger.info(f"Creating new user: {email}")
            user = User(
                username=info.get("name", email.split("@")[0]), 
                email=email,
                registration_source='google'
            )
            db.session.add(user)
            db.session.commit()
            flash("Welcome! Your account has been created.", "success")
        else:
            logger.info(f"Found existing user: {email}")

        # Log the user in with a permanent session
        session.permanent = True
        login_user(user, remember=True, duration=None)
        
        flash("Logged in with Google!", "success")
        return redirect("/")
        
    except Exception as e:
        logger.exception(f"Error in Google callback: {str(e)}")
        # Check if it's a state mismatch error
        if "MismatchingStateError" in str(type(e).__name__) or "state" in str(e).lower():
            flash("Session expired. Please try logging in again.", "warning")
        else:
            flash(f"An error occurred during login. Please try again.", "danger")
        return redirect(url_for("auth.login"))
