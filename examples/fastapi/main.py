import oso_sdk
from fastapi import Depends, FastAPI
from oso_sdk.integrations.fastapi import FastApiIntegration

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


# @oso.identify_action_from_method
# def action(_: str) -> str:
#     return "read"


# from fastapi import Request
# @oso.identify_user_from_request
# async def user(_: Request) -> str:
#     return "TEST_USER"


@app.get("/org/{id}")
@oso.enforce(
    "{id}",
    # Hardcode an action for this route
    # "read",
    # Hardcode a resource_type for this route
    # "Organization",
)
async def org(id: int):
    return {"org": id}
