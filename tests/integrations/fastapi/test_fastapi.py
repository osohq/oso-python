import asyncio
from typing import Optional, Tuple

import oso_sdk
import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from oso_sdk.integrations import ResourceIdKind
from oso_sdk.integrations.fastapi import FastApiIntegration, _FastApiIntegration


def fastapi_app_factory(
    optin: bool = False,
    exception: Optional[Exception] = None,
) -> Tuple[FastAPI, oso_sdk.OsoSdk]:
    oso = oso_sdk.init(
        "API_KEY", FastApiIntegration(), shared=False, optin=optin, exception=exception
    )
    app = FastAPI(dependencies=[Depends(oso)])  # type: ignore

    return (app, oso)


def test_parse_resource_id():
    oso = _FastApiIntegration("API_KEY", False, None)

    assert oso._parse_resource_id("{id}") == (ResourceIdKind.PARAM, "id")
    assert oso._parse_resource_id("{id:int}") == (ResourceIdKind.PARAM, "id")
    assert oso._parse_resource_id("/org/{id}") == (ResourceIdKind.PARAM, "id")
    assert oso._parse_resource_id("foo") == (ResourceIdKind.LITERAL, "foo")
    with pytest.raises(ValueError):
        oso._parse_resource_id("/org/{id}/repo/{repo_id}")


def test_default(mock_oso_allowed, jwt_token, test_user):
    app, _ = fastapi_app_factory()

    @app.post("/org")
    async def post_org():
        return {"status": "ok"}

    @app.get("/org/{id}")
    @app.put("/org/{id}")
    @app.patch("/org/{id}")
    @app.delete("/org/{id}")
    async def org(id: int):
        return {"status": "ok"}

    client = TestClient(app)
    client.headers = {"Authorization": f"Bearer {jwt_token}"}

    resp = client.get("/")
    assert resp.status_code == 404

    resp = client.post("/org")
    assert resp.json()["status"] == "ok"
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="create", resource={"type": "PostOrg", "id": "_"}
    )

    resp = client.get("/org/1")
    assert resp.json()["status"] == "ok"
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="view", resource={"type": "Org", "id": "_"}
    )

    resp = client.put("/org/1")
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="update", resource={"type": "Org", "id": "_"}
    )

    resp = client.patch("/org/1")
    assert resp.json()["status"] == "ok"
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="update", resource={"type": "Org", "id": "_"}
    )

    resp = client.delete("/org/1")
    assert resp.json()["status"] == "ok"
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="delete", resource={"type": "Org", "id": "_"}
    )


def test_enforce_override(mock_oso_allowed, jwt_token, test_user):
    app, oso = fastapi_app_factory()

    @app.post("/org")
    @oso.enforce("foo", "bar", "Baz")
    async def post_org():
        return {"status": "ok"}

    @app.get("/org/{id}")
    @app.put("/org/{id}")
    @app.patch("/org/{id}")
    @app.delete("/org/{id}")
    @oso.enforce("{id}", "bar", "Baz")
    async def org(id: int):
        return {"status": "ok"}

    with pytest.raises(ValueError):

        @app.get("/repo/{id}")
        @oso.enforce("")
        async def repo(id: int):
            return {"status": "ok"}

    client = TestClient(app)
    client.headers = {"Authorization": f"Bearer {jwt_token}"}

    client.post("/org")
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="bar", resource={"type": "Baz", "id": "foo"}
    )

    client.get("/org/1")
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="bar", resource={"type": "Baz", "id": "1"}
    )

    client.put("/org/1")
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="bar", resource={"type": "Baz", "id": "1"}
    )

    client.patch("/org/1")
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="bar", resource={"type": "Baz", "id": "1"}
    )

    client.delete("/org/1")
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="bar", resource={"type": "Baz", "id": "1"}
    )


def test_optin(mock_oso_allowed, jwt_token, test_user):
    app, oso = fastapi_app_factory(optin=True)

    @app.get("/org/{id}")
    async def org(id: int):
        return {"status": "ok"}

    @app.get("/org/{org_id}/repo/{repo_id}")
    @oso.enforce("{repo_id}")
    async def repo(repo_id: int):
        return {"status": "ok"}

    client = TestClient(app)
    client.headers = {"Authorization": f"Bearer {jwt_token}"}

    resp = client.get("/org/1")
    assert resp.json()["status"] == "ok"

    resp = client.get("/org/1/repo/2")
    assert resp.json()["status"] == "ok"
    mock_oso_allowed.assert_called_once_with(
        actor=test_user, action="view", resource={"type": "Repo", "id": "2"}
    )


def test_denied(mock_oso_denied, jwt_token, test_user):
    app, _ = fastapi_app_factory()

    @app.get("/org/{id}")
    async def org(id: int):
        return {"status": "ok"}

    client = TestClient(app)
    client.headers = {"Authorization": f"Bearer {jwt_token}"}

    resp = client.get("/org/1")
    assert resp.status_code == 404
    mock_oso_denied.assert_called_once_with(
        actor=test_user, action="view", resource={"type": "Org", "id": "_"}
    )


def test_custom_exception(mock_oso_denied, jwt_token, test_user):
    app, oso = fastapi_app_factory(exception=Exception())

    @app.get("/org/{id}")
    async def org(id: int):
        return {"status": "ok"}

    client = TestClient(app)
    client.headers = {"Authorization": f"Bearer {jwt_token}"}

    with pytest.raises(Exception):
        client.get("/org/1")
        mock_oso_denied.assert_called_once_with(
            actor=test_user, action="view", resource={"type": "Org", "id": "_"}
        )


def test_invalid_token(jwt_payload_no_sub):
    app, _ = fastapi_app_factory()

    @app.get("/org/{id}")
    async def org(id: int):
        return {"status": "ok"}

    client = TestClient(app)
    client.headers = {"Authorization": f"Bearer {jwt_payload_no_sub}"}

    resp = client.get("/org/1")
    assert resp.status_code == 404


def test_custom_user_func_sync(mock_oso_allowed):
    app, oso = fastapi_app_factory()

    @app.get("/org/{id}")
    async def org(id: int):
        return {"status": "ok"}

    @oso.identify_user_from_request
    def user(_: Request) -> str:
        return "foo"

    client = TestClient(app)
    client.get("/org/1")
    mock_oso_allowed.assert_called_once_with(
        actor={"type": "User", "id": "foo"},
        action="view",
        resource={"type": "Org", "id": "_"},
    )


def test_custom_user_func_async(mock_oso_allowed):
    app, oso = fastapi_app_factory()

    @app.get("/org/{id}")
    async def org(id: int):
        return {"status": "ok"}

    @oso.identify_user_from_request
    async def user(_: Request) -> str:
        await asyncio.sleep(0.1)
        return "foo"

    client = TestClient(app)
    client.get("/org/1")
    mock_oso_allowed.assert_called_once_with(
        actor={"type": "User", "id": "foo"},
        action="view",
        resource={"type": "Org", "id": "_"},
    )


def test_custom_action_func_sync(mock_oso_allowed, jwt_token, test_user):
    app, oso = fastapi_app_factory()

    @app.get("/org/{id}")
    async def org(id: int):
        return {"status": "ok"}

    @oso.identify_action_from_method
    def action(_: str) -> str:
        return "bar"

    client = TestClient(app)
    client.headers = {"Authorization": f"Bearer {jwt_token}"}
    client.get("/org/1")
    mock_oso_allowed.assert_called_once_with(
        actor=test_user, action="bar", resource={"type": "Org", "id": "_"}
    )


def test_custom_action_func_async(mock_oso_allowed, jwt_token, test_user):
    app, oso = fastapi_app_factory()

    @app.get("/org/{id}")
    async def org(id: int):
        return {"status": "ok"}

    @oso.identify_action_from_method
    async def action(_: str) -> str:
        await asyncio.sleep(0.1)
        return "bar"

    client = TestClient(app)
    client.headers = {"Authorization": f"Bearer {jwt_token}"}
    client.get("/org/1")
    mock_oso_allowed.assert_called_once_with(
        actor=test_user, action="bar", resource={"type": "Org", "id": "_"}
    )
