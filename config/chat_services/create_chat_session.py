from models.users import ChatSession
from config.extensions.database_config import db


def create_chat_session(user_id):
    session = ChatSession(user_id=user_id)
    db.session.add(session)
    db.session.commit()

    return session