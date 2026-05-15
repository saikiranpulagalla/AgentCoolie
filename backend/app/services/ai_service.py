"""
AI and embedding services.
"""

import logging
import time
from typing import Any, Optional, List
from app.core.config import settings
from app.services.runtime_config_service import runtime_config_service
from app.services.tracing_service import traceable

logger = logging.getLogger(__name__)

AI_KEY_COOLDOWN_SECONDS = 120


def _error_status_code(error: Exception) -> int | None:
    status = getattr(error, "status_code", None)
    if isinstance(status, int):
        return status
    response = getattr(error, "response", None)
    response_status = getattr(response, "status_code", None)
    return response_status if isinstance(response_status, int) else None


def _ai_error_category(error: Exception) -> str:
    """Classify provider errors so fallback only rotates keys when it can help."""
    status = _error_status_code(error)
    text = str(error).lower()

    if status in {401, 403} or any(term in text for term in (
        "api key not valid",
        "invalid api key",
        "api key expired",
        "unauthenticated",
        "permission denied",
        "forbidden",
        "api_key_invalid",
    )):
        return "key"
    if status in {408, 409, 425, 429, 500, 502, 503, 504}:
        return "retryable"
    if status is not None and 400 <= status < 500:
        return "fatal"
    if any(term in text for term in (
        "quota",
        "rate limit",
        "resource_exhausted",
        "temporarily unavailable",
        "timeout",
        "timed out",
        "overloaded",
        "unavailable",
    )):
        return "retryable"
    if any(term in text for term in (
        "invalid argument",
        "bad request",
        "model not found",
        "unsupported",
        "safety",
    )):
        return "fatal"
    return "retryable"


def _available_keys(api_keys: list[str], cooldowns: dict[str, float]) -> list[str]:
    now = time.monotonic()
    ready = [key for key in api_keys if cooldowns.get(key, 0) <= now]
    if ready:
        return ready
    return [min(api_keys, key=lambda key: cooldowns.get(key, now))]


def _error_summary(error: Exception) -> str:
    text = str(error)
    if len(text) > 180:
        text = f"{text[:177]}..."
    return f"{error.__class__.__name__}: {text}"


class EmbeddingService:
    """Handle embeddings with multiple providers."""

    def __init__(self):
        """Initialize embedding service based on configured provider."""
        self.provider = settings.EMBEDDING_PROVIDER
        self.client = None

        if self.provider == "google":
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
            if self.provider == "google":
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
            if self.provider == "google":
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
        self.model_name = settings.GEMINI_MODEL
        self.vision_model_name = settings.GEMINI_VISION_MODEL
        self._google_key_cooldowns: dict[str, float] = {}
        self._groq_key_cooldowns: dict[str, float] = {}
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
            self.client = genai.GenerativeModel(self.model_name)
            self.vision_model = genai.GenerativeModel(self.vision_model_name)
            logger.info(f"Gemini service initialized with model: {self.model_name}")
        except ImportError:
            logger.warning("Google Generative AI not installed - Gemini will not work")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini: {e}")

    async def _google_api_keys(self, *, vision: bool = False) -> list[str]:
        if vision:
            keys = await runtime_config_service.get_secret_list(
                "GEMINI_VISION_API_KEYS",
                fallback_keys=("GOOGLE_AI_VISION_API_KEY",),
            )
            if keys:
                return keys

        return await runtime_config_service.get_secret_list(
            "GOOGLE_AI_API_KEYS",
            fallback_keys=("GOOGLE_AI_API_KEY", "GOOGLE_AI_API_FALLBACK_KEY"),
        )

    def _generate_with_google(self, model_name: str, content: Any, api_keys: list[str]) -> str:
        """Try configured Google API keys in order."""
        if not api_keys:
            raise RuntimeError("No Google AI API keys configured")

        last_error: Exception | None = None
        import google.generativeai as genai

        keys_to_try = _available_keys(api_keys, self._google_key_cooldowns)
        for api_key in keys_to_try:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(content)
                return response.text
            except Exception as e:
                last_error = e
                category = _ai_error_category(e)
                if category in {"key", "retryable"}:
                    self._google_key_cooldowns[api_key] = time.monotonic() + AI_KEY_COOLDOWN_SECONDS
                key_index = api_keys.index(api_key) + 1 if api_key in api_keys else "?"
                logger.warning("Google AI key #%s failed (%s): %s", key_index, category, _error_summary(e))
                if category == "fatal":
                    raise

        raise last_error or RuntimeError("Google AI generation failed")

    async def _generate_with_groq(self, prompt: str) -> str:
        """Fallback text generation through Groq's OpenAI-compatible API."""
        groq_api_keys = await runtime_config_service.get_secret_list(
            "GROQ_API_KEYS",
            fallback_keys=("GROQ_API_KEY",),
        )
        groq_model = await runtime_config_service.get_secret("GROQ_MODEL", settings.GROQ_MODEL)
        if not groq_api_keys:
            raise RuntimeError("No Groq API key configured")

        last_error: Exception | None = None
        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError("OpenAI SDK is required for Groq fallback") from e

        keys_to_try = _available_keys(groq_api_keys, self._groq_key_cooldowns)
        for groq_api_key in keys_to_try:
            try:
                client = OpenAI(
                    api_key=groq_api_key,
                    base_url="https://api.groq.com/openai/v1",
                )
                response = client.chat.completions.create(
                    model=groq_model or settings.GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                last_error = e
                category = _ai_error_category(e)
                if category in {"key", "retryable"}:
                    self._groq_key_cooldowns[groq_api_key] = time.monotonic() + AI_KEY_COOLDOWN_SECONDS
                key_index = groq_api_keys.index(groq_api_key) + 1 if groq_api_key in groq_api_keys else "?"
                logger.warning("Groq key #%s failed (%s): %s", key_index, category, _error_summary(e))
                if category == "fatal":
                    raise

        raise last_error or RuntimeError("Groq fallback failed")

    @traceable(name="llm.analyze_text", run_type="llm")
    async def analyze_text(self, text: str, prompt: Optional[str] = None) -> str:
        """
        Analyze text with Gemini.

        Args:
            text: Text to analyze (not used if prompt is provided)
            prompt: Custom analysis prompt (should include the text if needed)

        Returns:
            Analysis result
        """
        try:
            # Use the prompt as-is if provided, otherwise use the text
            full_prompt = prompt if prompt else text
            try:
                return self._generate_with_google(self.model_name, full_prompt, await self._google_api_keys())
            except Exception as google_error:
                logger.error(f"Google AI text generation failed across configured keys: {google_error}")
                return await self._generate_with_groq(full_prompt)
        except Exception as e:
            logger.error(f"Failed to analyze text: {e}")
            raise

    @traceable(name="llm.analyze_image", run_type="llm")
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
            try:
                from PIL import Image
            except ImportError as e:
                raise RuntimeError("Image analysis requires Pillow. Install backend requirements and restart the server.") from e
            import io
            import base64

            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))

            full_prompt = prompt or "What's in this image?"
            return self._generate_with_google(
                self.vision_model_name,
                [full_prompt, image],
                await self._google_api_keys(vision=True),
            )
        except Exception as e:
            logger.error(f"Failed to analyze image: {e}")
            raise

    @traceable(name="llm.analyze_audio", run_type="llm")
    async def analyze_audio(
        self,
        audio_base64: str,
        mime_type: str = "audio/webm",
        prompt: Optional[str] = None,
    ) -> str:
        """
        Analyze or answer a short audio recording with Gemini.

        Args:
            audio_base64: Base64 encoded audio bytes
            mime_type: Audio MIME type from the upload
            prompt: Optional user text/instruction to pair with the recording

        Returns:
            Model response
        """
        try:
            import base64
            import google.generativeai as genai

            audio_data = base64.b64decode(audio_base64)
            full_prompt = prompt or (
                "Transcribe this audio message, then answer it as AgentCoolie. "
                "If the user gives a command or asks a question, respond directly."
            )
            return self._generate_with_google(
                self.model_name,
                [
                    full_prompt,
                    {
                        "mime_type": mime_type or "audio/webm",
                        "data": audio_data,
                    },
                ],
                await self._google_api_keys(vision=True),
            )
        except Exception as e:
            logger.error(f"Failed to analyze audio: {e}")
            raise

    async def transcribe_audio(
        self,
        audio_base64: str,
        mime_type: str = "audio/webm",
    ) -> str:
        """Transcribe an audio clip so the normal router can handle the user's intent."""
        return await self.analyze_audio(
            audio_base64,
            mime_type=mime_type,
            prompt=(
                "Transcribe the user's audio message accurately. "
                "Return only the spoken words, without commentary."
            ),
        )


def extract_pdf_text_with_metadata(
    pdf_base64: str,
    max_chars: int = 50000,
    max_pages: int = 25,
) -> dict:
    """Extract readable text and limits metadata from a base64 PDF attachment."""
    try:
        import base64
        import io
        from pypdf import PdfReader

        pdf_bytes = base64.b64decode(pdf_base64)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        parts: list[str] = []
        page_count = len(reader.pages)
        pages_read = min(page_count, max_pages)
        for page in reader.pages[:pages_read]:
            text = page.extract_text() or ""
            if text.strip():
                parts.append(text.strip())
            if sum(len(part) for part in parts) >= max_chars:
                break
        text = "\n\n".join(parts)[:max_chars].strip()
        return {
            "text": text,
            "page_count": page_count,
            "pages_read": pages_read,
            "max_pages": max_pages,
            "max_chars": max_chars,
            "truncated": page_count > pages_read or len("\n\n".join(parts)) > max_chars,
        }
    except ImportError as e:
        raise RuntimeError("PDF analysis requires pypdf. Install backend requirements and restart the server.") from e
    except Exception as e:
        logger.error(f"Failed to extract PDF text: {e}")
        raise


def extract_pdf_text(pdf_base64: str, max_chars: int = 50000, max_pages: int = 25) -> str:
    """Extract readable text from a base64 PDF attachment."""
    return str(extract_pdf_text_with_metadata(pdf_base64, max_chars=max_chars, max_pages=max_pages).get("text") or "")


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
