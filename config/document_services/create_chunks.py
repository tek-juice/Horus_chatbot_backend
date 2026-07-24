# import logging


# logger = logging.getLogger(__name__)

# def create_chunks(text, chunk_size=500):
#     try:
#         logger.info(
#             "Creating document chunks"
#         )

#         words = text.split()
#         chunks=[]
#         for i in range(0, len(words), chunk_size):

#             chunk = " ".join(
#                 words[i:i+chunk_size]
#             )

#             chunks.append(chunk)


#         logger.info(
#             f"Created {len(chunks)} chunks"
#         )


#         return chunks


#     except Exception as e:

#         logger.exception(
#             f"Chunk creation failed: {e}"
#         )

#         raise