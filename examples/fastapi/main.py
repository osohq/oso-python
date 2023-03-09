from fastapi import Depends, FastAPI, Request
import oso_sdk
from oso_sdk.integrations.fastapi import FastApiIntegration
import os

oso = oso_sdk.init(
    "https://api.osohq.com", os.environ["OSO_AUTH"], FastApiIntegration()
)

app = FastAPI(dependencies=[Depends(oso)])


@oso.identify_action_from_method
def action(method: str):
    return "read"


@oso.identify_user_from_request
def user(request: Request):
    return "mike"


@app.get("/org/{id}")
@oso.enforce("{id}", resource_type="Repo")
async def org(id: int):
    return {"message": f"Org {id}"}
