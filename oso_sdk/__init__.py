from typing import TYPE_CHECKING

__version__ = "0.1.0"

_shared = None

if TYPE_CHECKING:
    import oso_cloud
    from .integrations import Integration, IntegrationConfig

    class ClientConstructor(oso_cloud.Oso, Integration):
        pass

    # Make static analyzers think `init` and `oso` have the desired return and
    # argument types for nicer autocompletion of params.
    class init(ClientConstructor):
        def __init__(
            self,
            api_key: str,
            integration: IntegrationConfig,
            shared: bool = True,
            optin: bool = False,
            exception: Exception | None = None,
        ):
            pass

    class oso(ClientConstructor):
        def __init__(self):
            pass

else:
    # Alias `init and `oso` for actual usage.
    def init(
        api_key,
        integration,
        shared: bool = True,
        optin: bool = False,
        exception: Exception | None = None,
    ):
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

    def oso():
        if _shared is None:
            raise RuntimeError("`oso_sdk.init` must first be called with shared=True")

        return _shared


__all__ = ("init", "oso")
