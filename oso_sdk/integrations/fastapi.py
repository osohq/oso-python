import inspect
import re
import traceback
from typing import Optional, Tuple

from fastapi import HTTPException, Request
from oso_sdk import IntegrationConfig, OsoSdk
from starlette.concurrency import run_in_threadpool

from ..constants import RESOURCE_ID_DEFAULT
from ..exceptions import OsoSdkInternalError
from . import ResourceIdKind, to_resource_type, utils

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


class _FastApiIntegration(OsoSdk):
    async def __call__(self, request: Request):
        if not request["endpoint"]:
            return  # pragma: no cover

        r = self.routes.get(request["endpoint"].__name__)
        if self._optin and not r:
            return

        try:
            user_id = await self._get_user_from_request(request)
            action = (r and r.action) or await self._get_action_from_method(
                request.method
            )
        except OsoSdkInternalError:
            traceback.print_exc()
            self._unauthorized()

        resource_type = (r and r.resource_type) or to_resource_type(
            request["endpoint"].__name__
        )
        if r and r.resource_id:
            if r.resource_id_kind == ResourceIdKind.LITERAL:
                resource_id = r.resource_id
            else:
                resource_id = request.path_params.get(r.resource_id)  # type: ignore
                if resource_id is None:
                    raise KeyError(
                        f"`{r.resource_id} param not found"
                    )  # pragma: no cover
        else:
            resource_id = RESOURCE_ID_DEFAULT

        try:
            if not await _FastApiIntegration._run(
                self.authorize,
                actor={"type": "User", "id": str(user_id)},
                action=str(action),
                resource={"type": resource_type, "id": str(resource_id)},
            ):
                self._unauthorized()
        except Exception:
            traceback.print_exc()
            self._unauthorized()

    def _unauthorized(self):
        if self._custom_exception:
            raise self._custom_exception

        raise HTTPException(status_code=404)

    @staticmethod
    async def _run(func, *args, **kwargs):
        """TODO
        support for sync and async (documenting bc this is the most
        FastAPI specific function on this class)
        Args:
            func (Callable[..., Any]): _description_

        Returns:
            _type_: _description_
        """
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

    def _parse_resource_id(self, resource_id: str) -> Tuple[ResourceIdKind, str]:
        matches = _PARAM_REGEX.findall(resource_id)
        if not matches:
            return (ResourceIdKind.LITERAL, resource_id)
        elif len(matches) > 1:
            raise ValueError("Only one path parameter may be used")
        else:
            return (ResourceIdKind.PARAM, matches[0][0])


class FastApiIntegration(IntegrationConfig):
    @staticmethod
    def init(
        api_key: str, optin: bool, exception: Optional[Exception]
    ) -> _FastApiIntegration:
        return _FastApiIntegration(api_key, optin, exception)
