from functools import wraps
import inspect
from typing import Any, Callable
from fastapi import Request
from . import Integration, IntegrationConfig, ResourceIdKind, Route, constants, utils
import oso_cloud
import re
import string
from starlette.concurrency import run_in_threadpool

PARAM_REGEX = re.compile("{([a-zA-Z_][a-zA-Z0-9_]+)}")


class _FastApiIntegration(oso_cloud.Oso, Integration):
    def __init__(self, url: str, api_key: str):
        oso_cloud.Oso.__init__(self, url, api_key)
        Integration.__init__(self)

    async def __call__(self, request: Request):
        r = self.routes.get(request["endpoint"].__name__)

        user_id = await self._get_user_from_request(request)
        action = (r and r.action) or await self._get_action_from_method(request.method)
        resource_type = (r and r.resource_type) or request["endpoint"].__name__
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
        return utils.get_sub_from_jwt(authorization)

    async def _get_action_from_method(self, method: str) -> str:
        if self._identify_action_from_method:
            return await _FastApiIntegration._run(
                self._identify_action_from_method, {"method": method}
            )

        return utils.default_get_action_from_method(method)

    def enforce(
        self,
        resource_id: str,
        action: str | None = None,
        resource_type: str | None = None,
    ):
        matches = PARAM_REGEX.findall(resource_id)
        if len(matches) == 0:
            resource_id_kind = ResourceIdKind.LITERAL
        else:
            resource_id_kind = ResourceIdKind.PARAM
            resource_id = matches[0]

        def decorator(f):
            self.routes[f.__name__] = Route(
                action,
                resource_type
                or string.capwords(f.__name__.replace("_", " ")).replace(" ", ""),
                resource_id,
                resource_id_kind,
            )

            @wraps(f)
            async def decorated_view(*args, **kwargs):
                return await f(*args, **kwargs)

            return decorated_view

        return decorator


class FastApiIntegration(IntegrationConfig):
    @staticmethod
    def init(url: str, api_key: str):
        return _FastApiIntegration(url, api_key)
