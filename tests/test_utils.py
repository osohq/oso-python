import pytest
from oso_sdk.exceptions import OsoSdkInternalError
from oso_sdk.integrations.utils import default_get_action_from_method, get_sub_from_jwt


def test_invalid_authorize_header():
    with pytest.raises(OsoSdkInternalError):
        get_sub_from_jwt(None)

    with pytest.raises(OsoSdkInternalError):
        get_sub_from_jwt("TEST")


def test_jwt_payload_malformed(jwt_payload_malformed):
    with pytest.raises(OsoSdkInternalError):
        get_sub_from_jwt(jwt_payload_malformed)


def test_jwt_payload_missing_sub(jwt_payload_no_sub):
    with pytest.raises(OsoSdkInternalError):
        get_sub_from_jwt(jwt_payload_no_sub)


@pytest.mark.parametrize(
    "method,action",
    [
        ("get", "view"),
        ("put", "update"),
        ("patch", "update"),
        ("post", "create"),
        ("delete", "delete"),
    ],
)
def test_default_get_action_from_method(method, action):
    assert default_get_action_from_method(method) == action


def test_unsupported_method():
    with pytest.raises(OsoSdkInternalError):
        default_get_action_from_method(None)

    with pytest.raises(OsoSdkInternalError):
        default_get_action_from_method("head")
