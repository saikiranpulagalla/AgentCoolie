"""
Firebase Admin SDK integration service.
"""

import firebase_admin
from firebase_admin import credentials, auth
from app.core.config import settings
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class FirebaseService:
    """Firebase authentication and admin operations."""

    _instance = None

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize Firebase Admin SDK."""
        if self._initialized:
            return
        self._available = False

        try:
            if settings.FIREBASE_SERVICE_ACCOUNT_JSON and settings.FIREBASE_SERVICE_ACCOUNT_JSON != "{}":
                # Load from JSON string
                service_account = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
                cred = credentials.Certificate(service_account)
            elif settings.FIREBASE_ADMIN_CREDENTIALS_PATH:
                # Load from file path
                cred = credentials.Certificate(settings.FIREBASE_ADMIN_CREDENTIALS_PATH)
            else:
                logger.warning("Firebase credentials not configured - authentication will not work")
                self._initialized = True
                return

            firebase_admin.initialize_app(cred)
            logger.info("Firebase SDK initialized successfully")
            self._available = True
            self._initialized = True
        except Exception as e:
            logger.warning(f"Firebase initialization failed: {e} - authentication will not work until configured")
            # Don't re-raise - allow app to start without Firebase
            self._initialized = True

    def is_ready(self) -> bool:
        """Return whether Firebase Admin is available for token verification."""
        return bool(getattr(self, "_available", False))

    def verify_id_token(self, token: str) -> dict:
        """
        Verify Firebase ID token.

        Args:
            token: Firebase ID token

        Returns:
            Decoded token data including UID

        Raises:
            ValueError: If token is invalid
        """
        try:
            decoded = auth.verify_id_token(token, clock_skew_seconds=60)
            return decoded
        except firebase_admin.auth.InvalidIdTokenError as e:
            logger.warning(f"Invalid ID token: {e}")
            raise ValueError(f"Invalid token: {e}")
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise ValueError(f"Token verification failed: {e}")

    def get_user(self, uid: str) -> Optional[dict]:
        """
        Get user information from Firebase.

        Args:
            uid: Firebase user ID

        Returns:
            User information dict
        """
        try:
            user = auth.get_user(uid)
            return {
                "uid": user.uid,
                "email": user.email,
                "display_name": user.display_name,
                "photo_url": user.photo_url,
            }
        except firebase_admin.auth.UserNotFoundError:
            logger.warning(f"User not found: {uid}")
            return None
        except Exception as e:
            logger.error(f"Failed to get user {uid}: {e}")
            return None

    def create_user(self, email: str, password: str, display_name: Optional[str] = None) -> str:
        """
        Create a new Firebase user.

        Args:
            email: User email
            password: User password
            display_name: Optional display name

        Returns:
            Firebase UID
        """
        try:
            user = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
            )
            logger.info(f"Created Firebase user: {user.uid}")
            return user.uid
        except firebase_admin.auth.EmailAlreadyExistsError:
            raise ValueError(f"Email already exists: {email}")
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise

    def update_user(self, uid: str, **kwargs) -> bool:
        """
        Update Firebase user.

        Args:
            uid: Firebase user ID
            **kwargs: Fields to update (email, password, display_name, photo_url)

        Returns:
            True if successful
        """
        try:
            auth.update_user(uid, **kwargs)
            return True
        except Exception as e:
            logger.error(f"Failed to update user {uid}: {e}")
            raise


# Initialize singleton instance
firebase_service = FirebaseService()
