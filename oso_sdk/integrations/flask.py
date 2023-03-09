import functools
from typing import Tuple
from flask import abort, current_app, request, Blueprint
from . import (
    Integration,
    IntegrationConfig,
    ResourceIdKind,
    constants,
    utils,
    to_resource_type,
)
from ..exceptions import OsoSdkInternalError
import oso_cloud
import re

# from werkzeug.routing.rules import _part_re
# Extract parameter regex and copy instead of import as a safeguard against
# future changes to the pattern
_PARAM_REGEX = re.compile(
    r"""
        <
            (?:
                (?P<converter>[a-zA-Z_][a-zA-Z0-9_]*)   # converter name
                (?:\((?P<arguments>.*?)\))?             # converter arguments
                \:                                      # variable delimiter
            )?
            (?P<variable>[a-zA-Z_][a-zA-Z0-9_]*)      # variable name
        >
    """,
    re.VERBOSE,
)


class _FlaskIntegration(oso_cloud.Oso, Integration):
    def __init__(self, url: str, api_key: str, exception: Exception | None = None):
        oso_cloud.Oso.__init__(self, url, api_key)
        Integration.__init__(self, exception)

    def __call__(self):
        # Route is not declared
        if request.endpoint is None:
            return

        r = self.routes.get(request.endpoint)

        try:
            user_id = self._get_user_from_request()
            action = (r and r.action) or self._get_action_from_method()
        except OsoSdkInternalError:
            self._unauthorized()
        
        resource_type = (r and r.resource_type) or to_resource_type(request.endpoint)
        if r and r.resource_id:
            if r.resource_id_kind == ResourceIdKind.LITERAL:
                resource_id = r.resource_id
            elif request.view_args:
                resource_id = request.view_args.get(r.resource_id)
                if resource_id is None:
                    raise KeyError(f"`{r.resource_id} param not found")
            else:
                raise KeyError(f"`{r.resource_id}` param not found")
            
        else:
            resource_id = constants.RESOURCE_ID_DEFAULT

        if not self.authorize(
            actor={"type": "User", "id": user_id},
            action=action,
            resource={"type": resource_type, "id": resource_id},
        ):
            self._unauthorized()
    
    def _unauthorized(self):
        if self._custom_exception:
            raise self._custom_exception
        
        else:
            abort(400)

    def _get_user_from_request(self) -> str:
        if self._identify_user_from_request:
            foo = current_app.ensure_sync(self._identify_user_from_request)
            return current_app.ensure_sync(self._identify_user_from_request)(request)

        authorization = request.headers.get("Authorization")
        return utils.get_sub_from_jwt(authorization)  # type: ignore

    def _get_action_from_method(self) -> str:
        if self._identify_action_from_method:
            return current_app.ensure_sync(self._identify_action_from_method)(
                request.method
            )

        return utils.default_get_action_from_method(request.method)

    def _parse_resource_id(self, resource_id: str) -> Tuple[ResourceIdKind, str]:
        match = _PARAM_REGEX.match(resource_id)
        if not match:
            return (ResourceIdKind.LITERAL, resource_id)
        else:
            return (ResourceIdKind.PARAM, match.group("variable"))


def _before_request(**kwargs):
    kwargs["oso"]()

    return


_oso_bp = Blueprint("oso", __name__)


class FlaskIntegration(IntegrationConfig):
    @staticmethod
    def init(url: str, api_key: str, exception: Exception | None = None):
        rv = _FlaskIntegration(url, api_key, exception)
        before_request = functools.partial(_before_request, oso=rv)
        _oso_bp.before_app_request(before_request)
        current_app.register_blueprint(_oso_bp)
        return rv
