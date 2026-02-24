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
    CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

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

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(flights_bp, url_prefix='/flights')
    app.register_blueprint(trains_bp, url_prefix='/trains')
    app.register_blueprint(buses_bp, url_prefix='/buses')
    app.register_blueprint(hotels_bp, url_prefix='/hotels')
    app.register_blueprint(payment_bp, url_prefix='/payment')
    app.register_blueprint(api_bp, url_prefix='/api')

    # --- Create tables if they don't exist (dev convenience) ---
    with app.app_context():
        db.create_all()

    return app
