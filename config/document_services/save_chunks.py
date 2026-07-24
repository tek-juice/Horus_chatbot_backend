# from models.document import DocumentChunk
# from config.extensions.database_config import db
# import logging

# logger = logging.getLogger(__name__)


# def save_chunks(document_id, chunks, embeddings):

#     try:

#         for index, chunk in enumerate(chunks):

#             record = DocumentChunk(
#                 document_id=document_id,
#                 chunk_number=index,
#                 content=chunk,
#                 embedding=embeddings[index]
#             )

#             db.session.add(record)


#         db.session.commit()


#     except Exception as e:

#         db.session.rollback()

#         logger.exception(
#             f"Saving chunks failed: {e}"
#         )

#         raise