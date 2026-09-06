"""
Unified Flask + React Application
Serves React frontend at root, Flask API routes, and OAuth
"""
import os
from flask import jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create the main app using the existing web_app factory (includes DB, OAuth, routes)
from web_app import create_app
app = create_app()

# Register the lightweight API blueprint for RQ task orchestration under /api
from backend.routes import api_bp
app.register_blueprint(api_bp, url_prefix='/api')

# Enable CORS for the React frontend and allow cookies for auth
frontend_origin = os.getenv('FRONTEND_ORIGIN', 'http://localhost:3000')
CORS(
    app,
    resources={r"/*": {"origins": [frontend_origin]}},
    supports_credentials=True,
)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "api+web"}), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
