"""Application Factory for the Travel Booking Platform."""
import os
from flask import Flask
from config import config_by_name
from app.extensions import db, migrate, login_manager


def create_app(config_name=None):
    """Create and configure the Flask application.

    Args:
        config_name: One of 'development', 'production', or 'default'.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Enable CORS for the React frontend (running on Vite's default port 5173)
    from flask_cors import CORS
    CORS(app, supports_credentials=True, resources={r"/api/*": {
        "origins": ["http://localhost:5001", "http://localhost:5173", "http://127.0.0.1:5001"]
    }})

    # --- Initialize extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # --- User loader for Flask-Login ---
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Register blueprints ---
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.flights import flights_bp
    from app.blueprints.trains import trains_bp
    from app.blueprints.buses import buses_bp
    from app.blueprints.hotels import hotels_bp
    from app.blueprints.payment import payment_bp
    from app.blueprints.api import api_bp
    from app.blueprints.chatbot import chatbot_bp
    from app.blueprints.seat_api import seat_api_bp
    from app.blueprints.ticket import ticket_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(flights_bp, url_prefix='/flights')
    app.register_blueprint(trains_bp, url_prefix='/trains')
    app.register_blueprint(buses_bp, url_prefix='/buses')
    app.register_blueprint(hotels_bp, url_prefix='/hotels')
    app.register_blueprint(payment_bp, url_prefix='/payment')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(chatbot_bp, url_prefix='/api/chat')
    app.register_blueprint(seat_api_bp)
    app.register_blueprint(ticket_bp)

    # --- CSRF Protection ---
    import secrets
    from flask import session, request as req, abort
    from markupsafe import Markup

    CSRF_EXEMPT_ENDPOINTS = {'chatbot.chat', 'api.create_review', 'api.get_reviews'}

    @app.before_request
    def _csrf_protect():
        if req.method == 'POST':
            if req.endpoint in CSRF_EXEMPT_ENDPOINTS:
                return  # JSON APIs exempt
            token = session.get('_csrf_token')
            form_token = req.form.get('_csrf_token')
            if not token or token != form_token:
                abort(403)

    def _generate_csrf_token():
        if '_csrf_token' not in session:
            session['_csrf_token'] = secrets.token_hex(32)
        return session['_csrf_token']

    @app.context_processor
    def _inject_csrf():
        def csrf_token():
            token = _generate_csrf_token()
            return Markup(f'<input type="hidden" name="_csrf_token" value="{token}">')
        return dict(csrf_token=csrf_token)

    # --- Create tables if they don't exist (dev convenience) ---
    with app.app_context():
        db.create_all()

    return app
