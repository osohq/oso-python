import oso_sdk
from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel
from oso_sdk.integrations.fastapi import FastApiIntegration
from oso_sdk.types import oso_type

from random import randint

oso = oso_sdk.init(
    "YOUR_API_KEY",
    FastApiIntegration(),
    # create a local instance of the Oso SDK
    # if only a local instance is created, then global_oso() is not instantiated
    # shared=False,
    # only enforce routes with the `@oso.enforce` decorator
    # optin=True,
    # raise a custom exception on authorization failure
    # exception=Exception(),
)

app = FastAPI(dependencies=[Depends(oso)])


@oso_type
class Org(BaseModel):
    id: int


def lookup_org(id: int) -> Org:
    return Org(id=id)


@oso_type(id="name")
class User(BaseModel):
    name: str


@oso_type
class Repo(BaseModel):
    id: int | None
    name: str


@oso.identify_user_from_request
async def user(_: Request) -> str:
    return "TEST_USER"


@app.get("/org/{id}")
@oso.enforce(
    "{id}",
    # Hardcode an action for this route
    # "read",
    # Hardcode a resource_type for this route
    # "Organization",
)
async def org(id: int) -> Org:
    return lookup_org(id)


TEST_USER = User(name="TEST_USER")


@oso.enforce("{org_id}", "create_repos", "Org")
@app.post("/org/{org_id}/repo/")
async def create_repo(org_id: int, repo: Repo) -> Repo:
    org: Org = lookup_org(org_id)
    repo.id = randint(0, 100_000)

    # write one fact
    # oso.insert_fact("has_relation", (repo, "parent", org))
    # or many
    oso.insert_facts(
        [
            ("has_relation", (repo, "parent", org)),
            ("has_role", (TEST_USER, "owner", repo)),
        ]
    )
    return repo
