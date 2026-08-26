from models.users import ChatSession, ChatMessage, MessageRole
from config.extensions.database_config import db
from config.model_engine.model_streamer import stream_answer

def get_chat_session(session_uuid):

    return ChatSession.query.filter_by(
        chat_id=session_uuid
    ).first()

def generate_answer(session_uuid, question):
    session = get_chat_session(session_uuid)

    if session is None:
        raise Exception("Invalid session")

    try:
        user_message = ChatMessage(
            session_id=session.id,
            role=MessageRole.USER,
            message=question
        )

        db.session.add(user_message)
        db.session.commit()

        answer = ""

        for token in stream_answer(
            session_uuid,
            question
        ):
            answer += token

        if answer.strip():
            assistant_message = ChatMessage(
                session_id=session.id,
                role=MessageRole.ASSISTANT,
                message=answer
            )
            db.session.add(assistant_message)
            db.session.commit()


        return answer

    except Exception:
        db.session.rollback()
        raise