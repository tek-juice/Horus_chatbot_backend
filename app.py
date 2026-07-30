from flask import Flask, jsonify
from config.extensions.database_config import db, migrate
from config.extensions.jwt_config import jwt
import os
import logging
from routes.auth_routes import auth
from routes.documents import document
from routes.chat import chat_bp
from flasgger import Swagger
from dotenv import load_dotenv
from config.logs.logs import setup_logging
from config.helpers.email import mail
from flask_cors import CORS


load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

    # email 
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USE_SSL"] = False
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")

    setup_logging()
    logging.info("Starting Horus Backend Application")

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    # CORS(app, origins=["http://localhost:5173", "http://localhost:5173"])
    CORS(
        app,
        resources={
            r"/*": {
                "origins": "http://localhost:5173"
            }
        },
        supports_credentials=True,
    )

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):

        logging.warning(
            "Expired JWT token used"
        )

        return jsonify({
            "message": "Token expired"
        }),401



    @jwt.invalid_token_loader
    def invalid_token(error):

        logging.warning(
            f"Invalid JWT token: {error}"
        )

        return jsonify({
            "message": "Invalid token"
        }),401



    @jwt.unauthorized_loader
    def missing_token(error):

        logging.warning(
            f"Missing JWT token: {error}"
        )

        return jsonify({
            "message": "Authorization token required"
        }),401
        logging.info("Database and JWT initialized")

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }

    swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Horus API",
        "description": "Horus Chatbot Backend API",
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": (
                "JWT Authorization header using the Bearer scheme.\n\n"
                "Example:\n"
                "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            )
        }
    }
}

    Swagger(
        app,
        config=swagger_config,
        template=swagger_template
    )
    app.register_blueprint(auth)
    app.register_blueprint(document)
    app.register_blueprint(chat_bp)
    logging.info("Routes registered successfully")
    return app

app = create_app()

if __name__ == "__main__":
    logging.info("Running development server")
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )