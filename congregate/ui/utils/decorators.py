from distutils.util import strtobool
from functools import wraps
from flask import request

def enforce_dry_run(function):
    """
        Decorator used to enforce a dry run from an API request

        If a route is decorated with this function, a 'dry_run' kwarg needs to be present in its signature
    """
    @wraps(function)
    def is_committed(*args, **kwargs):
        # Check if true or false was passed in.
        # Any other values will be treated as false and will set dry run to True
        if request.args.get('commit', '').lower() in ['true', 'false']:
            # Parse true/false string as a bool
            if bool(strtobool(request.args.get('commit', False))):
                # If it's true, disable the dry run
                return function(*args, dry_run=False, **kwargs)
        return function(*args, dry_run=True, **kwargs)
    return is_committed
