from functools import wraps

import requests

from flask import request

# Auth decorators
def authenticated(func):
    """Only checks that this person is who they say they are"""
    @wraps(func)
    def wrapped(*args, **kwargs):
        """Wrapper function, obvs"""
        username = request.headers.get('Github-Login')
        token = request.headers.get('Github-Auth-Token')

        auth_test = requests.get('https://api.github.com/user',
                                 params={'access_token': token})

        is_authed = (auth_test.status_code == 200 and
                     'login' in auth_test.json() and
                     auth_test.json()['login'] == username)
        if not is_authed:
            return 'I don\'t know who you are, or I don\'t believe you are ' + \
                   'who you say you are.', 401
        return func(*args, **kwargs)
    return wrapped

def authorised(func):
    """Checks that the user is allowed to do what they're trying to do. Very simple perms model -
    either you're doing an action to yourself, or you're an admin."""
    @wraps(func)
    def wrapped(*args, **kwargs):
        """Wrapper function, obvs"""
        if 'username' in kwargs:
            doer = request.headers.get('Github-Login')
            doee = kwargs['username']
            if doer != doee and doer not in admins:
                # Very simplistic authorisation model right now
                return 'The person you\'re claiming to be isn\'t allowed to do this', 403
        return func(*args, **kwargs)
    return wrapped

def admin_only(func):
    """Checks that the username is in the admin set - must always be used in conjunction
    with @authenticated else it's useless."""
    @wraps(func)
    def wrapped(*args, **kwargs):
        "Wrapper function, obvs"""
        doer = request.headers.get('Github-Login')
        if doer not in admins:
            return 'The person you\'re claiming to be isn\'t allowed to do this', 403
        return func(*args, **kwargs)
    return wrapped
