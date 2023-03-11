import asyncio

import oso_sdk
import pytest
from flask import Flask
from oso_sdk.integrations import ResourceIdKind
from oso_sdk.integrations.flask import FlaskIntegration, _FlaskIntegration


@pytest.fixture
def app_default():
    app = Flask(__name__)
    app.testing = True
    with app.app_context():
        oso = oso_sdk.init(
            "API_KEY",
            FlaskIntegration(),
            shared=False,
        )

    yield (app, oso)


@pytest.fixture
def app_optin():
    app = Flask(__name__)
    app.testing = True
    with app.app_context():
        oso = oso_sdk.init("API_KEY", FlaskIntegration(), shared=False, optin=True)

    yield (app, oso)


@pytest.fixture
def app_custom_exception():
    app = Flask(__name__)
    app.testing = True
    with app.app_context():
        oso = oso_sdk.init(
            "API_KEY", FlaskIntegration(), shared=False, exception=Exception()
        )

    yield (app, oso)


def test_parse_resource_id():
    oso = _FlaskIntegration("API_KEY", False, None)

    assert oso._parse_resource_id("<id>") == (ResourceIdKind.PARAM, "id")
    assert oso._parse_resource_id("<int:id>") == (ResourceIdKind.PARAM, "id")
    assert oso._parse_resource_id("/org/<id>") == (ResourceIdKind.PARAM, "id")
    assert oso._parse_resource_id("foo") == (ResourceIdKind.LITERAL, "foo")
    with pytest.raises(ValueError):
        oso._parse_resource_id("/org/<id>/repo/<repo_id>")


@pytest.fixture
def jwt_token_header(jwt_token):
    return {"Authorization": f"Bearer {jwt_token}"}


@pytest.fixture
def jwt_payload_malformed_header(jwt_payload_malformed):
    return {"Authorization": f"Bearer {jwt_payload_malformed}"}


@pytest.fixture
def jwt_payload_no_sub_header(jwt_payload_no_sub):
    return {"Authorization": f"Bearer {jwt_payload_no_sub}"}


def test_default(app_default, mock_oso_allowed, jwt_token_header, test_user):
    app, _ = app_default

    @app.post("/org")
    def post_org():
        return {"status": "ok"}

    @app.route("/org/<id>", methods=["GET", "PUT", "PATCH", "DELETE"])
    def org(id: int):
        return {"status": "ok"}

    client = app.test_client()

    resp = client.get("/")
    assert resp.status_code == 404

    resp = client.post("/org", headers=jwt_token_header)
    assert resp.json["status"] == "ok"
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="create", resource={"type": "PostOrg", "id": "_"}
    )

    resp = client.get("/org/1", headers=jwt_token_header)
    assert resp.json["status"] == "ok"
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="view", resource={"type": "Org", "id": "_"}
    )

    resp = client.put("/org/1", headers=jwt_token_header)
    assert resp.json["status"] == "ok"
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="update", resource={"type": "Org", "id": "_"}
    )

    resp = client.patch("/org/1", headers=jwt_token_header)
    assert resp.json["status"] == "ok"
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="update", resource={"type": "Org", "id": "_"}
    )

    resp = client.delete("/org/1", headers=jwt_token_header)
    assert resp.json["status"] == "ok"
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="delete", resource={"type": "Org", "id": "_"}
    )


def test_enforce_override(app_default, mock_oso_allowed, jwt_token_header, test_user):
    app, oso = app_default

    @app.post("/org")
    @oso.enforce("foo", "bar", "Baz")
    def post_org():
        return {"status": "ok"}

    @app.route("/org/<id>", methods=["GET", "PUT", "PATCH", "DELETE"])
    @oso.enforce("<id>", "bar", "Baz")
    def org(id: int):
        return {"status": "ok"}

    client = app.test_client()
    resp = client.post("/org", headers=jwt_token_header)
    assert resp.json["status"] == "ok"
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="bar", resource={"type": "Baz", "id": "foo"}
    )

    resp = client.get("/org/1", headers=jwt_token_header)
    assert resp.json["status"] == "ok"
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="bar", resource={"type": "Baz", "id": "1"}
    )

    resp = client.put("/org/1", headers=jwt_token_header)
    assert resp.json["status"] == "ok"
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="bar", resource={"type": "Baz", "id": "1"}
    )

    resp = client.patch("/org/1", headers=jwt_token_header)
    assert resp.json["status"] == "ok"
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="bar", resource={"type": "Baz", "id": "1"}
    )

    resp = client.delete("/org/1", headers=jwt_token_header)
    assert resp.json["status"] == "ok"
    mock_oso_allowed.assert_called_with(
        actor=test_user, action="bar", resource={"type": "Baz", "id": "1"}
    )


def test_optin(app_optin, mock_oso_allowed, jwt_token_header, test_user):
    app, oso = app_optin

    @app.get("/org/<id>")
    def org(id: int):
        return {"status": "ok"}

    @app.get("/org/<org_id>/repo/<repo_id>")
    @oso.enforce("<repo_id>")
    def repo(org_id: int, repo_id: int):
        return {"status": "ok"}

    client = app.test_client()

    resp = client.get("/org/1", headers=jwt_token_header)
    assert resp.json["status"] == "ok"

    resp = client.get("/org/1/repo/2", headers=jwt_token_header)
    assert resp.json["status"] == "ok"
    mock_oso_allowed.assert_called_once_with(
        actor=test_user, action="view", resource={"type": "Repo", "id": "2"}
    )


def test_denied(app_default, mock_oso_denied, jwt_token_header, test_user):
    app, _ = app_default

    @app.get("/org/<id>")
    def org(id: int):
        return {"status": "ok"}

    client = app.test_client()

    resp = client.get("/org/1", headers=jwt_token_header)
    assert resp.status_code == 404
    mock_oso_denied.assert_called_once_with(
        actor=test_user, action="view", resource={"type": "Org", "id": "_"}
    )


def test_custom_exception(
    app_custom_exception, mock_oso_denied, jwt_token_header, test_user
):
    app, _ = app_custom_exception

    @app.get("/org/<id>")
    def org(id: int):
        return {"status": "ok"}

    client = app.test_client()

    with pytest.raises(Exception):
        client.get("/org/1", headers=jwt_token_header)
        mock_oso_denied.assert_called_once_with(
            actor=test_user, action="view", resource={"type": "Org", "id": "_"}
        )


def test_invalid_token(app_default, jwt_payload_no_sub_header):
    app, _ = app_default

    @app.get("/org/<id>")
    def org(id: int):
        return {"status": "ok"}

    client = app.test_client()

    resp = client.get("/org/1", headers=jwt_payload_no_sub_header)
    assert resp.status_code == 404


def test_custom_user_func_sync(app_default, mock_oso_allowed):
    app, oso = app_default

    @app.get("/org/<id>")
    def org(id: int):
        return {"status": "ok"}

    @oso.identify_user_from_request
    def user() -> str:
        return "foo"

    client = app.test_client()
    client.get("/org/1")
    mock_oso_allowed.assert_called_once_with(
        actor={"type": "User", "id": "foo"},
        action="view",
        resource={"type": "Org", "id": "_"},
    )


def test_custom_user_func_async(app_default, mock_oso_allowed):
    app, oso = app_default

    @app.get("/org/<id>")
    def org(id: int):
        return {"status": "ok"}

    @oso.identify_user_from_request
    async def user() -> str:
        await asyncio.sleep(0.1)
        return "foo"

    client = app.test_client()
    client.get("/org/1")
    mock_oso_allowed.assert_called_once_with(
        actor={"type": "User", "id": "foo"},
        action="view",
        resource={"type": "Org", "id": "_"},
    )


def test_custom_action_func_sync(
    app_default, mock_oso_allowed, jwt_token_header, test_user
):
    app, oso = app_default

    @app.get("/org/<id>")
    def org(id: int):
        return {"status": "ok"}

    @oso.identify_action_from_method
    def action(_: str) -> str:
        return "bar"

    client = app.test_client()
    client.get("/org/1", headers=jwt_token_header)
    mock_oso_allowed.assert_called_once_with(
        actor=test_user, action="bar", resource={"type": "Org", "id": "_"}
    )


def test_custom_action_func_async(
    app_default, mock_oso_allowed, jwt_token_header, test_user
):
    app, oso = app_default

    @app.get("/org/<id>")
    def org(id: int):
        return {"status": "ok"}

    @oso.identify_action_from_method
    async def action(_: str) -> str:
        await asyncio.sleep(0.1)
        return "bar"

    client = app.test_client()
    client.get("/org/1", headers=jwt_token_header)
    mock_oso_allowed.assert_called_once_with(
        actor=test_user, action="bar", resource={"type": "Org", "id": "_"}
    )
