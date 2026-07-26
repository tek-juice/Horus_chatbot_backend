from config.extensions.database_config import db
from models.users import ChatMessage


def save_chat_message(session_id, role, message):
    chat_message = ChatMessage(
        session_id=session_id,
        role=role,
        message=message
    )

    db.session.add(chat_message)
    db.session.commit()

    return chat_message