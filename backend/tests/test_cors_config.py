import importlib
import os
import sys
import unittest
from unittest import mock

from pydantic import ValidationError

VALID_SECRET = "test-only-jwt-secret-key-32-bytes-long"
DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/"
    "ai_document_rag"
)

os.environ.setdefault("DATABASE_URL", DATABASE_URL)
os.environ.setdefault("JWT_SECRET_KEY", VALID_SECRET)

from fastapi.testclient import TestClient

from app.core.config import Settings


class CorsConfigTests(unittest.TestCase):
    def test_frontend_origin_is_allowed(self):
        with mock.patch.dict(
            os.environ,
            {
                "DATABASE_URL": DATABASE_URL,
                "JWT_SECRET_KEY": VALID_SECRET,
            },
            clear=True,
        ):
            sys.modules.pop("app.core.config", None)
            sys.modules.pop("app.main", None)

            import app.core.config as config_module
            importlib.reload(config_module)

            import app.main as main_module
            client = TestClient(main_module.app)
            response = client.options(
                "/auth/login",
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "http://localhost:5173",
        )

    def test_explicit_deployment_origin_is_wired_to_app(self):
        with mock.patch.dict(
            os.environ,
            {
                "DATABASE_URL": DATABASE_URL,
                "JWT_SECRET_KEY": VALID_SECRET,
                "CORS_ORIGINS": "https://app.example.com",
            },
            clear=True,
        ):
            sys.modules.pop("app.core.config", None)
            sys.modules.pop("app.main", None)

            import app.core.config as config_module
            importlib.reload(config_module)

            import app.main as main_module
            client = TestClient(main_module.app)

            response = client.options(
                "/auth/login",
                headers={
                    "Origin": "https://app.example.com",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "https://app.example.com",
        )

    def test_wildcard_origin_is_rejected(self):
        with mock.patch.dict(
            os.environ,
            {
                "DATABASE_URL": DATABASE_URL,
                "JWT_SECRET_KEY": VALID_SECRET,
                "CORS_ORIGINS": "*",
            },
            clear=True,
        ):
            with self.assertRaises(ValidationError):
                Settings()

    def test_credentials_remain_enabled(self):
        with mock.patch.dict(
            os.environ,
            {
                "DATABASE_URL": DATABASE_URL,
                "JWT_SECRET_KEY": VALID_SECRET,
            },
            clear=True,
        ):
            sys.modules.pop("app.main", None)
            import app.main as main_module

            middleware = next(
                item
                for item in main_module.app.user_middleware
                if item.cls.__name__ == "CORSMiddleware"
            )

        self.assertTrue(middleware.kwargs["allow_credentials"])


if __name__ == "__main__":
    unittest.main()
