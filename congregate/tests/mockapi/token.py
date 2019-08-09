def invalid_token():
    return {
        "error": "invalid_token",
        "error_description": "Token was revoked. You have to re-authorize from the user."
    }