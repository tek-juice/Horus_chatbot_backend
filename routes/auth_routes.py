import logging
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from flasgger import swag_from
from werkzeug.security import generate_password_hash
from config.extensions.database_config import db
from models.users import User, UserRole, UserStatus
from flask_jwt_extended import create_access_token
from config.helpers.validators import validate_email, validate_name, validate_password
from itsdangerous import URLSafeTimedSerializer
from config.helpers.email import send_password_reset_email
from itsdangerous import (URLSafeTimedSerializer, SignatureExpired, BadSignature)
from config.helpers.helpers import admin_required, super_admin_required, admin_or_super_admin_required

auth =  Blueprint("auth", __name__, url_prefix="/auth")

logger = logging.getLogger(__name__)

# REGISTER ADMIN 
@auth.route("/register-admin", methods=["POST"])
@super_admin_required
@swag_from({
    "tags": ["Super Admin Auth"],
    "summary": "Register admin",
    "description": "Creates a new admin user account.",
    "security": [
        {
            "Bearer": []
        }
    ],
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
        email = data.get("email").strip().lower()
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
@super_admin_required
@swag_from({
    "tags": ["Super Admin Auth"],
    "summary": "Register super admin",
    "description": "Creates a new super admin user account.",
    "security": [
        {
            "Bearer": []
        }
    ],
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
        email = data.get("email").strip().lower()
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
    

# SUPER ADMIN 
@auth.post("/super-admin/login")
@swag_from({
    "tags": ["Super Admin Auth"],
    "summary": "Super admin login",
    "description": "Authenticates a super admin user and returns a JWT access token.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
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
        200: {
            "description": "Login successful",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True
                    },
                    "message": {
                        "type": "string",
                        "example": "Login successful."
                    },
                    "access_token": {
                        "type": "string",
                        "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                    },
                    "user": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "integer",
                                "example": 1
                            },
                            "name": {
                                "type": "string",
                                "example": "Super Admin"
                            },
                            "email": {
                                "type": "string",
                                "format": "email",
                                "example": "superadmin@example.com"
                            },
                            "role": {
                                "type": "string",
                                "example": "super_admin"
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Missing request body, missing credentials, or invalid email",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "Email and password are required."
                    }
                }
            }
        },
        401: {
            "description": "Incorrect email or password",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "Email or password is incorrect."
                    }
                }
            }
        },
        403: {
            "description": "Super admin account is inactive",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "Account is inactive."
                    }
                }
            }
        },
        404: {
            "description": "Super admin account not found",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "Super Admin account not found."
                    }
                }
            }
        },
        500: {
            "description": "Unexpected server error",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "An unexpected error occurred."
                    }
                }
            }
        }
    }
})
def super_admin_login():
    try:
        data = request.get_json()
        if not data:
            logging.warning("Super Admin login attempted without request body.")
            return jsonify({
                "success": False,
                "message": "Request body is required."
            }), 400

        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:

            logging.warning("Super Admin login missing email or password.")

            return jsonify({
                "success": False,
                "message": "Email and password are required."
            }), 400

        if not validate_email(email):

            logging.warning(f"Invalid Super Admin email: {email}")

            return jsonify({
                "success": False,
                "message": "Please enter a valid email address."
            }), 400

        user = User.query.filter_by(
            email=email,
            role=UserRole.SUPER_ADMIN
        ).first()

        if not user:
            logging.warning(
                f"Super Admin account not found: {email}"
            )
            return jsonify({
                "success": False,
                "message": "Super Admin account not found."
            }), 404

        if user.status != UserStatus.ACTIVE:

            logging.warning(
                f"Inactive Super Admin login attempt: {email}"
            )

            return jsonify({
                "success": False,
                "message": "Account is inactive."
            }), 403

        if not user.check_password(password):

            logging.warning(
                f"Incorrect password for Super Admin: {email}"
            )

            return jsonify({
                "success": False,
                "message": "Email or password is incorrect."
            }), 401

        token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "role": user.role.value,
                "email": user.email,
                "name": user.name
            }
        )
        logging.info(
            f"Super Admin '{user.email}' logged in successfully."
        )
        return jsonify({
            "success": True,
            "message": "Login successful.",
            "access_token": token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value
            }
        }), 200

    except Exception as e:
        logging.exception(
            f"Super Admin login error: {e}"
        )
        return jsonify({
            "success": False,
            "error": str(e)
            # "message": "An unexpected error occurred."
        }), 500
    

# ADMIN LOGIN 
@auth.post("/admin/login")
@swag_from({
    "tags": ["Admin Auth"],
    "summary": "Admin login",
    "description": "Authenticates an admin user and returns a JWT access token.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
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
        200: {
            "description": "Login successful",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True
                    },
                    "message": {
                        "type": "string",
                        "example": "Login successful."
                    },
                    "access_token": {
                        "type": "string",
                        "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                    },
                    "user": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "integer",
                                "example": 1
                            },
                            "name": {
                                "type": "string",
                                "example": "Admin User"
                            },
                            "email": {
                                "type": "string",
                                "format": "email",
                                "example": "admin@example.com"
                            },
                            "role": {
                                "type": "string",
                                "example": "admin"
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Missing request body, missing credentials, or invalid email",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "Email and password are required."
                    }
                }
            }
        },
        401: {
            "description": "Incorrect email or password",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "Email or password is incorrect."
                    }
                }
            }
        },
        403: {
            "description": "Admin account is inactive",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "Account is inactive."
                    }
                }
            }
        },
        404: {
            "description": "Admin account not found",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "Admin account not found."
                    }
                }
            }
        },
        500: {
            "description": "Unexpected server error",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "An unexpected error occurred."
                    }
                }
            }
        }
    }
})
def admin_login():
    try:
        data = request.get_json()
        if not data:
            logging.warning("Admin login attempted without request body.")
            return jsonify({
                "success": False,
                "message": "Request body is required."
            }), 400

        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:

            logging.warning("Admin login missing email or password.")

            return jsonify({
                "success": False,
                "message": "Email and password are required."
            }), 400

        if not validate_email(email):
            logging.warning(f"Invalid Admin email: {email}")
            return jsonify({
                "success": False,
                "message": "Please enter a valid email address."
            }), 400
        user = User.query.filter_by(
            email=email,
            role=UserRole.ADMIN
        ).first()

        if not user:
            logging.warning(
                f"Admin account not found: {email}"
            )
            return jsonify({
                "success": False,
                "message": "Admin account not found."
            }), 404

        if user.status != UserStatus.ACTIVE:
            logging.warning(
                f"Inactive Admin login attempt: {email}"
            )
            return jsonify({
                "success": False,
                "message": "Account is inactive."
            }), 403

        if not user.check_password(password):
            logging.warning(
                f"Incorrect password for Admin: {email}"
            )
            return jsonify({
                "success": False,
                "message": "Email or password is incorrect."
            }), 401

        token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "role": user.role.value,
                "email": user.email,
                "name": user.name
            }
        )

        logging.info(
            f"Admin '{user.email}' logged in successfully."
        )

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "access_token": token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value
            }
        }), 200

    except Exception as e:
        logging.exception(
            f"Admin login error: {e}"
        )
        return jsonify({
            "success": False,
            "error": str(e)
            # "message": "An unexpected error occurred."
        }), 500


# SEND LINK TO SUPER ADMIN FORGOT PASSWORD 
@auth.post("/super-admin/forgot-password")
@swag_from({
    "tags": ["Super Admin Auth"],
    "summary": "Send Super Admin forgot password link",
    "description": "Send a password reset link to a Super Admin email address.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["email"],
                "properties": {
                    "email": {
                        "type": "string",
                        "format": "email",
                        "example": "superadmin@example.com",
                        "description": "Registered Super Admin email address."
                    }
                }
            }
        }
    ],
    "responses": {
        200: {
            "description": "Password reset link sent successfully.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "message": {
                        "type": "string",
                        "example": "Password reset link has been sent to your email."
                    }
                }
            }
        },
        400: {
            "description": "Missing request body, missing email, or invalid email.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "message": {
                        "type": "string",
                        "example": "Please enter a valid email address."
                    }
                }
            }
        },
        404: {
            "description": "Super Admin email does not exist.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "message": {
                        "type": "string",
                        "example": "Email does not exist."
                    }
                }
            }
        },
        500: {
            "description": "Unexpected server error.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "message": {
                        "type": "string",
                        "example": "An unexpected error occurred."
                    }
                }
            }
        }
    }
})
def super_admin_forgot_password():

    try:

        data = request.get_json()

        if not data:
            logging.warning("Forgot password called without request body.")
            return jsonify({
                "success": False,
                "message": "Request body is required."
            }), 400

        email = data.get("email", "").strip().lower()

        if not email:

            logging.warning("Forgot password missing email.")

            return jsonify({
                "success": False,
                "message": "Email is required."
            }), 400

        if not validate_email(email):

            logging.warning(f"Invalid email supplied: {email}")

            return jsonify({
                "success": False,
                "message": "Please enter a valid email address."
            }), 400

        user = User.query.filter_by(
            email=email,
            role=UserRole.SUPER_ADMIN
        ).first()

        if not user:

            logging.warning(
                f"Password reset requested for unknown email: {email}"
            )

            return jsonify({
                "success": False,
                "message": "Email does not exist."
            }), 404

        serializer = URLSafeTimedSerializer(
            current_app.config["JWT_SECRET_KEY"]
        )

        token = serializer.dumps(
            user.email,
            salt="password-reset-salt"
        )

        reset_url = (
            f"http://localhost:3000/reset-password/{token}"
        )

        send_password_reset_email(
            user.name,
            user.email,
            reset_url
        )

        logging.info(
            f"Password reset email sent to {email}"
        )

        return jsonify({
            "success": True,
            "message": "Password reset link has been sent to your email."
        }), 200

    except Exception as e:

        logging.exception(
            f"Forgot password error: {e}"
        )

        return jsonify({
            "success": False,
            "error": str(e)
            # "message": "An unexpected error occurred."
        }), 500
    

# CHANGE PASSWORD FOR FORGOT PASSWORD FOR SUPER ADMIN 
@auth.post("/super-admin/reset-password/<token>")
@swag_from({
    "tags": ["Super Admin Auth"],
    "summary": "Reset Super Admin password",
    "description": "Reset a Super Admin password using a valid forgot-password reset token.",
    "parameters": [
        {
            "name": "token",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "Password reset token sent to the Super Admin email."
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["password", "confirm_password"],
                "properties": {
                    "password": {
                        "type": "string",
                        "example": "NewPassword123",
                        "description": "New password. Must be at least 8 characters."
                    },
                    "confirm_password": {
                        "type": "string",
                        "example": "NewPassword123",
                        "description": "Confirmation of the new password."
                    }
                }
            }
        }
    ],
    "responses": {
        200: {
            "description": "Password changed successfully.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "message": {
                        "type": "string",
                        "example": "Password changed successfully."
                    }
                }
            }
        },
        400: {
            "description": "Bad request, invalid token, expired token, or validation error.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "message": {
                        "type": "string",
                        "example": "Passwords do not match."
                    }
                }
            }
        },
        404: {
            "description": "Super Admin user not found.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "message": {
                        "type": "string",
                        "example": "User not found."
                    }
                }
            }
        },
        500: {
            "description": "Unexpected server error.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "message": {
                        "type": "string",
                        "example": "An unexpected error occurred."
                    }
                }
            }
        }
    }
})
def reset_super_admin_password(token):

    try:

        data = request.get_json()

        if not data:

            logging.warning(
                "Reset password called without body."
            )

            return jsonify({
                "success": False,
                "message": "Request body is required."
            }), 400

        password = data.get("password", "")
        confirm_password = data.get(
            "confirm_password",
            ""
        )

        if not password or not confirm_password:

            logging.warning(
                "Password reset missing fields."
            )

            return jsonify({
                "success": False,
                "message": "Password and confirm password are required."
            }), 400

        if password != confirm_password:

            logging.warning(
                "Password confirmation mismatch."
            )

            return jsonify({
                "success": False,
                "message": "Passwords do not match."
            }), 400

        if not validate_password(password):

            logging.warning(
                "Password does not meet security requirements."
            )

            return jsonify({
                "success": False,
                "message": (
                    "Password must be at least 8 characters long and contain "
                    "at least one letter, one number, and one special character."
                )
            }), 400

        serializer = URLSafeTimedSerializer(
            current_app.config["JWT_SECRET_KEY"]
        )

        try:

            email = serializer.loads(
                token,
                salt="password-reset-salt",
                max_age=300
            )

        except SignatureExpired:

            logging.warning(
                "Expired password reset token."
            )

            return jsonify({
                "success": False,
                "message": "Password reset link has expired."
            }), 400

        except BadSignature:

            logging.warning(
                "Invalid password reset token."
            )

            return jsonify({
                "success": False,
                "message": "Invalid password reset link."
            }), 400

        user = User.query.filter_by(
            email=email,
            role=UserRole.SUPER_ADMIN
        ).first()

        if not user:

            logging.warning(
                f"Reset password user not found: {email}"
            )

            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404

        user.set_password(password)

        db.session.commit()

        logging.info(
            f"Super Admin password reset successfully for {email}"
        )

        return jsonify({
            "success": True,
            "message": "Password changed successfully."
        }), 200

    except Exception as e:

        db.session.rollback()

        logging.exception(
            f"Password reset error: {e}"
        )

        return jsonify({
            "success": False,
            "message": "An unexpected error occurred."
        }), 500
    


# SEND LIINK TO  ADMIN FORGOT PASSWORD 
@auth.post("/admin/forgot-password")
@swag_from({
    "tags": ["Admin Auth"],
    "summary": "Send Admin forgot password link",
    "description": "Send a password reset link to a Super Admin email address.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["email"],
                "properties": {
                    "email": {
                        "type": "string",
                        "format": "email",
                        "example": "superadmin@example.com",
                        "description": "Registered Super Admin email address."
                    }
                }
            }
        }
    ],
    "responses": {
        200: {
            "description": "Password reset link sent successfully.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "message": {
                        "type": "string",
                        "example": "Password reset link has been sent to your email."
                    }
                }
            }
        },
        400: {
            "description": "Missing request body, missing email, or invalid email.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "message": {
                        "type": "string",
                        "example": "Please enter a valid email address."
                    }
                }
            }
        },
        404: {
            "description": "Admin email does not exist.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "message": {
                        "type": "string",
                        "example": "Email does not exist."
                    }
                }
            }
        },
        500: {
            "description": "Unexpected server error.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "message": {
                        "type": "string",
                        "example": "An unexpected error occurred."
                    }
                }
            }
        }
    }
})
def admin_forgot_password():

    try:

        data = request.get_json()

        if not data:
            logging.warning("Forgot password called without request body.")
            return jsonify({
                "success": False,
                "message": "Request body is required."
            }), 400

        email = data.get("email", "").strip().lower()

        if not email:

            logging.warning("Forgot password missing email.")

            return jsonify({
                "success": False,
                "message": "Email is required."
            }), 400

        if not validate_email(email):

            logging.warning(f"Invalid email supplied: {email}")

            return jsonify({
                "success": False,
                "message": "Please enter a valid email address."
            }), 400

        user = User.query.filter_by(
            email=email,
            role=UserRole.ADMIN
        ).first()

        if not user:

            logging.warning(
                f"Password reset requested for unknown email: {email}"
            )

            return jsonify({
                "success": False,
                "message": "Email does not exist."
            }), 404

        serializer = URLSafeTimedSerializer(
            current_app.config["JWT_SECRET_KEY"]
        )

        token = serializer.dumps(
            user.email,
            salt="password-reset-salt"
        )

        reset_url = (
            f"http://localhost:3000/reset-password/{token}"
        )

        send_password_reset_email(
            user.name,
            user.email,
            reset_url
        )

        logging.info(
            f"Password reset email sent to {email}"
        )

        return jsonify({
            "success": True,
            "message": "Password reset link has been sent to your email."
        }), 200

    except Exception as e:

        logging.exception(
            f"Forgot password error: {e}"
        )

        return jsonify({
            "success": False,
            "error": str(e)
            # "message": "An unexpected error occurred."
        }), 500
    

# CHANGE PASSWORD FOR FORGOT PASSWORD FOR ADMIN 
@auth.post("/admin/reset-password/<token>")
@swag_from({
    "tags": ["Admin Auth"],
    "summary": "Reset  Admin password",
    "description": "Reset a  Admin password using a valid forgot-password reset token.",
    "parameters": [
        {
            "name": "token",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "Password reset token sent to the Super Admin email."
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["password", "confirm_password"],
                "properties": {
                    "password": {
                        "type": "string",
                        "example": "NewPassword123",
                        "description": "New password. Must be at least 8 characters."
                    },
                    "confirm_password": {
                        "type": "string",
                        "example": "NewPassword123",
                        "description": "Confirmation of the new password."
                    }
                }
            }
        }
    ],
    "responses": {
        200: {
            "description": "Password changed successfully.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "message": {
                        "type": "string",
                        "example": "Password changed successfully."
                    }
                }
            }
        },
        400: {
            "description": "Bad request, invalid token, expired token, or validation error.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "message": {
                        "type": "string",
                        "example": "Passwords do not match."
                    }
                }
            }
        },
        404: {
            "description": "Super Admin user not found.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "message": {
                        "type": "string",
                        "example": "User not found."
                    }
                }
            }
        },
        500: {
            "description": "Unexpected server error.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "message": {
                        "type": "string",
                        "example": "An unexpected error occurred."
                    }
                }
            }
        }
    }
})
def reset_admin_password(token):
    try:
        data = request.get_json()
        if not data:
            logging.warning(
                "Reset password called without body."
            )
            return jsonify({
                "success": False,
                "message": "Request body is required."
            }), 400
        password = data.get("password", "")
        confirm_password = data.get(
            "confirm_password",
            ""
        )

        if not password or not confirm_password:
            logging.warning(
                "Password reset missing fields."
            )
            return jsonify({
                "success": False,
                "message": "Password and confirm password are required."
            }), 400

        if password != confirm_password:
            logging.warning(
                "Password confirmation mismatch."
            )
            return jsonify({
                "success": False,
                "message": "Passwords do not match."
            }), 400

        if not validate_password(password):
            logging.warning(
                "Password does not meet security requirements."
            )
            return jsonify({
                "success": False,
                "message": (
                    "Password must be at least 8 characters long and contain "
                    "at least one letter, one number, and one special character."
                )
            }), 400

        serializer = URLSafeTimedSerializer(
            current_app.config["JWT_SECRET_KEY"]
        )

        try:
            email = serializer.loads(
                token,
                salt="password-reset-salt",
                max_age=300
            )

        except SignatureExpired:
            logging.warning(
                "Expired password reset token."
            )

            return jsonify({
                "success": False,
                "message": "Password reset link has expired."
            }), 400

        except BadSignature:
            logging.warning(
                "Invalid password reset token."
            )

            return jsonify({
                "success": False,
                "message": "Invalid password reset link."
            }), 400

        user = User.query.filter_by(
            email=email,
            role=UserRole.ADMIN
        ).first()

        if not user:
            logging.warning(
                f"Reset password user not found: {email}"
            )

            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404

        user.set_password(password)
        db.session.commit()
        logging.info(
            f"Super Admin password reset successfully for {email}"
        )

        return jsonify({
            "success": True,
            "message": "Password changed successfully."
        }), 200

    except Exception as e:
        db.session.rollback()
        logging.exception(
            f"Password reset error: {e}"
        )
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred."
        }), 500


# SUPER ADMIN FORGOT PASSWORD 
@auth.post("/super-admin-change-password")
@super_admin_required
@swag_from({
    "tags": ["Super Admin Auth"],
    "summary": "Change user password",
    "description": "Changes the authenticated user's password.",
    "security": [
        {
            "Bearer": []
        }
    ],
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["current_password", "new_password", "confirm_password"],
                "properties": {
                    "current_password": {"type": "string", "example": "OldPass123!"},
                    "new_password": {"type": "string", "example": "NewPass123!"},
                    "confirm_password": {"type": "string", "example": "NewPass123!"}
                }
            }
        }
    ],
    "responses": {
        200: {
            "description": "Password changed successfully.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "message": {"type": "string", "example": "Password changed successfully."}
                }
            }
        },
        400: {
            "description": "Invalid password input.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "message": {"type": "string", "example": "Current password is incorrect."}
                }
            }
        },
        500: {
            "description": "Database or unexpected server error.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "message": {"type": "string", "example": "A database error occurred."}
                }
            }
        }
    }
})
def super_admin_change_password():
    try:
        user_id = get_jwt_identity()
        logger.info(f"Password change requested. User ID: {user_id}")
        user = User.query.get(user_id)

        if not user:
            logger.warning(f"User not found. ID: {user_id}")
            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404

        data = request.get_json() or {}
        current_password = data.get("current_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if not all([current_password, new_password, confirm_password]):
            logger.warning(f"Missing password fields. User ID: {user.id}")
            return jsonify({
                "success": False,
                "message": "Current password, new password and confirmation are required."
            }), 400

        if not user.check_password(current_password):
            logger.warning(f"Incorrect current password. User ID: {user.id}")

            return jsonify({
                "success": False,
                "message": "Current password is incorrect."
            }), 400

        if new_password != confirm_password:
            logger.warning(f"Password confirmation mismatch. User ID: {user.id}")

            return jsonify({
                "success": False,
                "message": "Passwords do not match."
            }), 400

        if not validate_password(new_password):
            logger.warning(f"Password validation failed. User ID: {user.id}")

            return jsonify({
                "success": False,
                "message": (
                    "Password must be at least 8 characters long and contain "
                    "an uppercase letter, lowercase letter, number, and special character."
                )
            }), 400

        if user.check_password(new_password):
            logger.warning(f"New password is the same as current password. User ID: {user.id}")

            return jsonify({
                "success": False,
                "message": "New password must be different from the current password."
            }), 400

        user.set_password(new_password)

        db.session.commit()

        logger.info(f"Password changed successfully. User ID: {user.id}")

        return jsonify({
            "success": True,
            "message": "Password changed successfully."
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()

        logger.exception(f"Database error changing password: {str(e)}")

        return jsonify({
            "success": False,
            "message": "A database error occurred."
        }), 500

    except Exception as e:
        db.session.rollback()

        logger.exception(f"Unexpected error changing password: {str(e)}")

        return jsonify({
            "success": False,
            "message": "An unexpected error occurred."
        }), 500
    

# ADMIN CHANGE PASSWORD 
@auth.post("/admin-change-password")
@swag_from({
    "tags": ["Admin Auth"],
    "summary": "Change admin password",
    "description": "Allows an authenticated admin to change their own password.",
    "security": [
        {
            "Bearer": []
        }
    ],
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": [
                    "current_password",
                    "new_password",
                    "confirm_password"
                ],
                "properties": {
                    "current_password": {
                        "type": "string",
                        "example": "OldPass123!"
                    },
                    "new_password": {
                        "type": "string",
                        "example": "NewPass123!"
                    },
                    "confirm_password": {
                        "type": "string",
                        "example": "NewPass123!"
                    }
                }
            }
        }
    ],
    "responses": {
        200: {
            "description": "Password changed successfully.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True
                    },
                    "message": {
                        "type": "string",
                        "example": "Password changed successfully."
                    }
                }
            }
        },
        400: {
            "description": "Invalid password data.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "Current password, new password and confirmation are required."
                    }
                }
            }
        },
        404: {
            "description": "Admin user not found.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "User not found."
                    }
                }
            }
        },
        500: {
            "description": "Database or unexpected server error.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "A database error occurred."
                    }
                }
            }
        }
    }
})
@admin_required
def admin_change_password():
    try:
        user_id = get_jwt_identity()

        logger.info(f"Admin password change requested. User ID: {user_id}")

        user = User.query.get(user_id)

        if not user:
            logger.warning(f"Admin not found. ID: {user_id}")

            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404

        data = request.get_json() or {}

        current_password = data.get("current_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if not all([current_password, new_password, confirm_password]):
            logger.warning(f"Missing password fields. User ID: {user.id}")

            return jsonify({
                "success": False,
                "message": "Current password, new password and confirmation are required."
            }), 400

        if not user.check_password(current_password):
            logger.warning(f"Incorrect current password. User ID: {user.id}")

            return jsonify({
                "success": False,
                "message": "Current password is incorrect."
            }), 400

        if new_password != confirm_password:
            logger.warning(f"Password confirmation mismatch. User ID: {user.id}")

            return jsonify({
                "success": False,
                "message": "Passwords do not match."
            }), 400

        if not validate_password(new_password):
            logger.warning(f"Password validation failed. User ID: {user.id}")

            return jsonify({
                "success": False,
                "message": (
                    "Password must be at least 8 characters long and contain "
                    "an uppercase letter, lowercase letter, number, and special character."
                )
            }), 400

        if user.check_password(new_password):
            logger.warning(f"New password is the same as current password. User ID: {user.id}")

            return jsonify({
                "success": False,
                "message": "New password must be different from the current password."
            }), 400

        user.set_password(new_password)

        db.session.commit()

        logger.info(f"Password changed successfully. User ID: {user.id}")

        return jsonify({
            "success": True,
            "message": "Password changed successfully."
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()

        logger.exception(f"Database error changing admin password: {str(e)}")

        return jsonify({
            "success": False,
            "message": "A database error occurred."
        }), 500

    except Exception as e:
        db.session.rollback()

        logger.exception(f"Unexpected error changing admin password: {str(e)}")

        return jsonify({
            "success": False,
            "message": "An unexpected error occurred."
        }), 500
    

@auth.get("/admins")
@super_admin_required
@swag_from({
    "tags": ["Super Admin Auth"],
    "summary": "Get all admins",
    "description": "Returns a list of all admin users. Requires super admin authentication.",
    "security": [
        {
            "Bearer": []
        }
    ],
    "responses": {
        200: {
            "description": "Admins retrieved successfully.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True
                    },
                    "count": {
                        "type": "integer",
                        "example": 2
                    },
                    "admins": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "integer",
                                    "example": 1
                                },
                                "name": {
                                    "type": "string",
                                    "example": "Admin User"
                                },
                                "email": {
                                    "type": "string",
                                    "example": "admin@example.com"
                                },
                                "status": {
                                    "type": "string",
                                    "example": "active"
                                },
                                "role": {
                                    "type": "string",
                                    "example": "admin"
                                },
                                "created_at": {
                                    "type": "string",
                                    "format": "date-time",
                                    "example": "2026-07-23T10:30:00"
                                },
                                "updated_at": {
                                    "type": "string",
                                    "format": "date-time",
                                    "example": "2026-07-23T10:30:00"
                                }
                            }
                        }
                    }
                }
            }
        },
        401: {
            "description": "Missing or invalid authentication token.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "Missing or invalid token."
                    }
                }
            }
        },
        403: {
            "description": "Super admin access required.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "Super admin access required."
                    }
                }
            }
        }
    }
})
def get_admins():
    try:
        admins = (
            User.query
            .filter(User.role == UserRole.ADMIN)
            .order_by(User.created_at.desc())
            .all()
        )

        logger.info(
            f"Retrieved {len(admins)} admin account(s)."
        )

        return jsonify({
            "success": True,
            "count": len(admins),
            "admins": [
                {
                    "id": admin.id,
                    "name": admin.name,
                    "email": admin.email,
                    "status": admin.status.value,
                    "role": admin.role.value,
                    "created_at": admin.created_at.isoformat(),
                    "updated_at": admin.updated_at.isoformat(),
                }
                for admin in admins
            ]
        }), 200

    except Exception as e:
        logger.exception(
            f"Error retrieving admin accounts: {str(e)}"
        )

        return jsonify({
            "success": False,
            "message": "An unexpected error occurred while retrieving admins."
        }), 500
    
@auth.delete("/admins/<int:admin_id>")
@super_admin_required
@swag_from({
    "tags": ["Super Admin Auth"],
    "summary": "Delete admin",
    "description": "Deletes an admin account by ID. Requires super admin authentication.",
    "security": [
        {
            "Bearer": []
        }
    ],
    "parameters": [
        {
            "name": "admin_id",
            "in": "path",
            "required": True,
            "type": "integer",
            "description": "ID of the admin account to delete.",
            "example": 1
        }
    ],
    "responses": {
        200: {
            "description": "Admin deleted successfully.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True
                    },
                    "message": {
                        "type": "string",
                        "example": "Admin deleted successfully."
                    }
                }
            }
        },
        400: {
            "description": "The selected user is not an admin account.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "Only admin accounts can be deleted."
                    }
                }
            }
        },
        401: {
            "description": "Missing or invalid authentication token.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "Missing or invalid token."
                    }
                }
            }
        },
        403: {
            "description": "Super admin access required.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "Super admin access required."
                    }
                }
            }
        },
        404: {
            "description": "Admin not found.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "Admin not found."
                    }
                }
            }
        },
        500: {
            "description": "Unexpected server error.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "An unexpected error occurred while deleting the admin."
                    }
                }
            }
        }
    }
})
def delete_admin(admin_id):
    try:
        admin = User.query.get(admin_id)

        if not admin:
            logger.warning(
                f"Admin with ID {admin_id} not found."
            )

            return jsonify({
                "success": False,
                "message": "Admin not found."
            }), 404

        if admin.role != UserRole.ADMIN:
            logger.warning(
                f"Attempt to delete non-admin user (ID: {admin_id})."
            )

            return jsonify({
                "success": False,
                "message": "Only admin accounts can be deleted."
            }), 400

        db.session.delete(admin)
        db.session.commit()

        logger.info(
            f"Admin '{admin.email}' (ID: {admin.id}) deleted successfully."
        )

        return jsonify({
            "success": True,
            "message": "Admin deleted successfully."
        }), 200

    except Exception as e:
        db.session.rollback()

        logger.exception(
            f"Error deleting admin {admin_id}: {str(e)}"
        )

        return jsonify({
            "success": False,
            "message": "An unexpected error occurred while deleting the admin."
        }), 500