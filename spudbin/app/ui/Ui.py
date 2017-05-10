"""All the UI gubbins"""
from functools import wraps
from datetime import date

from flask import session
from flask import request
from flask import redirect
from flask import render_template

import requests

from spudbin.storage import Database

from spudbin.app import app
from spudbin.app import config

from spudbin.app.auth.GithubLogin import redirect_to_github

from spudbin.storage import Gifs, Gif

GIFS = Gifs()

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

@app.route(config.get('interface', 'application_root') + '/', methods=['GET'])
def ui_root():
    """Default routing for the root path"""
    return redirect(config.get('interface', 'application_root') + '/submit', 302)

@app.route(config.get('interface', 'application_root') + '/submit', defaults={'tokendate': None}, methods=['GET'])
@app.route(config.get('interface', 'application_root') + '/submit/<date:tokendate>', methods=['GET'])
@authenticated
def ui_submit_tokens(tokendate):
    """UI for submitting tokens"""
    username = request.cookies['github_login']
    if tokendate is None:
        tokendate = date.today()
    return render_template('record.html', username=username, date=tokendate, application_root=config.get('interface', 'application_root'))

@app.route(config.get('interface', 'application_root') + '/success/<date:date>', methods=['GET'])
def ui_success(date):
    """What we show when people have successfully submitted tokens"""
    with Database.connection() as connection:
        gif = GIFS.fetch_by_date(date, connection)
        if gif is None:
            new_gif_url = requests.get('http://scrape.3cu.eu/gif').json()['url']
            GIFS.create(Gif(date=date,
                            url=new_gif_url), connection)
            connection.commit()
            gif = GIFS.fetch_by_date(date, connection)

        return render_template('success.html', gif=gif.url, application_root=config.get('interface', 'application_root'))

@app.route(config.get('interface', 'application_root') + '/available', methods=['GET'])
def availability():
    """Simple availability check."""
    return "Howdy", 200

@app.route('/tokenizer/available', methods=['GET'])
def availability2():
    """Simple availability check."""
    return "Howdy2", 200
