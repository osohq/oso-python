# FastAPI

Integrate Oso Cloud into your FastAPI application.

## Install

Install `oso-sdk` from PyPI with the `fastapi` extra:
```bash
pip install --upgrade 'oso-sdk[fastapi]`
```

## Configure

The Oso SDK instance should be added as a dependency of your FastAPI application:

```python
import oso_sdk
from fastapi import Depends, FastAPI
from oso_sdk.integrations.fastapi import FastApiIntegration

oso = oso_sdk.init(
    "YOUR_API_KEY",
    FastApiIntegration(),
)

app = FastAPI(dependencies=[Depends(oso)])
```

After the Oso SDK is initialized, you may access it by calling `global_oso()`:

```python
from oso_sdk import global_oso

oso = global_oso()
```

## Integration Options

By default, all routes are enforced by Oso Cloud.
- Actor ID is the `subject` field of a JWT token. If you do not use JWT, you may [override the user identification](#user-identification).
- Action is inferred from the HTTP method. If you have a different set of permissions from the defaults, you may [override the action identification](#action-identification).
- HTTP 404 is returned on authorization failure.

### Initialization

You may pass additional keyword arguments to `oso_sdk.init`.

```python
oso = oso_sdk.init(
    "YOUR_API_KEY",
    FastApiIntegration(),
    
    # create a local instance of the Oso SDK
    # if only a local instance is created, then global_oso() is not instantiated
    # shared=False,

    # only enforce routes with the `@oso.enforce` decorator
    # optin=True,

    # raise a custom exception on authorization failure
    # exception=Exception()
)
```

### Route overrides

You may override the default action and resource arguments and opt-in a route for enforcement using the `@oso.enforce` decorator. The `resource_id` argument may either be a literal or a path parameter.

```python
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
```


### User Identification

You may provide a function to determine the Actor ID using the `@oso.identify_user_from_request` decorator. The function can be either `sync` or `async`. It should take one `fastapi.Request` argument.

```python
@oso.identify_user_from_request
async def user(_: Request) -> str:
    return "TEST_USER"
```

### Action Identification

For routes that do not have a hardcoded action from `@oso.enforce`, you may provide a function to determine the action for routes using the `@oso.identify_action_from_method` decorator. The function can be either `sync` or `async`. It should take one `str` argument, and FastAPI contexts are available.

```python
@oso.identify_action_from_method
async def action(_: str) -> str:
    return "read"
```

## Supported Versions

- FastAPI: 0.79.0+
- Python: 3.8+