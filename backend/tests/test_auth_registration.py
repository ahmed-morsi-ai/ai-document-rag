import unittest
from unittest import mock

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.api.routes import auth as auth_module
from app.schemas.auth import UserCreate


RAW_DATABASE_ERROR = "duplicate key value violates unique constraint users_email_key"


def _user_data():
    return UserCreate(
        email="user@example.com",
        password="strong-password",
    )


class RegistrationReliabilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_existing_duplicate_registration_behavior_remains_409(self):
        existing_user = mock.Mock()

        db = mock.AsyncMock()

        with mock.patch.object(
            auth_module,
            "get_user_by_email",
            new=mock.AsyncMock(return_value=existing_user),
        ), mock.patch.object(
            auth_module,
            "create_user",
            new=mock.AsyncMock(),
        ) as mock_create_user:
            with self.assertRaises(HTTPException) as context:
                await auth_module.register(_user_data(), db)

        self.assertEqual(
            context.exception.status_code,
            409,
        )
        self.assertEqual(
            context.exception.detail,
            "Email already registered",
        )
        mock_create_user.assert_not_awaited()
        db.rollback.assert_not_awaited()

    async def test_integrity_error_during_creation_returns_409(self):
        db = mock.AsyncMock()

        integrity_error = IntegrityError(
            "INSERT INTO users ...",
            {},
            Exception(RAW_DATABASE_ERROR),
        )

        with mock.patch.object(
            auth_module,
            "get_user_by_email",
            new=mock.AsyncMock(return_value=None),
        ), mock.patch.object(
            auth_module,
            "create_user",
            new=mock.AsyncMock(side_effect=integrity_error),
        ):
            with self.assertRaises(HTTPException) as context:
                await auth_module.register(_user_data(), db)

        self.assertEqual(
            context.exception.status_code,
            409,
        )
        self.assertEqual(
            context.exception.detail,
            "Email already registered",
        )
        self.assertNotIn(
            RAW_DATABASE_ERROR,
            str(context.exception.detail),
        )

    async def test_integrity_error_triggers_database_rollback(self):
        db = mock.AsyncMock()

        integrity_error = IntegrityError(
            "INSERT INTO users ...",
            {},
            Exception(RAW_DATABASE_ERROR),
        )

        with mock.patch.object(
            auth_module,
            "get_user_by_email",
            new=mock.AsyncMock(return_value=None),
        ), mock.patch.object(
            auth_module,
            "create_user",
            new=mock.AsyncMock(side_effect=integrity_error),
        ):
            with self.assertRaises(HTTPException):
                await auth_module.register(_user_data(), db)

        db.rollback.assert_awaited_once()

    async def test_integrity_error_does_not_leak_raw_database_text(self):
        db = mock.AsyncMock()

        integrity_error = IntegrityError(
            "INSERT INTO users ...",
            {},
            Exception(RAW_DATABASE_ERROR),
        )

        with mock.patch.object(
            auth_module,
            "get_user_by_email",
            new=mock.AsyncMock(return_value=None),
        ), mock.patch.object(
            auth_module,
            "create_user",
            new=mock.AsyncMock(side_effect=integrity_error),
        ):
            with self.assertRaises(HTTPException) as context:
                await auth_module.register(_user_data(), db)

        self.assertNotIn(
            RAW_DATABASE_ERROR,
            str(context.exception),
        )

    async def test_successful_registration_behavior_remains_unchanged(self):
        created_user = mock.Mock()

        db = mock.AsyncMock()

        with mock.patch.object(
            auth_module,
            "get_user_by_email",
            new=mock.AsyncMock(return_value=None),
        ), mock.patch.object(
            auth_module,
            "create_user",
            new=mock.AsyncMock(return_value=created_user),
        ) as mock_create_user:
            result = await auth_module.register(_user_data(), db)

        self.assertIs(result, created_user)
        mock_create_user.assert_awaited_once_with(
            db,
            _user_data(),
        )
        db.rollback.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
