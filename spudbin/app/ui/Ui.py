"""All the UI gubbins"""
from functools import wraps
from datetime import datetime

from flask import session
from flask import request
from flask import redirect
from flask import render_template

from spudbin.app import app
from spudbin.app.auth.GithubLogin import redirect_to_github

def authenticated(func):
    """Checks that we have a github token - if not, bounce via login to get one"""
    @wraps(func)
    def wrapped(*args, **kwargs):
        """PaRapper the wrapper"""
        if 'github_auth_token' not in request.cookies or 'github_login' not in request.cookies:
            session['target_url'] = request.url
            print 'persisting destination', session['target_url']
            return redirect_to_github()

        return func(*args, **kwargs)
    return wrapped

@app.route('/', methods=['GET'])
def ui_root():
    """Default routing for the root path"""
    return redirect('/submit', 302)

@app.route('/submit', defaults={'date': None}, methods=['GET'])
@app.route('/submit/<date:date>', methods=['GET'])
@authenticated
def ui_submit_tokens(date):
    """UI for submitting tokens"""
    username = request.cookies['github_login']
    if date is None:
        date = datetime.today()
    return render_template('record.html', username=username, date=date)

@app.route('/success', methods=['GET'])
def ui_success():
    """What we show when people have successfully submitted tokens"""
    return "YOU ARE A GOOD PERSON THANKS"
