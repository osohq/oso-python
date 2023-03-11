import os

from flask import Flask

import oso_sdk
from oso_sdk.integrations.flask import FlaskIntegration

app = Flask(__name__)

with app.app_context():
    oso_sdk.init(
        os.environ["OSO_AUTH"],
        FlaskIntegration(),
        exception=Exception(),
        optin=True,
    )


@app.route("/org/<int:id>")
def org(id: int):
    return {"message": f"Org {id}"}


if __name__ == "__main__":
    app.run(port=8000)
