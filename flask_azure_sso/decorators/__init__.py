from functools import wraps
from flask import session, abort

def requires_role(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = session.get("user")
            if not user or role not in user.get("roles", []):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def requires_group(group):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = session.get("user")
            if not user or group not in user.get("groups", []):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
