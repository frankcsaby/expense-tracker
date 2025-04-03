from flask import Flask
from app.config import SECRET_KEY, DEBUG
from app.database import init_db
from app.controllers.expense_controller import expense_bp
from app.controllers.analytics_controller import analytics_bp
from app.controllers.budget_controller import budget_bp
from app.controllers.settings_controller import settings_bp

def create_app():
    """Initialize and configure the Flask application."""
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.debug = DEBUG
    
    # Initialize database
    init_db()
    
    # Register blueprints
    app.register_blueprint(expense_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(settings_bp)
    
    return app 