from unittest.mock import patch

import oso_cloud  # type: ignore
import pytest


@pytest.fixture
def mock_oso_allowed():
    """Mock `allowed` response Oso service on `authorize` call"""
    with patch.object(oso_cloud.Oso, "authorize", return_value=True) as _fixture:
        yield _fixture


@pytest.fixture
def mock_oso_denied():
    """Mock `denied` response from Oso service on `authorize` call"""
    with patch.object(oso_cloud.Oso, "authorize", return_value=False) as _fixture:
        yield _fixture


@pytest.fixture
def jwt_token():
    """JWT token with the following components:
    Header {
        "alg": "HS256",
        "typ": "JWT"
    }
    Payload {
        "sub": "1234567890",
        "name": "John Doe",
        "iat": 1516239022
    }
    """
    return (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ"
        ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    )


@pytest.fixture
def test_user():
    return {"type": "User", "id": "1234567890"}


@pytest.fixture
def jwt_payload_malformed(jwt_token):
    """JWT token with invalid payload"""
    parts = jwt_token.split(".")
    parts[1] = parts[1] + "0000"  # append noise to payload
    return ".".join(parts)


@pytest.fixture
def jwt_payload_no_sub():
    """JWT token with the following components:
    Header {
        "alg": "HS256",
        "typ": "JWT"
    }
    Payload {
        "name": "John Doe",
        "iat": 1516239022
    }
    """
    return (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJuYW1lIjoiSm9obiBEb2UiLCJpYXQiOjE1MTYyMzkwMjJ9"
        ".hqWGSaFpvbrXkOWc6lrnffhNWR19W_S1YKFBx2arWBk"
    )
