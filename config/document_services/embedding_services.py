import logging
from fastembed import TextEmbedding


logger = logging.getLogger(__name__)


MODEL_NAME = "BAAI/bge-small-en-v1.5"


try:
    model = TextEmbedding(model_name=MODEL_NAME)

    logger.info(f"Embedding model loaded successfully: {MODEL_NAME}")

except Exception as e:
    logger.exception(f"Failed loading embedding model: {e}")
    raise



def generate_embeddings(chunks):
    try:
        if not chunks:
            logger.warning(
                "No chunks provided for embedding."
            )
            return []
        
        logger.info(f"Generating embeddings for {len(chunks)} chunks.")

        embeddings = list(model.embed(chunks))
        embeddings = [
            embedding.tolist()
            for embedding in embeddings
        ]


        logger.info(f"Successfully generated {len(embeddings)} embeddings.")
        return embeddings


    except Exception as e:
        logger.exception(f"Embedding generation failed: {e}")
        raise