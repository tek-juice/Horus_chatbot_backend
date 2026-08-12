import logging

from models.users import ChatSession, ChatMessage, MessageRole


logger = logging.getLogger(__name__)


def get_last_assistant_message(chat_id):
    logger.info(
        "Fetching last assistant message for chat_id=%s",
        chat_id
    )

    try:
        session = ChatSession.query.filter_by(chat_id=chat_id).first()

        if not session:
            logger.warning(
                "Chat session not found. chat_id=%s",
                chat_id
            )
            return None

        message = (
            ChatMessage.query
            .filter_by(
                session_id=session.id,
                role=MessageRole.ASSISTANT
            )
            .order_by(ChatMessage.created_at.desc())
            .first()
        )

        if not message:
            logger.info(
                "No previous assistant message for chat_id=%s",
                chat_id
            )
            return None

        return message.message

    except Exception:
        logger.exception(
            "Error fetching last assistant message for chat_id=%s",
            chat_id
        )
        return None