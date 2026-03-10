from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import uuid
from datetime import datetime
import logging
from models import Base, User, CreditPurchase, GuestUsage

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration - use Replit's PG vars if DATABASE_URL is unavailable
def get_database_url():
    db_url = os.environ.get("DATABASE_URL")
    # Build from individual PG vars as fallback (Replit managed PostgreSQL)
    pg_host = os.environ.get("PGHOST")
    pg_user = os.environ.get("PGUSER")
    pg_password = os.environ.get("PGPASSWORD")
    pg_database = os.environ.get("PGDATABASE")
    pg_port = os.environ.get("PGPORT", "5432")
    if pg_host and pg_user and pg_password and pg_database:
        constructed = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}?sslmode=require"
        return constructed
    return db_url

app.config["SQLALCHEMY_DATABASE_URI"] = get_database_url()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Initialize extensions
db = SQLAlchemy(app, model_class=Base)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to continue using the analyzer.'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

# Create tables
with app.app_context():
    db.create_all()
    logging.info("Database tables created")

# Import routes after app initialization
from app_upgraded import *

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)