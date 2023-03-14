import functools
import re
import traceback
from typing import Optional, Tuple

from flask import Blueprint, abort, current_app, request
from oso_sdk import IntegrationConfig, OsoSdk

from ..constants import RESOURCE_ID_DEFAULT
from ..exceptions import OsoSdkInternalError
from . import ResourceIdKind, to_resource_type, utils

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
            (?P<variable>[a-zA-Z_][a-zA-Z0-9_]*)        # variable name
        >
    """,
    re.VERBOSE,
)


class _FlaskIntegration(OsoSdk):
    def __call__(self):
        # Route is not declared
        if request.endpoint is None:
            return

        r = self.routes.get(request.endpoint)
        if self._optin and not r:
            return

        try:
            user_id = self._get_user_from_request()
            action = (r and r.action) or self._get_action_from_method()
        except OsoSdkInternalError:
            traceback.print_exc()
            self._unauthorized()

        resource_type = (r and r.resource_type) or to_resource_type(request.endpoint)
        if r and r.resource_id:
            if r.resource_id_kind == ResourceIdKind.LITERAL:
                resource_id = r.resource_id
            elif request.view_args:
                resource_id = request.view_args.get(r.resource_id)
                if resource_id is None:
                    raise KeyError(
                        f"`{r.resource_id} param not found"
                    )  # pragma: no cover
            else:
                raise KeyError(f"`{r.resource_id}` param not found")  # pragma: no cover

        else:
            resource_id = RESOURCE_ID_DEFAULT

        try:
            if not self.authorize(
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

        else:
            abort(404)

    def _get_user_from_request(self) -> str:
        if self._identify_user_from_request:
            return current_app.ensure_sync(self._identify_user_from_request)()

        authorization = request.headers.get("Authorization")
        return utils.get_sub_from_jwt(authorization)

    def _get_action_from_method(self) -> str:
        if self._identify_action_from_method:
            return current_app.ensure_sync(self._identify_action_from_method)(
                request.method
            )

        return utils.default_get_action_from_method(request.method)

    def _parse_resource_id(self, resource_id: str) -> Tuple[ResourceIdKind, str]:
        matches = _PARAM_REGEX.findall(resource_id)
        if not matches:
            return (ResourceIdKind.LITERAL, resource_id)
        if len(matches) > 1:
            raise ValueError("Only one path parameter may be used")
        else:
            return (ResourceIdKind.PARAM, matches[0][2])


def _before_request(**kwargs):
    kwargs["oso"]()

    return


class FlaskIntegration(IntegrationConfig):
    @staticmethod
    def init(
        api_key: str, optin: bool, exception: Optional[Exception]
    ) -> _FlaskIntegration:
        rv = _FlaskIntegration(api_key, optin, exception)
        before_request = functools.partial(_before_request, oso=rv)
        oso_bp = Blueprint("oso", __name__)
        oso_bp.before_app_request(before_request)
        current_app.register_blueprint(oso_bp)
        return rv
