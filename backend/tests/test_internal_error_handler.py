import logging
from unittest import mock

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.main import app
from app.services.chat_factory import get_chat_service


GENERIC_ERROR_DETAIL = "Internal server error"
RAW_EXCEPTION_MESSAGE = "simulated secret internal failure"


def _fake_user():
    return mock.Mock(
        id="00000000-0000-0000-0000-000000000001",
        is_active=True,
    )


def _client():
    return TestClient(
        app,
        raise_server_exceptions=False,
    )


def setup_function():
    app.dependency_overrides.clear()


def teardown_function():
    app.dependency_overrides.clear()


def test_unexpected_runtime_error_returns_safe_500():
    fake_chat_service = mock.Mock()
    fake_chat_service.chat.side_effect = RuntimeError(
        RAW_EXCEPTION_MESSAGE
    )

    app.dependency_overrides[get_current_user] = _fake_user
    app.dependency_overrides[get_chat_service] = (
        lambda: fake_chat_service
    )

    response = _client().post(
        "/chat",
        json={"query": "hello", "top_k": 5},
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": GENERIC_ERROR_DETAIL,
    }
    assert RAW_EXCEPTION_MESSAGE not in response.text


def test_unexpected_error_is_logged_without_request_secrets():
    fake_chat_service = mock.Mock()
    fake_chat_service.chat.side_effect = RuntimeError(
        RAW_EXCEPTION_MESSAGE
    )

    app.dependency_overrides[get_current_user] = _fake_user
    app.dependency_overrides[get_chat_service] = (
        lambda: fake_chat_service
    )

    with mock.patch.object(
        logging.getLogger("app.main"),
        "exception",
    ) as mock_logger:
        response = _client().post(
            "/chat",
            headers={
                "Authorization": "Bearer test-token-value",
            },
            json={"query": "hello", "top_k": 5},
        )

    assert response.status_code == 500
    assert response.json() == {
        "detail": GENERIC_ERROR_DETAIL,
    }

    mock_logger.assert_called_once()
    assert "test-token-value" not in str(mock_logger.call_args)
    assert RAW_EXCEPTION_MESSAGE not in str(mock_logger.call_args)


def test_existing_http_exception_behavior_remains_unchanged():
    response = _client().post(
        "/chat",
        json={"query": "hello", "top_k": 5},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_existing_validation_behavior_remains_unchanged():
    app.dependency_overrides[get_current_user] = _fake_user

    fake_chat_service = mock.Mock()
    app.dependency_overrides[get_chat_service] = (
        lambda: fake_chat_service
    )

    response = _client().post(
        "/chat",
        json={"top_k": 5},
    )

    assert response.status_code == 422
    assert "detail" in response.json()
    assert isinstance(response.json()["detail"], list)


def test_existing_authentication_behavior_remains_unchanged():
    response = _client().post(
        "/chat",
        json={"query": "hello", "top_k": 5},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_cors_middleware_remains_functional():
    response = _client().get(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:5173"
    )
    assert response.headers["access-control-allow-credentials"] == "true"
