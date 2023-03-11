import oso_sdk
from flask import Flask
from oso_sdk.integrations.flask import FlaskIntegration

app = Flask(__name__)

with app.app_context():
    oso = oso_sdk.init(
        "YOUR_API_KEY",
        FlaskIntegration(),
        # create a local instance of the Oso SDK
        # if only a local instance is created, then global_oso() is not instantiated
        # shared=False,
        # only enforce routes with the `@oso.enforce` decorator
        # optin=True,
        # raise a custom exception on authorization failure
        # exception=Exception(),
    )


# @oso.identify_action_from_method
# def action(_: str) -> str:
#     return "read"


# @oso.identify_user_from_request
# def user() -> str:
#     return "TEST_USER"


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
