import logging
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from werkzeug.security import generate_password_hash
from config.database_config import db
from models.users import User, UserRole, UserStatus
from config.validators import validate_email, validate_name,validate_password

auth =  Blueprint("auth", __name__, url_prefix="/auth")

logger = logging.getLogger(__name__)

# REGISTER ADMIN 
@auth.route("/register-admin", methods=["POST"])
@swag_from({
    "tags": ["Auth"],
    "summary": "Register admin",
    "description": "Creates a new admin user account.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["name", "email", "password"],
                "properties": {
                    "name": {
                        "type": "string",
                        "example": "Admin User"
                    },
                    "email": {
                        "type": "string",
                        "format": "email",
                        "example": "admin@example.com"
                    },
                    "password": {
                        "type": "string",
                        "format": "password",
                        "example": "Admin@123"
                    }
                }
            }
        }
    ],
    "responses": {
        201: {
            "description": "Admin created successfully",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Admin created successfully"
                    }
                }
            }
        },
        400: {
            "description": "Validation error or missing request body",
            "schema": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "example": "Invalid email format"
                    }
                }
            }
        },
        409: {
            "description": "Email already exists",
            "schema": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "example": "Email already exists"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error"
        }
    }
})
def register_admin():
    try:
        data = request.get_json()

        if not data:
            logger.warning(
                "Admin registration failed: Empty request body"
            )

            return jsonify({
                "error": "Request body is required"
            }), 400


        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        logger.info(
            f"Admin registration attempt: {email}"
        )


        # Validate name
        if not validate_name(name):
            logger.warning(
                "Admin registration failed: Invalid name"
            )
            return jsonify({
                "error": "Name must be at least 4 characters"
            }), 400


        # Validate email
        if not validate_email(email):
            logger.warning(
                f"Invalid email format: {email}"
            )

            return jsonify({
                "error": "Invalid email format"
            }), 400

        # Validate password
        if not validate_password(password):
            logger.warning(
                f"Weak password attempt: {email}"
            )
            return jsonify({
                "error": "Password must contain 8+ characters, letters, numbers and special characters"
            }), 400
        
        # Check existing user
        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            logger.warning(
                f"Email already exists: {email}"
            )
            return jsonify({
                "error": "Email already exists"
            }), 409

        # Create admin
        admin = User(name=name, email=email, password_hash=generate_password_hash(password),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_registered=True
        )

        db.session.add(admin)
        db.session.commit()
        logger.info(
            f"Admin created successfully: {email}"
        )
        return jsonify({
            "message": "Admin created successfully"
        }), 201



    except Exception as e:
        db.session.rollback()
        logger.exception(
            f"Unexpected error creating admin: {str(e)}"
        )
        return jsonify({
            "error": "Internal server error"
        }), 500
    
# REGISTER SUPER ADMIN
@auth.route("/register-super-admin", methods=["POST"])
@swag_from({
    "tags": ["Auth"],
    "summary": "Register super admin",
    "description": "Creates a new super admin user account.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["name", "email", "password"],
                "properties": {
                    "name": {
                        "type": "string",
                        "example": "Super Admin"
                    },
                    "email": {
                        "type": "string",
                        "format": "email",
                        "example": "superadmin@example.com"
                    },
                    "password": {
                        "type": "string",
                        "format": "password",
                        "example": "SuperAdmin@123"
                    }
                }
            }
        }
    ],
    "responses": {
        201: {
            "description": "Super admin created successfully",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Super admin created successfully"
                    }
                }
            }
        },
        400: {
            "description": "Validation error or missing request body",
            "schema": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "example": "Invalid email"
                    }
                }
            }
        },
        409: {
            "description": "Email already exists",
            "schema": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "example": "Email already exists"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "schema": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "example": "Internal server error"
                    }
                }
            }
        }
    }
})
def register_super_admin():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "Request body is required"
            }), 400

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")


        if not validate_name(name):
            return jsonify({
                "error": "Invalid name"
            }), 400


        if not validate_email(email):
            return jsonify({
                "error": "Invalid email"
            }), 400


        if not validate_password(password):
            return jsonify({
                "error": "Weak password"
            }), 400


        if User.query.filter_by(email=email).first():
            return jsonify({
                "error": "Email already exists"
            }), 409



        super_admin = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=UserRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE,
            is_registered=True
        )
        db.session.add(super_admin)
        db.session.commit()
        logger.info(
            f"Super admin created: {email}"
        )


        return jsonify({
            "message": "Super admin created successfully"
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.exception(
            f"Error creating super admin: {str(e)}"
        )
        return jsonify({
            "error": "Internal server error"
        }), 500