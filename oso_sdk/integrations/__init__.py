from dataclasses import dataclass
from enum import Enum
from functools import wraps
import inspect
import string
from typing import Dict, Tuple


class ResourceIdKind(Enum):
    LITERAL = 1
    PARAM = 2


@dataclass
class Route:
    action: str | None
    resource_type: str | None
    resource_id: str | None
    resource_id_kind: ResourceIdKind


def to_resource_type(resource_type: str) -> str:
    return string.capwords(resource_type.replace("_", " ")).replace(" ", "")


class Integration:
    """_summary_"""

    def __init__(self, optin: bool, exception: Exception | None):
        self.routes: Dict[str, Route] = {}
        self._identify_action_from_method = None
        self._identify_user_from_request = None
        self._optin = optin
        self._custom_exception: Exception | None = exception

    def identify_user_from_request(self, f):
        """TODO

        Args:
            f (Callable[..., str]): _description_
        """
        self._identify_user_from_request = f

    def identify_action_from_method(self, f):
        """TODO

        Args:
            f (Callable[..., str]): _description_
        """
        self._identify_action_from_method = f

    def _parse_resource_id(self, resource_id: str) -> Tuple[ResourceIdKind, str]:
        raise NotImplementedError

    def enforce(
        self,
        resource_id: str,
        action: str | None = None,
        resource_type: str | None = None,
    ):
        """TODO

        Args:
            resource_id (str): _description_
            action (str | None, optional): _description_. Defaults to None.
            resource_type (str | None, optional): _description_. Defaults to None.

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
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
