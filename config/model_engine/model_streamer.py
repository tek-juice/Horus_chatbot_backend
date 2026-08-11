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

# client = OpenAI(
#     base_url="https://models.github.ai/inference",
#     api_key=os.getenv("GITHUB_TOKEN")
# )

MODEL = "deepseek-ai/deepseek-v4-flash-0731"


def stream_answer(session_id: int, question: str):
    logger.info(f"Starting AI response generation. Session={session_id}")
    try:
        if not question or not question.strip():
            logger.warning("Empty question received.")
            yield "Please provide a question."
            return

        logger.info("Searching documents.")

        results = search_documents(question,top_k=3, similarity_threshold=0.50)


        if not results:
            logger.warning("No relevant documents found.")

        documents = [
            row[0]
            for row in results
        ]
        logger.info(f"Retrieved {len(documents)} document chunks.")

        context = "\n\n--- DOCUMENT CHUNK ---\n\n".join(
            doc.content
            for doc in documents
        )

        logger.info(f"Context created. Length={len(context)} characters.")

        messages = [
            {
                "role": "system",
                "content": f"""
You are the friendly AI assistant for Horus Music.

Your goal is to have natural, helpful conversations while providing
accurate information about Horus Music.

There are two kinds of information you can provide:

GENERAL CONVERSATION AND MUSIC KNOWLEDGE
- You may naturally respond to greetings, casual conversation about music,
  small talk, and general questions about music.
- You may provide general music advice and general music-industry
  knowledge.
- Be conversational, friendly, concise, and helpful.

HORUS MUSIC INFORMATION
- For questions specifically about Horus Music, its services,
  pricing, packages, policies, people, history, partnerships,
  or operations, use ONLY the provided Horus Music context.
- Never use general knowledge to invent or guess facts about
  Horus Music.
- Never speculate about Horus Music.
- If the requested Horus Music information is not in the context,
  say:
  "I don't have enough information about that in my current
  Horus Music resources to give you an accurate answer."

CONVERSATION STYLE
- Be warm and natural.
- Don't mention "knowledge base", "vector database", "context",
  "retrieval", or technical implementation details unless the
  user specifically asks about them.
- Don't unnecessarily repeat that you are an AI.
- Speak as part of Horus Music, using "we", "our", and "us" when
  referring to the company.
- Do not refer to Horus Music as "they", "them", or "the company"
  when speaking about our services or operations. For example:
  "We provide music distribution services."
  "Our VEVO Starter package..."
  "We have offices in..."
- Keep responses concise unless the user asks for more detail.
- When appropriate, ask a natural follow-up question cocerning horus music.
- Use emojis occasionally when they fit the conversation.
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
            top_p=0.7,
            max_tokens=1024,
            stream=True,
            timeout=120.0,
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