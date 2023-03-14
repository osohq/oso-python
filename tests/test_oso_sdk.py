from typing import Optional, Tuple

import oso_sdk
import pytest
from oso_sdk import IntegrationConfig, OsoSdk
from oso_sdk.integrations import ResourceIdKind


class _TestIntegration(OsoSdk):
    def _parse_resource_id(self, resource_id: str) -> Tuple[ResourceIdKind, str]:
        return (ResourceIdKind.LITERAL, "TEST")


class TestIntegration(IntegrationConfig):
    @staticmethod
    def init(api_key: str, optin: bool, exception: Optional[Exception]) -> OsoSdk:
        return _TestIntegration(api_key=api_key, optin=optin, exception=exception)


def test_global_oso_sdk():
    with pytest.raises(RuntimeError):
        oso = oso_sdk.global_oso()

    oso = oso_sdk.init("TEST_API_KEY", TestIntegration(), shared=True)
    copy = oso_sdk.global_oso()

    assert type(oso).__name__ == "_TestIntegration"
    assert oso == copy

    with pytest.raises(RuntimeError):
        oso_sdk.init("TEST_API_KEY", TestIntegration(), shared=True)

    # Instantiating a local instance is okay
    local = oso_sdk.init("TEST_API_KEY", TestIntegration(), shared=False)
    assert oso != local
    assert type(local).__name__ == "_TestIntegration"
