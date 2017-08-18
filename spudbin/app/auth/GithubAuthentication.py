"""Decorators providing authentication from GitHub"""
from functools import wraps

import requests

from flask import request
from flask import session

from spudbin.app.auth.GithubLogin import redirect_to_github

class GitHubAuthenticator(object):
    """Decorators for handling GitHub UI Authentication."""

    @staticmethod
    def is_authentic(username, token):
        """Checks with Github that this person is who they say they are."""
        auth_test = requests.get('https://api.github.com/user',
                                 params={'access_token': token})

        is_authenticated = (auth_test.status_code == 200 and
                            'login' in auth_test.json() and
                            auth_test.json()['login'] == username)
        return is_authenticated

class GitHubAPIAuthenticator(GitHubAuthenticator):
    """Specific decorators for API auth (returns a formatted error on fail)"""

    @classmethod
    def authenticated(cls, func):
        """Only checks that this person is who they say they are"""
        @wraps(func)
        def wrapped(*args, **kwargs):
            """Wrapper function, obvs"""
            username = request.headers.get('Github-Login')
            token = request.headers.get('Github-Auth-Token')

            if not cls.is_authentic(username, token):
                return 'I don\'t know who you are, or I don\'t believe you are ' + \
                       'who you say you are.', 401
            return func(*args, **kwargs)
        return wrapped


class GitHubUIAuthenticator(GitHubAuthenticator):
    """Specific decorators for UI auth (redirects to GitHub login on fail)"""

    @classmethod
    def authenticated(cls, func):
        """Only checks that this person is who they say they are"""
        @wraps(func)
        def wrapped(*args, **kwargs):
            """Wrapper function, obvs"""
            username = request.cookies.get('github_login')
            token = request.cookies.get('github_auth_token')

            if not cls.is_authentic(username, token):
                session['target_url'] = request.url
                return redirect_to_github()
            return func(*args, **kwargs)
        return wrapped
