# Setting up the Starter Policy

This application assumes the following Polar policy is active:

``` sh
actor User {}

resource Organization {
  roles = ["viewer", "owner"];
  permissions = ["view", "edit"];

  "view" if "viewer";
  "view" if "owner";
  "edit" if "owner";
}

resource Repository {
  roles = ["viewer", "owner"];
  permissions = ["view", "edit"];
  relations = { repository_container: Organization };

  "view" if "viewer";
  "view" if "owner";
  "edit" if "owner";
  "view" if "viewer" on "repository_container";
  "view" if "owner" on "repository_container";
  "edit" if "owner" on "repository_container";
}
```

# Running the sample application

Install `oso-sdk` from PyPI with the `fastapi` extra:
```bash
pip install --upgrade 'oso-sdk[fastapi]`
```

Install `uvicorn` from PyPI to run the webserver:
```bash
pip install --upgrade 'uvicorn[standard]`
```

Grab an API key from Oso Cloud, setting the `OSO_AUTH` environment variable.

Now you can run the webserver with `uvicorn`:
```bash
export OSO_AUTH="YOUR_API_KEY"
uvicorn sample_application:app
```

# Making Requests

To authenticate requests, Oso needs to know which Actor is performing an action.

To keep the implementation of this sample application simple, there are two users:
- `anonymous`
- `admin`

## `User:admin`

To authenticate as `User:admin`, set the `Authorization` header's value to `secret_password`:

```bash
curl -H 'Authorization: secret_password' localhost:8000/org/acme
```

## `User:anonymous`

All other requests are authenticated as `User:anonymous`:

```bash
curl localhost:8000/org/acme
```

# Configuring Authorization Data with Facts

By default, all routes will return a 404 for all users. To get a successful 200 OK response, you'll need to add some **facts** to Oso Cloud.

## Assigning Roles on an `Organization`

The `Organization` resource has two roles:
- the `viewer` role (which grants `view`), and
- the `owner` role (which grants both `view` and `edit`)

By assigning roles to an Actor as a fact, we can authorize access. Roles are assigned to individual instances of a resource - in this case, we'll consider `Organization:acme`.

### `GET /org/acme` as `User:anonymous`

The `get_organization` route is enforced:

```python
@app.get("/org/{id}")
@oso.enforce("{id}", "view", "Organization")
```


To access this route, you'll need to provide the `view` permission. This can be accomplished by adding a fact, which gives `User:anonymous` the `viewer` role:
- `has_role(User:anonymous, "viewer", Organization:acme)`

Now, the following request should succeed:

```bash
curl localhost:8000/org/acme
```

### `POST /org/acme` as `User:admin`

The `post_organization` route is enforced:

``` python
@app.get("/org/{id}")
@oso.enforce("{id}", "edit", "Organization")
```
To access thie route, you'll need to provide the `edit` permission. This can be accomplished by adding a fact which gives `User:admin` the `owner` role:
- `has_role(User:admin, "owner", Organization:acme)`

Now, the following request should succeed:

```bash
curl -H 'Authorization: secret_password' localhost:8000/org/acme
```

## Constructing a Relation with Facts

TODO 

- `has_relation(Repository:code, "repository_container", Organization:acme)`

```
"viewer" if "viewer" on "repository_container";
"owner" if "owner" on "repository_container";
```

## `GET /org/code` as `User:anonymous`

TODO 

### Allowing `view` through `Organization:acme`

TODO 

### Allowing `view` through `Repository:acme`

TODO

## `POST /org/code` as `User:admin`

### Allowing `edit` through `Organization:acme`

TODO

### Allowing `edit` through `Repository:code`

TODO
