from models.users import (
    ChatSession,
    ChatMessage,
    MessageRole
)

from config.extensions.database_config import db
from config.model_engine.model_streamer import stream_answer


def get_chat_session(session_uuid):

    return ChatSession.query.filter_by(
        chat_id=session_uuid
    ).first()


def generate_answer(session_uuid, question):

    session = get_chat_session(session_uuid)

    if session is None:
        raise Exception(
            "Invalid session"
        )


    # Save user message

    db.session.add(
        ChatMessage(
            session_id=session.id,
            role=MessageRole.USER,
            message=question
        )
    )

    db.session.commit()


    # Generate AI response

    answer = ""

    for token in stream_answer(
        session_uuid,
        question
    ):
        answer += token


    # Save assistant response

    db.session.add(
        ChatMessage(
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            message=answer
        )
    )

    db.session.commit()


    return answer