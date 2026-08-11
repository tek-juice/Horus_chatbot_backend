# import logging
# from models.users import ChatMessage, MessageRole
# from config.extensions.database_config import db

# logger = logging.getLogger(__name__)


# def get_last_assistant_message(session_id: int):
#     logger.info(
#         f"Fetching last assistant message. Session={session_id}"
#     )
#     try:
#         message = (
#             ChatMessage.query
#             .filter(
#                 ChatMessage.session_id == session_id,
#                 ChatMessage.role == MessageRole.ASSISTANT
#             )
#             .order_by(ChatMessage.created_at.desc())
#             .first()
#         )

#         if not message:
#             return None

#         return {
#             "id": message.id,
#             "message": message.message,
#             "created_at": message.created_at
#         }

#     except Exception as e:
#         logger.exception(
#             f"Error fetching last assistant message: "
#             f"Session={session_id}: {str(e)}"
#         )
#         raise