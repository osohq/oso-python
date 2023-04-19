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
