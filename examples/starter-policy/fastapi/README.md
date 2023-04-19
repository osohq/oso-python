# Setting up the Starter Policy

This application assumes the following Polar policy is active:

```ruby
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
  relations = { repository_tenant: Organization };

  "view" if "viewer";
  "view" if "owner";
  "edit" if "owner";
  "view" if "viewer" on "repository_tenant";
  "view" if "owner" on "repository_tenant";
  "edit" if "owner" on "repository_tenant";
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

To keep the implementation of this sample application simple, all requests assume the actor is `User{"anonymous"}`. This is configured with the `identify_user_from_request` decorator:

``` python
@oso.identify_user_from_request
async def user(request: Request) -> str:
  return "anonymous"
```

So, this request is authenticated as the `User{"anonymous"}` actor:

```bash
curl localhost:8000/org/acme
```

You can use whatever HTTP client you like for these requests - for these examples, we'll be using `curl`.

# Configuring Authorization Data with Facts

By default, all routes will return a 404 for all users. To get a successful 200 OK response, you'll need to add some **facts** to Oso Cloud.

## Assigning Roles on an `Organization`

The `Organization` resource has two roles:
- the `viewer` role (which grants `view`), and
- the `owner` role (which grants both `view` and `edit`)

By assigning roles to an Actor as a fact, we can authorize access. Roles are assigned to individual instances of a resource - in this case, we'll consider `Organization{"acme"}`.

### `GET /org/acme`

The `get_organization` route is enforced:

```python
@app.get("/org/{id}")
@oso.enforce("{id}", "view", "Organization")
```


To access this route, you'll need to provide the `view` permission. This can be accomplished by adding a fact, which gives `User{"anonymous"}` the `viewer` role:
- `has_role(User{"anonymous"}, "viewer", Organization{"acme"})`

Now, the following request should succeed:

```bash
curl localhost:8000/org/acme
```

### `POST /org/acme`

The `post_organization` route is enforced:

``` python
@app.post("/org/{id}")
@oso.enforce("{id}", "edit", "Organization")
```

This time, instead of the `view` permission, you'll need to provide the `edit` permission.

This can be accomplished by adding a fact which gives `User{"anonymous"}` the `owner` role:
- `has_role(User{"anonymous"}, "owner", Organization{"acme"})`

Now, the following request should succeed:

```bash
curl -X POST localhost:8000/org/acme
```

(This route doesn't require a request body, it is just looking for a POST request.)

## Constructing a Relation with Facts

The resource block definition for `Repository` contains a relation, `repository_tenant`:

```
resource Repository {
  # ...
  relations = { repository_tenant: Organization };
  # ...
}
```

This allows **associating a Repository with an Organization**. We declare this with a fact, which references:
- a specific instance of a `Repository`, and
- a specific instance of an `Organization`.

For example, if we wanted to declare a relationship from `Repository{"code"}` to `Organization{"acme"}`, we could add the following fact to Oso Cloud:

- `has_relation(Repository{"code"}, "repository_tenant", Organization{"acme"})`

This is relevant for a few permissions, defined on the `Repository` resource:
```
resource Repository {
  # ...
  "view" if "viewer" on "repository_tenant";
  "edit" if "owner" on "repository_tenant";
  # ...
}
```

Assuming we declared the relationship between `Repository{"code"}` and `Organization{"acme"}`, this means:
- if an actor has the `viewer` role on `Organization{"acme"}`, they will have the `view` permission on `Repository{"code"}`
- if an actor has the `owner` role on `Organization{"acme"}`, they will have the `edit` permission on `Repository{"code"}`

This gives us some flexbility - we can allow access with a few different approaches.

## `GET /repo/code`

The `get_repository` route is enforced:

```python
@app.get("/repo/{id}")
@oso.enforce("{id}", "view", "Repository")
```

### Allowing `view` through `Repository{"code"}`

To access this route, you'll need to provide the `view` permission. This can be accomplished by adding a fact, which gives `User{"anonymous"}` the `view` permission on the Repository:
- `has_permission(User{"anonymous"}, "view", Repository{"code"})`

This can also be accomplished by giving `User{"anonymous"}` the `viewer` role on the Repository:
- `has_role(User{"anonymous"}, "viewer", Repository{"code"})`

### Allowing `view` through `Organization{"acme"}`

Alternatively, we can allow access by assigning roles on `Organization{"acme"}`:
- `has_role(User{"anonymous"}, "viewer", Organization{"acme"})`

Even though this fact does not reference `Repository{"code"}`, assuming the relation mentioned earlier is defined (`has_relation(Repository{"code"}, "repository_tenant", Organization{"acme"})`), our Polar policy declares that the `view` permission is implied:

> if an actor has the `viewer` role on `Organization{"acme"}`, they will have the `view` permission on `Repository{"code"}`

Now, whichever approach you chose, the following request should succeed:

```bash
curl localhost:8000/repo/code
```

## `POST /repo/code`

The `post_repository` route is enforced:

```python
@app.post("/repo/{id}")
@oso.enforce("{id}", "edit", "Repository")
```

### Allowing `edit` through `Repository{"code"}`

To access this route, you'll need to provide the `edit` permission. As before, we can add a fact to accomplish this directly:
- `has_permission(User{"anonymous"}, "edit", Repository{"code"})`

Or, we can assign the `owner` role, which gives the `edit` permission:
- `has_role(User{"anonymous"}, "owner", Organization{"acme"})`

### Allowing `edit` through `Organization{"acme"}`

Alternatively, we can allow access by assigning roles on `Organization{"acme"}`:
- `has_role(User{"anonymous"}, "owner", Organization{"acme"})`

Again, we're not referencing `Repository{"code"}`, but assuming the relation mentioned earlier is defined (`has_relation(Repository{"code"}, "repository_tenant", Organization{"acme"})`), the Polar policy declares that the `edit` permission is implied:

> if an actor has the `owner` role on `Organization{"acme"}`, they will have the `edit` permission on `Repository{"code"}`

Whichever approach you chose, the following request should succeed:

```bash
curl -X POST localhost:8000/repo/code
```

# Additional Resources

Thanks for taking the time to read through this guide! If you're looking for more information on Oso Cloud and this SDK, check out some of the following resources:

- [Python Oso SDK](https://github.com/osohq/oso-python)
- [Oso Cloud Documentation](https://www.osohq.com/docs)

If you'd like to get in touch, or need some extra help, [check out our Slack!](https://join-slack.osohq.com/?utm_source=starter-policy-sample-application)
