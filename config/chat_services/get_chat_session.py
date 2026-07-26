from models.users import ChatSession

def get_chat_session(chat_id):
    return ChatSession.query.filter_by(
        chat_id=chat_id
    ).first()