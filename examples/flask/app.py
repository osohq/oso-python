from flask import Flask
import oso_sdk
from oso_sdk.integrations.flask import FlaskIntegration
import os

app = Flask(__name__)

with app.app_context():
    oso_sdk.init(
        "https://api.osohq.com", os.environ["OSO_AUTH"], FlaskIntegration()
    )


@app.route("/org/<int:id>")
def org(id):
    return {"message": f"Org {id}"}


if __name__ == "__main__":
    app.run(port=8000)
