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
    authentication. That means it's up to you to figure out *who* a user is
    (for example, with a username and password).

    For this sample application, we identify the user by checking
    the request's Authorization header.

    For pedagogical purposes, we assume there are effectively two users:
    - "admin"
    - "anonymous"

    If the value of the Authorization header is "secret_password", we assume the
    user is "admin".

    Otherwise, we assume the user is "anonymous".
    """
    req = request["request"]
    auth = req.headers.get("Authorization")

    if auth == "secret_password":
        logger.warning(f"checking authorization for User:admin: {req.url.path}")
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
async def get_organization(id: str):
    """
    This is the "view" endpoint for an Organization, keyed on `id`.

    When this endpoint is accessed, we check to see if the actor has "view"
    permissions on the Organization in question.

    If you'd like to give the anonymous user access to GET `/org/acme`, you
    can add this fact to Oso Cloud:

        has_role(User:anonymous, "viewer", Organization:acme)

    Because the "viewer" role gives "view" permission, this will allow access.
    You can also add a fact giving this permission directly:

        has_permission(User:anonymous, "view", Organization:acme)

    This will also allow access, and is implied by the "viewer" role.
    """

    return {"org": id, "data": "..."}


@app.post("/org/{id}")
@oso.enforce("{id}", "edit", "Organization")
async def post_organization(id: str):
    """
    This is the "edit" endpoint for an Organization, keyed on `id`.

    When this endpoint is accessed, we check to see if the actor has "edit"
    permissions on the Organization in question.

    If you'd like to give the admin user access to POST `/org/acme`, you
    can add this fact to Oso Cloud:

        has_role(User:admin, "owner", Organization:acme)

    Because the "owner" role gives "edit" permission, this will allow access.
    You can also add a fact giving this permission directly:

        has_permission(User:admin, "edit", Organization:acme)

    This will also allow access, and is implied by the "owner" role.
    """

    # implementing this endpoint is left as an exercise for the reader
    # however, we'll return a 200 OK on successful authorization
    return {"org": id, "warning": "editing unimplemented"}


@app.get("/repo/{id}")
@oso.enforce("{id}", "view", "Repository")
async def get_repository(id: str):
    """
    This is the "view" endpoint for a Repository, keyed on `id`.

    When this endpoint is accessed, we check to see if the Actor has "view"
    permissions on the Repository in question.

    A repository belongs to an Organization, given the `repository_container`
    relation. Our policy declares that some roles on an Organization, give some
    permissions on a Repository:

        "view" if "viewer" on "repository_container";
        "edit" if "owner" on "repository_container";

    To construct the relation between the an instance of a Repository and an
    Organization, we add a fact to Oso Cloud:

        has_relation(Repository:code, "repository_container", Organization:acme)

    If you'd like to give the "anonymous" user access to GET `/repo/code`, you
    can add this fact to Oso Cloud:

        has_role(User:anonymous, "viewer", Organization:acme)

    Because the "viewer" role on Organization:acme gives the "view" permission on
    Repository:code (given the "repository_container" relation), this will allow
    access.

    Alternatively, you can give the "viewer" role directly on this resource:

        has_role(User:anonymous, "viewer", Repository:acme)

    Because the "viewer" role on Repository:code gives the "edit" permission,
    this will allow access. You can also add a fact giving this permission
    directly:

        has_permission(User:anonymous, "view", Repository:code)

    Each of the approaches described above will allow "anonymous" to GET
    `/repo/code`.
    """

    return {"repo": id, "data": "..."}


@app.post("/repo/{id}")
@oso.enforce("{id}", "edit", "Repository")
async def post_repository(id: str):
    """
    This is the "edit" endpoint for a Repository, keyed on `id`.

    When this endpoint is accessed, we check to see if the Actor has "edit"
    permissions on the Repository in question.

    Assuming that this relation exists as a fact in Oso Cloud:

        has_relation(Repository:code, "repository_container", Organization:acme)

    ...if you'd like to give the "admin" user access to POST `/repo/code`,
    you can add this fact to Oso Cloud:

        has_role(User:admin, "editor", Organization:acme)

    Because the "editor" role on Organization:acme gives the "viewer" permission
    on Repository:code (given the "repository_container" relation), this will
    allow access.

    Alternatively, you can give the "editor" role directly on this resource:

        has_role(User:admin, "editor", Repository:acme)

    Because the "editor" role on Repository:code gives the "edit" permission,
    this will allow access. You can also add a fact giving this permission
    directly:

        has_permission(User:anonymous, "edit", Repository:code)

    Each of the approaches described above will allow "admin" to POST
    `/repo/code`.
    """

    return {"repo": id, "data": "..."}
