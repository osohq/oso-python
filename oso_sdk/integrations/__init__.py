from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, TYPE_CHECKING, Dict


class ResourceIdKind(Enum):
    LITERAL = 1
    PARAM = 2


@dataclass
class Route:
    action: str | None
    resource_type: str | None
    resource_id: str | None
    resource_id_kind: ResourceIdKind


class Integration:
    def __init__(self):
        self.routes: Dict[str, Route] = {}
        self._identify_action_from_method: Callable[..., str] = None
        self._identify_user_from_request: Callable[..., str] = None

    def identify_user_from_request(self, f: Callable[..., str]):
        self._identify_user_from_request = f

    def identify_action_from_method(self, f: Callable[..., str]):
        self._identify_action_from_method = f

    def enforce(
        self,
        resource_id: str,
        action: str | None = None,
        resource_type: str | None = None,
    ):
        raise NotImplementedError


class IntegrationConfig:
    @staticmethod
    def init(url: str, api_key: str):
        raise NotImplementedError
