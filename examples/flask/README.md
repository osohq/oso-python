# Flask

Integrate Oso Cloud into your Flask application.

## Install

Install `oso-sdk` from PyPI with the `flask` extra:
```bash
pip install --upgrade 'oso-sdk[flask]`
```

## Configure

Configuration should happen as early as possible in your application's lifecycle:

```python
import oso_sdk
from flask import Flask
from oso_sdk.integrations.flask import FlaskIntegration

app = Flask(__name__)

with app.app_context():
    oso = oso_sdk.init(
        "YOUR_API_KEY",
        FlaskIntegration(),
    )
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
    FlaskIntegration(),
    
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
@app.get("/org/<int:id>")
@oso.enforce(
    "<id>",

    # Hardcode an action for this route
    # "read",

    # Hardcode a resource_type for this route
    # "Organization",
)
def org(id: int):
    return {"org": id}
```


### User Identification

You may provide a function to determine the Actor ID using the `@oso.identify_user_from_request` decorator. The function can be either `sync` or `async`. It should not take any arguments, and Flask contexts are available.

```python
@oso.identify_user_from_request
def user() -> str:
    return "TEST_USER"
```

### Action Identification

For routes that do not have a hardcoded action from `@oso.enforce`, you may provide a function to determine the action for routes using the `@oso.identify_action_from_method` decorator. The function can be either `sync` or `async`. It should take one `str` argument, and Flask contexts are available.

```python
@oso.identify_action_from_method
def action(_: str) -> str:
    return "read"
```

## Supported Versions

- Flask: 2.0.0+
- Python: 3.8+