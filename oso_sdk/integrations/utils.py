import base64
import json


def default_get_action_from_method(method: str):
    """Determines CRUD action from HTTP method.

    Returns:
        str: CRUD action.

    Raises:
        ValueError: If method is not supported.
    """
    map = {
        "get": "read",
        "put": "update",
        "patch": "update",
        "post": "create",
        "delete": "delete",
    }

    if method is None:
        raise TypeError("method cannot be None")

    action = map.get(method.lower())
    if action is None:
        raise ValueError(f"method {method} not supported")

    return action


def get_sub_from_jwt(authorization: str):
    """Extracts subject from JWT payload without verification.

    Returns:
        str: The subject of the token.

    Raises:
        ValueError: If the token is invalid in any way.
    """
    if authorization is None:
        raise TypeError("authorization cannot be None")

    parts = authorization.split(".")
    # JWT is composed of three parts: header, payload, signature
    if len(parts) != 3:
        raise ValueError("JWT token is malformed")

    # Pad payload before decoding; '=' is stripped because it's not URL-safe
    encoding = parts[1] + "=" * (len(parts[1]) % 4)
    payload = base64.urlsafe_b64decode(encoding)
    data = json.loads(payload.decode("utf-8"))

    sub = data.get("sub")
    if sub is None:
        raise ValueError("JWT payload missing `sub` field")

    return sub
