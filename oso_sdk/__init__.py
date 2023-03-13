from typing import Any, Optional

import oso_cloud  # type: ignore

from .constants import OSO_URL
from .integrations import Integration

__version__ = "0.2.0"

_shared = None


class OsoSdk(oso_cloud.Oso, Integration):
    def __init__(self, api_key: str, optin: bool, exception: Optional[Exception]):
        oso_cloud.Oso.__init__(self, OSO_URL, api_key)
        Integration.__init__(self, optin, exception)

    """A handle to Oso Cloud.

    You should not instantiate this class directly. Use `oso_sdk.init` or
    `oso_sdk.global_oso` instead.
    """

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        """This is trickery for static analyzers.

        Some integrations need to be `Callable` to work nice with their respective
        framework. This prevents static analyzers from complaining that an `OsoSdk`
        instance isn't a callable.
        """
        raise NotImplementedError  # pragma: no cover


class IntegrationConfig:
    """TODO

    Raises:
        NotImplementedError: _description_
    """

    @staticmethod
    def init(api_key: str, optin: bool, exception: Optional[Exception]) -> OsoSdk:
        raise NotImplementedError  # pragma: no cover


def init(
    api_key: str,
    integration: IntegrationConfig,
    shared: bool = True,
    optin: bool = False,
    exception: Optional[Exception] = None,
) -> OsoSdk:
    """Create an instance of the Oso SDK.

    Args:
        api_key (str): An Oso Cloud api key.
        integration (IntegrationConfig): A class implementing `IntegrationConfig`.
            e.g. `FastApiIntegration`, `FlaskIntegration`.
        shared (bool, optional): Create a global `OsoSdk` object that can be accessed
            by subsequent calls to `global_oso()`. Defaults to True.
        optin (bool, optional): Only enforce routes with the `@oso.enforce` decorator.
            Defaults to False.
        exception (Optional[Exception], optional): raise a custom exception on
            authorization failure. Defaults to None.

    Raises:
        RuntimeError: If called multiple times when shared=True
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
    """Get the global `OsoSdk` instance.

    Raises:
        RuntimeError: If the global instance was never initialized by calling
            `oso_sdk.init` must first be called with shared=True.
    """
    if _shared is None:
        raise RuntimeError("`oso_sdk.init` must first be called with shared=True")

    return _shared


__all__ = ("init", "global_oso")
