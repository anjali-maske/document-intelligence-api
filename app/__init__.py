
import os
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    database_url = (
        f"postgresql+psycopg://{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
    app.config["UPLOAD_FOLDER"] = str(Path(__file__).resolve().parent.parent / "uploads")

    db.init_app(app)

    from app.routes import documents_bp
    from app.models import Document

    app.register_blueprint(documents_bp)

    @app.get("/")
    def home():
        return {"message": "Document Intelligence API is running"}

    @app.get("/health/db")
    def database_health():
        try:
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return {"database": "connected"}, 200
        except Exception:
            app.logger.exception("Database health check failed")
            return {"database": "connection failed"}, 500

    with app.app_context():
        db.create_all()

    
    @app.errorhandler(413)
    def file_too_large(error):
        return {
            "error": "File too large. Maximum allowed size is 10 MB."
        }, 413


    return app
