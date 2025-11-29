from flask import Flask
from dotenv import load_dotenv
import os

from extensions import db, login_manager, migrate


def create_app():
    load_dotenv()

    app = Flask(__name__)
    # Configuration
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
    # app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///journal.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "login"

    # ---- IMPORTANT ----
    # Import models AFTER db.init_app()
    import models

    # Register routes AFTER models import
    from routes import register_routes
    register_routes(app)

    return app


# The actual Flask application
app = create_app()


if __name__ == "__main__":
    app.run()
