from fastapi import Depends, FastAPI
import oso_sdk
from oso_sdk.integrations.fastapi import FastApiIntegration
import os

oso = oso_sdk.init(
    "https://api.osohq.com", os.environ["OSO_AUTH"], FastApiIntegration()
)

app = FastAPI(dependencies=[Depends(oso)])


@app.get("/org/{id}")
@oso.enforce("{id}", "view", "Repo")
async def org(id: int):
    return {"message": f"Org {id}"}
