"""All the UI gubbins"""
from datetime import date

from flask import request
from flask import redirect
from flask import render_template
from flask import abort

import requests

from spudbin.storage import Database

from spudbin.app import app
from spudbin.app import config

from spudbin.app.auth import GitHubUIAuthenticator

from spudbin.storage import Gifs, Gif

GIFS = Gifs()

@app.route(config.get('interface', 'application_root') + '/', methods=['GET'])
def ui_root():
    """Default routing for the root path"""
    return redirect(config.get('interface', 'application_root') + '/submit', 302)

@app.route(config.get('interface', 'application_root') + '/interpolated/<string:filename>', methods=['GET'])
def interpolated_css(filename):
    """Handles the annoying problem of static css files not knowing that we're now living
    in a subdirectory"""
    whitelist = ['submit.css', 'success.css']
    print filename in whitelist
    if filename in whitelist:
        return render_template(filename,
                               application_root=config.get('interface', 'application_root'))
    abort(404)

@app.route(config.get('interface', 'application_root') + '/submit', defaults={'tokendate': None}, methods=['GET'])
@app.route(config.get('interface', 'application_root') + '/submit/<date:tokendate>', methods=['GET'])
@GitHubUIAuthenticator.authenticated
def ui_submit_tokens(tokendate):
    """UI for submitting tokens"""
    username = request.cookies['github_login']
    if tokendate is None:
        tokendate = date.today()
    return render_template('submit.html', username=username, date=tokendate,
                           application_root=config.get('interface', 'application_root'))

@app.route(config.get('interface', 'application_root') + '/success/<date:submissiondate>', methods=['GET'])
def ui_success(submissiondate):
    """What we show when people have successfully submitted tokens"""
    with Database.connection() as connection:
        gif = GIFS.fetch_by_date(submissiondate, connection)
        if gif is None:
            new_gif_url = requests.get('http://scrape.3cu.eu/gif').json()['url']
            GIFS.create(Gif(date=submissiondate,
                            url=new_gif_url), connection)
            connection.commit()
            gif = GIFS.fetch_by_date(submissiondate, connection)

        return render_template('success.html', gif=gif.url,
                               application_root=config.get('interface', 'application_root'))

@app.route(config.get('interface', 'application_root') + '/available', methods=['GET'])
def availability():
    """Simple availability check."""
    return "Howdy", 200

@app.route(config.get('interface', 'application_root') + '/whoHasTokenized', methods=['GET'])
def who_has_tokenized():
    """Render the graphs."""
    usernames = request.args.get('usernames')
    report_url = ('%s/api/whoHasTokenized?usernames=%s&start=%s&end=%s'
                  % (config.get('interface', 'application_root'),
                     usernames,
                     request.args.get('start'),
                     request.args.get('end')))

    return render_template('who_has_tokenized.html',
                           report_url=report_url)

@app.route(config.get('interface', 'application_root') + '/graph', methods=['GET'])
@GitHubUIAuthenticator.authenticated
def graph():
    """Render the graphs."""
    username = (request.args.get('usernames')
                if request.args.get('usernames')
                else request.cookies['github_login'])
    tags = request.args.get('tags') if request.args.get('tags') else ''
    stacked = 'percent' if request.args.get('stacked') == 'percent' else 'true'
    report_url = ('%s/api/reports?usernames=%s&start=%s&end=%s&groupBy=%s&timeWindow=%s&tags=%s'
                  % (config.get('interface', 'application_root'),
                     username,
                     request.args.get('start'),
                     request.args.get('end'),
                     request.args.get('groupBy'),
                     request.args.get('timeWindow'),
                     tags))

    return render_template('graph.html',
                           username=username,
                           report_url=report_url,
                           stacked=stacked)
