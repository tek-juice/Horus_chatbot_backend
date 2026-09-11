import os
from openai import OpenAI
from dotenv import load_dotenv
import logging
from config.model_engine.vector_search import search_documents
from config.model_engine.memory_service import get_last_assistant_message

load_dotenv()
logger = logging.getLogger(__name__)

# client = OpenAI(
#     base_url="https://integrate.api.nvidia.com/v1",
#     api_key=os.getenv("NVIDIA_API_KEY")
# )

# client = OpenAI(
#     base_url="https://api.x.ai/v1",
#     api_key=os.getenv("XAI_API_KEY")
# )

client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv("GEMINI_API_KEY")
)


# MODEL = "deepseek-ai/deepseek-v4-flash-0731"
# MODEL = "nvidia/nemotron-3.5-lightning-30b-a3b"
# MODEL = "grok-4.6"
MODEL = "gemini-3.8-flash"
# MODEL = "meta/llama-3.2-3b-instruct"
# MODEL = "meta/muse-glimmer-30b"
# MODEL = "nvidia/nemotron-mini-4b-instruct"
# MODEL = "nvidia/nemotron-3-nano-30b-a3b"
# MODEL = "thinkingmachines/inkling"


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

        # Get previous assistant message
        last_assistant_message = get_last_assistant_message(session_id)

        if last_assistant_message:
            logger.info(
                "Previous assistant message found for session=%s",
                session_id
            )
        else:
            logger.info(
                "No previous assistant message found for session=%s",
                session_id
            )

        messages = [
            {
                "role": "system",
                "content": f"""
You are the friendly AI assistant for Horus Music.

Your goal is to have natural, helpful conversations while providing
accurate information about Horus Music.

GENERAL CONVERSATION AND MUSIC KNOWLEDGE

- You may naturally respond to greetings, conversation about music,
  and general questions but ask question at the end about horus music
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

CONVERSATION MEMORY

- Maintain continuity with the previous assistant message.
- The user may answer a question from the previous assistant
  message using a very short response.
- If the user's current message answers the previous assistant's
  question, treat it as a continuation of the conversation.
- Do not repeat questions that the user has already answered.
- Use the previous assistant message to infer the meaning of short
  or incomplete user responses.

CONVERSATION STYLE

- Be warm and natural.
- Don't mention knowledge bases, vector databases, retrieval,
  or technical implementation details.
- Don't unnecessarily repeat that you are an AI.
- Speak as part of Horus Music, using "we", "our", and "us".
- Keep responses concise unless the user asks for more detail.
- Ask a natural follow-up question concerning
  Horus Music.
- Use emojis occasionally when they fit the conversation.

HORUS MUSIC CONTEXT:

{context}
"""
            }
        ]

        # Add previous assistant message to conversation
        if last_assistant_message:
            messages.append({
                "role": "assistant",
                "content": last_assistant_message
            })

        # Add current user message
        messages.append({
            "role": "user",
            "content": question
        })


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
            # extra_body={
            #     "chat_template_kwargs": {
            #     "enable_thinking": False
            # }}
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


