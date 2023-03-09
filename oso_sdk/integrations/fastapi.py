import inspect
from typing import Any, Callable, Tuple
from fastapi import Request
from . import (
    Integration,
    IntegrationConfig,
    ResourceIdKind,
    constants,
    to_resource_type,
    utils,
)
import oso_cloud
import re
from starlette.concurrency import run_in_threadpool


# from starlette.routing import PARAM_REGEX
# Copy instead of import as a safeguard against future changes to the pattern
# Match parameters in URL paths, eg. '{param}', and '{param:int}'
_PARAM_REGEX = re.compile(
    r"""
        {
            (?P<param>[a-zA-Z_][a-zA-Z0-9_]*)   # param name
            (:[a-zA-Z_][a-zA-Z0-9_]*)?          # optional converter
        }
    """,
    re.VERBOSE,
)


class _FastApiIntegration(oso_cloud.Oso, Integration):
    def __init__(self, url: str, api_key: str):
        oso_cloud.Oso.__init__(self, url, api_key)
        Integration.__init__(self)

    async def __call__(self, request: Request):
        r = self.routes.get(request["endpoint"].__name__)

        user_id = await self._get_user_from_request(request)
        action = (r and r.action) or await self._get_action_from_method(request.method)
        resource_type = (r and r.resource_type) or to_resource_type(
            request["endpoint"].__name__
        )
        if r and r.resource_id:
            if r.resource_id_kind == ResourceIdKind.LITERAL:
                resource_id = r.resource_id
            else:
                resource_id = request.path_params[r.resource_id]
                if not resource_id:
                    raise
        else:
            resource_id = constants.RESOURCE_ID_DEFAULT

        if not await _FastApiIntegration._run(
            self.authorize,
            actor={"type": "User", "id": user_id},
            action=action,
            resource={"type": resource_type, "id": resource_id},
        ):
            raise

    async def _run(func: Callable[..., Any], *args, **kwargs):
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return await run_in_threadpool(func, *args, **kwargs)

    async def _get_user_from_request(self, request: Request) -> str:
        if self._identify_user_from_request:
            return await _FastApiIntegration._run(
                self._identify_user_from_request, {"request": request}
            )

        authorization = request.headers.get("Authorization")
        return utils.get_sub_from_jwt(authorization)  # type: ignore

    async def _get_action_from_method(self, method: str) -> str:
        if self._identify_action_from_method:
            return await _FastApiIntegration._run(
                self._identify_action_from_method, {"method": method}
            )

        return utils.default_get_action_from_method(method)

    def _parse_resource_id(self, resource_id: str) -> Tuple[ResourceIdKind, str]:
        match = _PARAM_REGEX.match(resource_id)
        if not match:
            return (ResourceIdKind.LITERAL, resource_id)
        else:
            return (ResourceIdKind.PARAM, match.group("param"))


class FastApiIntegration(IntegrationConfig):
    @staticmethod
    def init(url: str, api_key: str):
        return _FastApiIntegration(url, api_key)
