import base64
import json
from typing import Optional

from ..exceptions import OsoSdkInternalError


def default_get_action_from_method(method: Optional[str]):
    """Determines CRUD action from HTTP method.

    Returns:
        str: CRUD action.

    Raises:
        ValueError: If method is not supported.
    """
    map = {
        "get": "view",
        "put": "update",
        "patch": "update",
        "post": "create",
        "delete": "delete",
    }

    if method is None:
        raise OsoSdkInternalError("method cannot be None")

    action = map.get(method.lower())
    if action is None:
        raise OsoSdkInternalError(f"method {method} not supported")

    return action


def get_sub_from_jwt(authorization: Optional[str]):
    """Extracts subject from JWT payload without verification.

    Returns:
        str: The subject of the token.

    Raises:
        ValueError: If the token is invalid in any way.
    """
    if authorization is None:
        raise OsoSdkInternalError("authorization cannot be None")

    parts = authorization.split(".")
    # JWT is composed of three parts: header, payload, signature
    if len(parts) != 3:
        raise OsoSdkInternalError("JWT token is malformed")

    # Pad payload before decoding; '=' is stripped because it's not URL-safe
    encoding = parts[1] + "=" * (len(parts[1]) % 4)
    try:
        payload = base64.urlsafe_b64decode(encoding)
        data = json.loads(payload.decode("utf-8"))
    except UnicodeDecodeError as e:
        raise OsoSdkInternalError("JWT payload can't be decoded") from e

    sub = data.get("sub")
    if sub is None:
        raise OsoSdkInternalError("JWT payload missing `sub` field")

    return sub
