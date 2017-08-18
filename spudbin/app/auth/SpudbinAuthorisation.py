"""Decorators applying authorisation"""
from functools import wraps

from flask import request

from spudbin.app import config

ADMINS = config.get('app', 'admin').split(',')

class SpudbinAuthoriser(object):
    """Handles authorisation of access to resources"""

    @staticmethod
    def authorised(func):
        """Checks that the user is allowed to do what they're trying to do. Very simple perms
        model - either you're doing an action to yourself, or you're an admin."""
        @wraps(func)
        def wrapped(*args, **kwargs):
            """Wrapper function, obvs"""
            if 'username' in kwargs:
                doer = request.headers.get('Github-Login')
                doee = kwargs['username']
                if doer != doee and doer not in ADMINS:
                    # Very simplistic authorisation model right now
                    return 'The person you\'re claiming to be isn\'t allowed to do this', 403
            return func(*args, **kwargs)
        return wrapped

    @staticmethod
    def admin_only(func):
        """Checks that the username is in the admin set - must always be used in conjunction
        with @authenticated else it's useless."""
        @wraps(func)
        def wrapped(*args, **kwargs):
            "Wrapper function, obvs"""
            doer = request.headers.get('Github-Login')
            if doer not in ADMINS:
                return 'The person you\'re claiming to be isn\'t allowed to do this', 403
            return func(*args, **kwargs)
        return wrapped
