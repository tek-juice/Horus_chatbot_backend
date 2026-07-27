from flasgger import swag_from
from flask import Blueprint, jsonify, request, stream_with_context, Response
from config.model_engine.model_streamer import stream_answer
from config.chat_services.get_chat_session import get_chat_session
from config.chat_services.save_chat_message import save_chat_message
from config.chat_services.create_chat_session import create_chat_session
from models.users import MessageRole
from config.chat_services.create_user import create_user
from config.chat_services.get_user_by_email import get_user_by_email
import logging
from models.users import ChatMessage, ChatSession

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat/start", methods=["POST"])
@swag_from({
    "tags": ["Chatbot"],
    "summary": "Start a new chatbot session",
    "description": (
        "Creates or retrieves a chatbot user using their name and email, "
        "then creates a new chat session and returns its unique session ID."
    ),
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": [
                    "name",
                    "email"
                ],
                "properties": {
                    "name": {
                        "type": "string",
                        "example": "John Doe"
                    },
                    "email": {
                        "type": "string",
                        "example": "john@example.com"
                    }
                }
            }
        }
    ],
    "responses": {
        "201": {
            "description": "Chat session created successfully."
        },
        "400": {
            "description": "Validation error."
        },
        "500": {
            "description": "Internal server error."
        }
    }
})
def start_chat():
    try:
        logger.info("Starting new chat session.")
        data = request.get_json() or {}
        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()

        if not name:
            logger.warning("Chat start failed: Name not provided.")

            return jsonify({
                "success": False,
                "error": "Name is required."
            }), 400

        if not email:
            logger.warning("Chat start failed: Email not provided.")

            return jsonify({
                "success": False,
                "error": "Email is required."
            }), 400

        logger.info(f"Looking up user with email: {email}")
        user = get_user_by_email(email)

        if user is None:
            logger.info(f"User not found. Creating new user: {email}")
            user = create_user(
                name=name,
                email=email
            )
        else:
            logger.info(f"Existing user found. User ID: {user.id}")

        logger.info(f"Creating chat session for user ID: {user.id}")
        session = create_chat_session(user.id)
        logger.info(f"Chat session created successfully. Session ID: {session.chat_id}")

        return jsonify({
            "success": True,
            "message": "Chat session started successfully.",
            "session_id": session.chat_id,
            "name": user.name,
            "email": user.email
        }), 201

    except Exception as e:
        logger.exception("Failed to start chat session.")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@chat_bp.route("/chat", methods=["POST"])
@swag_from({
    "tags": ["Chatbot"],
    "summary": "Ask the AI assistant a question",
    "description": (
        "Uses pgvector retrieval + NVIDIA LLM to answer questions based "
        "on your knowledge base. The user's message and assistant's reply "
        "are automatically stored in the chat history."
    ),
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "example": "ef8f03d2-2b70-43ba-b9e0-5b6a9f02f403"
                    },
                    "question": {
                        "type": "string",
                        "example": "What services does Horus provide?"
                    }
                },
                "required": [
                    "session_id",
                    "question"
                ]
            }
        }
    ],
    "responses": {
        "200": {
            "description": "Streaming AI response"
        },
        "400": {
            "description": "Question or session ID missing"
        },
        "404": {
            "description": "Chat session not found"
        },
        "500": {
            "description": "Internal server error"
        }
    }
})
def chat():
    data = request.get_json() or {}

    question = data.get("question", "").strip()
    session_uuid = data.get("session_id")

    if not question:
        return jsonify({
            "success": False,
            "error": "A question is required."
        }), 400

    if not session_uuid:
        return jsonify({
            "success": False,
            "error": "A session_id is required."
        }), 400

    # Retrieve the chat session
    session = get_chat_session(session_uuid)

    if session is None:
        return jsonify({
            "success": False,
            "error": "Invalid or expired chat session."
        }), 404

    # Save the user's message before generating a response
    save_chat_message(
        session_id=session.id,
        role=MessageRole.USER,
        message=question
    )

    def generate():
        """
        Streams the assistant response while building the
        complete message for storage.
        """

        full_response = ""

        try:
            for token in stream_answer(session_uuid, question):
                full_response += token
                yield token

        finally:
            # Save the assistant response only if one exists
            if full_response.strip():
                save_chat_message(
                    session_id=session.id,
                    role=MessageRole.ASSISTANT,
                    message=full_response
                )

    return Response(
        stream_with_context(generate()),
        mimetype="text/plain",
        headers={
            "X-Accel-Buffering": "no",
        },
    )

@chat_bp.route("/messages/<string:chat_id>", methods=["GET"])
@swag_from({
    "tags": ["Chatbot"],
    "summary": "Fetch chat messages for a session",
    "description": "Retrieves all chat messages belonging to a chat session ordered chronologically.",
    "parameters": [
        {
            "name": "session_uuid",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "Unique session UUID"
        }
    ],
    "responses": {
        200: {
            "description": "Messages retrieved successfully",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True
                    },
                    "messages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "integer",
                                    "example": 1
                                },
                                "role": {
                                    "type": "string",
                                    "example": "USER"
                                },
                                "message": {
                                    "type": "string",
                                    "example": "Hello"
                                },
                                "created_at": {
                                    "type": "string",
                                    "format": "date-time",
                                    "example": "2026-07-27T10:15:20Z"
                                }
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Session not found"
        },
        500: {
            "description": "Internal server error"
        }
    }
})
def get_session_messages(chat_id):
    logger.info("Fetching chat messages for chat_id=%s", chat_id)

    try:
        session = ChatSession.query.filter_by(chat_id=chat_id).first()

        if not session:
            logger.warning("Chat session not found. chat_id=%s", chat_id)
            return jsonify({
                "success": False,
                "error": "Chat session not found."
            }), 404

        messages = session.messages
        logger.info(
            "Retrieved %d messages for chat_id=%s",
            len(messages),
            chat_id
        )

        return jsonify({
            "success": True,
            "messages": [
                {
                    "id": message.id,
                    "role": message.role.value,
                    "message": message.message,
                    "created_at": message.created_at.isoformat() + "Z"
                }
                for message in messages
            ]
        }), 200

    except Exception as e:
        logger.exception(
            "Error fetching chat messages for chat_id=%s",
            chat_id
        )

        return jsonify({
            "success": False,
            "error": "An unexpected error occurred while fetching chat messages."
        }), 500

    