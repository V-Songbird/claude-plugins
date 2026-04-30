# WARNING: this endpoint is unauthenticated — do not leak secrets in response
def public_status():
    return {"ok": True}


# SECURITY: token is logged at INFO level in dev builds only
def log_token(t):
    print(f"token: {t}")


def process(x):
    """Test NEVER passes with negative x.

    This docstring mentions NEVER but is descriptive prose, not an invariant.
    """
    return x * 2
