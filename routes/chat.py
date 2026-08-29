from flasgger import swag_from
from flask import Blueprint, jsonify, request, stream_with_context, Response, send_file
from config.model_engine.model_streamer import stream_answer
from config.chat_services.get_chat_session import get_chat_session
from config.chat_services.save_chat_message import save_chat_message
from config.chat_services.create_chat_session import create_chat_session
from models.users import MessageRole
from config.chat_services.create_user import create_user
from config.chat_services.get_user_by_email import get_user_by_email
import logging
import time

from models.users import ChatSession
from config.helpers.validators import validate_email, validate_name

from config.speech.speech_service import speech_to_text
from config.speech.voice_streamer import generate_voice_answer
import tempfile
import os
from config.limit_config.limiter import limiter
from config.extensions.database_config import db


logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)
speech_bp = Blueprint("speech", __name__, url_prefix="/speech")


@limiter.limit("30 per minute")
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

        if not validate_name(name):
            logger.warning("Chat start failed: Invalid name.")

            return jsonify({
                "success": False,
                "error": "Invalid name. Name must contain more than 2 characters."
            }), 400

        if not validate_email(email):
            logger.warning(
                "Chat start failed: Invalid email."
            )

            return jsonify({
                "success": False,
                "error": "Invalid email format."
            }), 400

        logger.info(f"Looking up user with email: {email}")

        user = get_user_by_email(email)
        if user is None:
            logger.info(f"User not found. Creating new user: {email}")
            user = create_user(name=name, email=email)

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
            "error": "Internal server error."
        }), 500

@limiter.limit("30 per minute")
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

    # Store the database ID before streaming
    session_db_id = session.id

    # Save the user's message before generating a response
    save_chat_message(
        session_id=session_db_id,
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
                    session_id=session_db_id,
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

@limiter.limit("30 per minute")
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

@limiter.limit("30 per minute")
@speech_bp.route("/chat", methods=["POST"])
@swag_from({
    "tags": ["Speech"],
    "summary": "Voice chat with Horus",
    "description": (
        "Accepts an audio recording, transcribes it using "
        "Speech-to-Text, sends the transcription through the "
        "Horus RAG pipeline, converts the response to speech, "
        "and returns the generated audio."
    ),
    "consumes": [
        "multipart/form-data"
    ],
    "produces": [
        "audio/wav"
    ],
    "parameters": [
        {
            "name": "audio",
            "in": "formData",
            "type": "file",
            "required": True,
            "description": "Audio recording from the user."
        },
        {
            "name": "session_id",
            "in": "formData",
            "type": "string",
            "required": True,
            "description": "Horus chat session ID."
        }
    ],
    "responses": {
        "200": {
            "description": "Successfully generated voice response.",
            "content": {
                "audio/wav": {}
            }
        },
        "400": {
            "description": "Audio file or session ID is missing."
        },
        "500": {
            "description": "An error occurred while processing the voice request."
        }
    }
})

def speech_chat():
    request_start = time.perf_counter()

    logger.info("[VOICE] ===============================")
    logger.info("[VOICE] New voice request")
    logger.info("[VOICE] ===============================")

    audio_file = request.files.get("audio")
    session_uuid = request.form.get("session_id")

    if not audio_file:
        return jsonify({
            "success": False,
            "error": "Audio file is required."
        }), 400

    if not session_uuid:
        return jsonify({
            "success": False,
            "error": "A session_id is required."
        }), 400

    audio_path = None

    try:
        start = time.perf_counter()

        audio_temp = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".webm"
        )

        audio_file.save(audio_temp.name)

        audio_path = audio_temp.name

        audio_temp.close()

        logger.info(
            "[VOICE] Audio save: %.2fs",
            time.perf_counter() - start
        )

        question = speech_to_text(audio_path)

        logger.info(
            "[VOICE] STT total from route: %.2fs",
            time.perf_counter() - start
        )

        if not question:
            return jsonify({
                "success": False,
                "error": "Could not understand the audio."
            }), 400

        session = get_chat_session(session_uuid)

        if session is None:

            logger.error(
                "[VOICE] Invalid session: %s",
                session_uuid
            )

            return jsonify({
                "success": False,
                "error": "Invalid chat session."
            }), 400
        
        logger.info(
            "[VOICE] Starting streaming voice response"
        )

        audio_generator = generate_voice_answer(
            session_uuid,
            question
        )

        response = Response(
            stream_with_context(audio_generator),
            mimetype="application/octet-stream"
        )

        response.headers["Cache-Control"] = "no-cache"

        response.headers["X-Accel-Buffering"] = "no"

        return response

    except Exception as e:

        logger.exception(
            "[VOICE] Voice request failed"
        )

        db.session.rollback()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        if audio_path and os.path.exists(audio_path):

            try:

                os.remove(audio_path)

                logger.info(
                    "[VOICE] Temporary audio file removed"
                )

            except Exception:

                logger.exception(
                    "[VOICE] Failed to remove temporary audio"
                )

        logger.info(
            "[VOICE] Request handler finished: %.2fs",
            time.perf_counter() - request_start
        )

    