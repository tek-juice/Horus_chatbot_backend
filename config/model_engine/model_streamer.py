import os
from openai import OpenAI
from dotenv import load_dotenv
import logging
from config.model_engine.vector_search import search_documents

load_dotenv()
logger = logging.getLogger(__name__)

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)

MODEL = "meta/llama-3.1-8b-instruct"


def stream_answer(session_id: int, question: str):
    logger.info(f"Starting AI response generation. Session={session_id}")
    try:
        if not question or not question.strip():
            logger.warning("Empty question received.")
            yield "Please provide a question."
            return

        logger.info("Searching documents.")

        results = search_documents(question,top_k=3)


        if not results:
            logger.warning("No relevant documents found.")

        documents = [
            row[0]
            for row in results
        ]
        logger.info(f"Retrieved {len(documents)} document chunks.")

        context = "\n\n".join(
            doc.content[:150]
            for doc in documents
        )

        logger.info(f"Context created. Length={len(context)} characters.")

        messages = [
            {
                "role": "system",
                "content": f"""
You are AI assistant for Horus music.

Use ONLY the context below.

If not found, use general knowledge.

Context:
{context}
"""
            },

            {
                "role": "user",
                "content": question
            }

        ]


        logger.info(
            "Sending request to LLM."
        )

        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.2,
            stream=True,
            timeout=120,
        )


        logger.info( "LLM stream started.")


        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if not delta:
                continue

            token = getattr(delta, "content", None)
            if token:
                yield token

        logger.info("LLM stream completed successfully.")

    except TimeoutError:
        logger.exception("LLM request timed out.")
        yield "The AI service timed out. Please try again."


    except Exception as e:
        logger.exception(f"Unexpected error generating response: {str(e)}")
        yield "An unexpected error occurred while generating a response."