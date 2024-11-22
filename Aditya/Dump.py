import openai
from config import Config
from loguru import logger

openai.api_key = Config.OPENAI_API_KEY

def generate_embedding(text):
    """
    Generate embeddings using OpenAI.
    :param text: Text for embedding generation
    :return: Embedding vector
    """
    try:
        response = openai.Embedding.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response["data"][0]["embedding"]
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise
