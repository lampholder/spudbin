"""All the UI gubbins"""
from functools import wraps

from flask import session
from flask import request
from flask import render_template

from spudbin.app import app
from spudbin.app.auth.GithubLogin import redirect_to_github

def authenticated(func):
    """Checks that we have a github token - if not, bounce via login to get one"""
    @wraps(func)
    def wrapped(*args, **kwargs):
        """PaRapper the wrapper"""
        if 'github_token' not in request.cookies or 'github_login' not in request.cookies:
            session['target_url'] = request.url
            print 'persisting destination', session['target_url']
            return redirect_to_github()

        return func(*args, **kwargs)
    return wrapped

@app.route('/', methods=['GET'])
@authenticated
def ui_submit_tokens():
    """UI for submitting tokens"""
    username = request.cookies['github_login']
    return render_template('record.html', username=username)
