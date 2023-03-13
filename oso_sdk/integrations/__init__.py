import inspect
import string
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Dict, Optional, Tuple


class ResourceIdKind(Enum):
    LITERAL = 1
    PARAM = 2


@dataclass
class Route:
    action: Optional[str]
    resource_type: Optional[str]
    resource_id: str
    resource_id_kind: ResourceIdKind


def to_resource_type(resource_type: str) -> str:
    return string.capwords(resource_type.replace("_", " ")).replace(" ", "")


class Integration:
    """_summary_"""

    def __init__(self, optin: bool, exception: Optional[Exception]):
        self.routes: Dict[str, Route] = {}
        self._identify_action_from_method = None
        self._identify_user_from_request = None
        self._optin = optin
        self._custom_exception: Optional[Exception] = exception

    def identify_user_from_request(self, f):
        """Override the default function used to identify the "actor" to authorize.

        The type signature of the provided function is Integration specific.

        Args:
            f (_type_): The function that will be used to identify which user
                is being authorized for a given request. This will be called once
                for every authorized request.
        """
        self._identify_user_from_request = f

    def identify_action_from_method(self, f):
        """Override the default function used to identify the "action" to authorize.

        The type signature of the user provided function is Integration specific.

        Args:
            f (_type_): The function that will be used to identify what action
                is being authorized for a given request. This will be called once
                for every authorized request.
        """
        self._identify_action_from_method = f

    def _parse_resource_id(self, resource_id: str) -> Tuple[ResourceIdKind, str]:
        raise NotImplementedError  # pragma: no cover

    def enforce(
        self,
        resource_id: str,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
    ):
        """Add or modify enforcement to an endpoint.

        Args:
            resource_id (str): The resource id to authorize. Usually a route parameter.
            action (Optional[str], optional): Hardcode an action for this route. Defaults to None.
            resource_type (Optional[str], optional): Hardcode a resource_type for this route. Defaults to None.

        Raises:
            ValueError: If `resource_id` is an empty string
        """
        if len(resource_id) == 0:
            raise ValueError("`resource_id` cannot be an empty string")

        resource_id_kind, resource_id = self._parse_resource_id(resource_id)

        def decorator(f):
            self.routes[f.__name__] = Route(
                action,
                resource_type or to_resource_type(f.__name__),
                resource_id,
                resource_id_kind,
            )

            @wraps(f)
            async def decorated_view_async(*args, **kwargs):
                return await f(*args, **kwargs)

            @wraps(f)
            def decorated_view_sync(*args, **kwargs):
                return f(*args, **kwargs)

            if inspect.iscoroutinefunction(f):
                return decorated_view_async
            else:
                return decorated_view_sync

        return decorator
