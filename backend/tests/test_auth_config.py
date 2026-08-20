import os
import unittest
from unittest import mock
from uuid import uuid4

import jwt
from fastapi.security import HTTPAuthorizationCredentials

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_document_rag")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

from app.api.dependencies import auth as auth_module


class AuthConfigRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_current_user_uses_uppercase_jwt_settings(self):
        user_id = uuid4()
        token = jwt.encode({"sub": str(user_id)}, "test-secret-key", algorithm="HS256")

        auth_module.get_user_by_id = mock.AsyncMock(return_value=mock.Mock(id=user_id, is_active=True))

        user = await auth_module.get_current_user(
            credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
            db=mock.AsyncMock(),
        )

        self.assertEqual(user.id, user_id)
        self.assertTrue(user.is_active)


if __name__ == "__main__":
    unittest.main()
