import oso_sdk
import os
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import HTTPException
from oso_sdk.integrations.fastapi import FastApiIntegration
import logging

logger = logging.getLogger(__name__)


class ApiKeyNotFound(Exception):
    """
    Unable to start application, could not retrieve Oso Cloud API key.
    """

    pass


def api_key() -> str:
    """
    Retrieve API key, checking `OSO_AUTH` environment variable.

    Raise an exception if no value is set.
    """
    api_key = os.environ.get("OSO_AUTH")
    if api_key is None:
        raise ApiKeyNotFound
    else:
        return api_key


oso = oso_sdk.init(
    api_key(),
    FastApiIntegration(),
    # create a local instance of the Oso SDK
    shared=False,
    # only enforce routes with the `@oso.enforce` decorator
    optin=True,
)

app = FastAPI(dependencies=[Depends(oso)])


@oso.identify_user_from_request
async def user(request: Request) -> str:
    """
    Oso Cloud handles authorization - you'll need to handle your own
    authentication.

    For this sample application, we perform authentication by checking
    the Authorization header.

    For pedagogical purposes, we assume there are effectively two users:
    - "admin"
    - "anonymous"

    If it contains the value "secret_password", we assume the user is
    "admin".

    Otherwise, we assume the user is "anonymous".
    """
    req = request["request"]
    auth = req.headers.get("Authorization")

    if auth == "secret_password":
        logger.warning(f"checking authorization for User:superadmin: {req.url.path}")
        return "admin"
    else:
        logger.warning(f"checking authorization for User:anonymous: {req.url.path}")
        return "anonymous"


@app.get("/org/{id}")
@oso.enforce(
    # actor
    "{id}",
    # action
    "view",
    # resource
    "Organization",
)
async def org(id: str):
    """
    This is the "view" endpoint for an Organization, keyed on `id`.

    When this endpoint is accessed, we check to see if the actor has "view"
    permissions on the Organization in question.

    If you'd like to give the anonymous user access to GET `/org/acme`, you
    can add this fact to Oso Cloud:

    has_role(User:anonymous, "view", Organization:acme)
    """

    return {"org": id, "data": "TODO"}


@app.post("/org/{id}")
@oso.enforce("{id}", "edit", "Organization")
async def org(id: str):
    """
    This is the "edit" endpoint for an Organization, keyed on `id`.

    When this endpoint is accessed, we check to see if the actor has "edit"
    permissions on the Organization in question.

    If you'd like to give the superadmin user access to POST `/org/acme`, you
    can add this fact to Oso Cloud:

        has_role(User:admin, "owner", Organization:acme)

    Alternatively, you can give the permission directly:

        has_permission(User:admin, "edit", Organization:acme)

    """

    # implementing this endpoint is left as an exercise for the reader
    # however, we'll return a 200 OK on successful authorization
    return {"org": id, "warning": "editing unimplemented"}
