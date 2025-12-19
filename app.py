"""
GymSphere Flask Application

A production-ready fitness app with AI-powered workout and nutrition recommendations.

Quick Start:
1. Install dependencies: pip install -r requirements.txt
2. Initialize database: flask --app app initdb
3. Seed data: python seed_data.py
4. Create admin: flask --app app create-admin
5. Run: python run.py or flask --app app run
"""
from __future__ import annotations

import os
import getpass
from flask import Flask
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

from config import Config
from models import User, db

# Import Blueprints
from routes.auth import auth_bp
from routes.core import core_bp
from routes.onboarding import onboarding_bp
from routes.api import api_bp

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize Extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login" # Updated to blueprint view
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        return User.query.get(int(user_id))

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(core_bp) # Registered at root /
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(api_bp)

    # CLI Commands
    @app.cli.command("initdb")
    def initdb_command():
        """Initialize the database."""
        with app.app_context():
            db.create_all()
        print("Database initialized.")

    @app.cli.command("create-admin")
    def create_admin_command():
        """Create an admin user via CLI prompts."""
        name = input("Full name: ")
        email = input("Email: ")
        password = getpass.getpass("Password: ")
        with app.app_context():
            if User.query.filter_by(email=email).first():
                print("User already exists.")
                return
            admin = User(
                fullname=name,
                email=email,
                password_hash=generate_password_hash(password),
                is_admin=True,
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin created.")

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
