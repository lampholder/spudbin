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

@app.route('/', methods=['GET'])
def ui_root():
    """Default routing for the root path"""
    return redirect('/submit', 302)

@app.route('/submit', defaults={'tokendate': None}, methods=['GET'])
@app.route('/submit/<date:tokendate>', methods=['GET'])
@authenticated
def ui_submit_tokens(tokendate):
    """UI for submitting tokens"""
    username = request.cookies['github_login']
    if tokendate is None:
        tokendate = date.today()
    return render_template('record.html', username=username, date=tokendate)

@app.route('/success/<date:date>', methods=['GET'])
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

        return render_template('success.html', gif=gif.url)
