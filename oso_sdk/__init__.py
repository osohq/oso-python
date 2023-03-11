from typing import Any
import oso_cloud
from .constants import OSO_URL
from .integrations import Integration

__version__ = "0.1.0"

_shared = None


class OsoSdk(oso_cloud.Oso, Integration):
    def __init__(self, api_key: str, optin: bool, exception: Exception | None):
        oso_cloud.Oso.__init__(self, OSO_URL, api_key)
        Integration.__init__(self, optin, exception)

    """TODO

    Args:
        oso_cloud (_type_): _description_
        Integration (_type_): _description_
    """

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        """TODO

        This is trickery for static analyzers

        Raises:
            NotImplementedError: _description_

        Returns:
            Any: _description_
        """
        raise NotImplementedError


class IntegrationConfig:
    """TODO

    Raises:
        NotImplementedError: _description_
    """

    @staticmethod
    def init(api_key: str, optin: bool, exception: Exception | None) -> OsoSdk:
        raise NotImplementedError


def init(
    api_key: str,
    integration: IntegrationConfig,
    shared: bool = True,
    optin: bool = False,
    exception: Exception | None = None,
) -> OsoSdk:
    """TODO

    Create an OsoSdk

    Args:
        api_key (_type_): _description_
        integration (IntegrationConfig): _description_
        shared (bool, optional): _description_. Defaults to True.
        optin (bool, optional): _description_. Defaults to False.
        exception (Exception | None, optional): _description_. Defaults to None.

    Raises:
        RuntimeError: _description_

    Returns:
        OsoSdk: _description_
    """
    if shared:
        global _shared
        if _shared is not None:
            raise RuntimeError(
                "`oso_sdk.init` cannot be called multiple times when shared=True"
            )
        _shared = type(integration).init(api_key, optin, exception)
        return _shared
    else:
        return type(integration).init(api_key, optin, exception)


def global_oso() -> OsoSdk:
    """TODO

    Call this to get the existing global `OsoSdk`

    Raises:
        RuntimeError: the global oso was never initialized

    Returns:
        OsoSdk: _description_
    """
    if _shared is None:
        raise RuntimeError("`oso_sdk.init` must first be called with shared=True")

    return _shared


__all__ = ("init", "global_oso")
