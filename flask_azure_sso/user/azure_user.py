from flask_login import UserMixin
from datetime import datetime as dt, timezone as tz


class AzureUser(UserMixin):
    def __init__(self, userinfo):
        self.id = userinfo.get("oid")
        self.name = userinfo.get("name")
        self.email = userinfo.get("email")
        self.roles = userinfo.get("roles", [])
        self.groups = userinfo.get("groups", [])
        self.access_token = userinfo.get("access_token")
        self.refresh_token = userinfo.get("refresh_token")
        self.expires_at = userinfo.get("expires_at")

    def get_id(self):
        return self.id

    def is_active(self):
        return dt.now(tz=tz.utc) > dt.fromtimestamp(self.expires_at, tz=tz.utc)

    def is_authenticated(self):
        return self.is_active() and self.access_token is not None

    def is_anonymous(self):
        return False
