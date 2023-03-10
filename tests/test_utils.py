import pytest
from oso_sdk.integrations.utils import get_sub_from_jwt
from oso_sdk.exceptions import OsoSdkInternalError


def test_jwt_payload_malformed(jwt_payload_malformed):
    with pytest.raises(OsoSdkInternalError):
        get_sub_from_jwt(jwt_payload_malformed)


def test_jwt_payload_missing_sub(jwt_payload_no_sub):
    with pytest.raises(OsoSdkInternalError):
        get_sub_from_jwt(jwt_payload_no_sub)
