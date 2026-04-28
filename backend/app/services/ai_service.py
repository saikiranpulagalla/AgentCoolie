"""
AI and embedding services.
"""

import logging
from typing import Optional, List
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Handle embeddings with multiple providers."""

    def __init__(self):
        """Initialize embedding service based on configured provider."""
        self.provider = settings.EMBEDDING_PROVIDER
        self.client = None

        if self.provider == "cohere":
            try:
                import cohere
                self.client = cohere.Client(api_key=settings.COHERE_API_KEY)
                logger.info("Cohere embedding provider initialized")
            except ImportError:
                logger.warning("Cohere not installed - embeddings will not work")
            except Exception as e:
                logger.warning(f"Failed to initialize Cohere: {e}")

        elif self.provider == "google":
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
                logger.info("Google embedding provider initialized")
            except ImportError:
                logger.warning("Google AI not installed - embeddings will not work")
            except Exception as e:
                logger.warning(f"Failed to initialize Google AI: {e}")

        elif self.provider == "openai":
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI embedding provider initialized")
            except ImportError:
                logger.warning("OpenAI not installed - embeddings will not work")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            if self.provider == "cohere":
                response = self.client.embed(texts=[text], model="embed-english-v3.0", input_type="search_document")
                return response.embeddings[0]

            elif self.provider == "google":
                import google.generativeai as genai
                response = genai.embed_content(model="models/embedding-001", content=text)
                return response["embedding"]

            elif self.provider == "openai":
                response = self.client.embeddings.create(input=text, model="text-embedding-3-small")
                return response.data[0].embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            if self.provider == "cohere":
                response = self.client.embed(texts=texts, model="embed-english-v3.0", input_type="search_document")
                return response.embeddings

            elif self.provider == "google":
                import google.generativeai as genai
                embeddings = []
                for text in texts:
                    response = genai.embed_content(model="models/embedding-001", content=text)
                    embeddings.append(response["embedding"])
                return embeddings

            elif self.provider == "openai":
                response = self.client.embeddings.create(input=texts, model="text-embedding-3-small")
                return [item.embedding for item in response.data]

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise


class GeminiService:
    """Google Gemini AI service for text and image analysis."""

    def __init__(self):
        """Initialize Gemini service."""
        self.client = None
        self.vision_model = None
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
            self.client = genai.GenerativeModel("gemini-pro")
            self.vision_model = genai.GenerativeModel("gemini-pro-vision")
            logger.info("Gemini service initialized")
        except ImportError:
            logger.warning("Google Generative AI not installed - Gemini will not work")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini: {e}")

    async def analyze_text(self, text: str, prompt: Optional[str] = None) -> str:
        """
        Analyze text with Gemini.

        Args:
            text: Text to analyze
            prompt: Custom analysis prompt

        Returns:
            Analysis result
        """
        try:
            import google.generativeai as genai
            model = genai.GenerativeModel("gemini-pro")
            full_prompt = f"{prompt}\n\nText: {text}" if prompt else text
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Failed to analyze text: {e}")
            raise

    async def analyze_image(self, image_base64: str, prompt: Optional[str] = None) -> str:
        """
        Analyze image with Gemini.

        Args:
            image_base64: Base64 encoded image
            prompt: Analysis prompt

        Returns:
            Analysis result
        """
        try:
            import google.generativeai as genai
            from PIL import Image
            import io
            import base64

            model = genai.GenerativeModel("gemini-pro-vision")
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))

            full_prompt = prompt or "What's in this image?"
            response = model.generate_content([full_prompt, image])
            return response.text
        except Exception as e:
            logger.error(f"Failed to analyze image: {e}")
            raise


# Service instances - initialize with error handling
embedding_service = None
gemini_service = None

try:
    embedding_service = EmbeddingService()
except Exception as e:
    logger.warning(f"Embedding service initialization failed: {e} - embeddings will not be available")

try:
    gemini_service = GeminiService()
except Exception as e:
    logger.warning(f"Gemini service initialization failed: {e} - Gemini analysis will not be available")
