import uuid

import requests

from flask import session
from flask import redirect
from flask import request
from flask import make_response

from spudbin.storage import Database
from spudbin.storage import Users, User

from spudbin.app import app
from spudbin.app import config

users = Users()

#XXX: This is smelly:
state_tracker = []

@app.route(config.get('interface', 'application_root') + '/auth/callback/', methods=['GET'])
def login_complete():
    if request.args['state'] not in state_tracker:
        raise Exception('Unrecognised state token!')
    payload = {'client_id': config.get('github', 'client_id'),
               'client_secret': config.get('github', 'client_secret'),
               'code': request.args['code'],
               'state': request.args['state']}
    github = requests.post('https://github.com/login/oauth/access_token',
                           data=payload, headers={'Accept': 'application/json'}).json()

    user = requests.get('https://api.github.com/user',
                        params={'access_token': github['access_token']}).json()

    state_tracker.remove(request.args['state'])

    with Database.connection() as connection:
        existing_user = users.fetch_by_username(user['login'], connection)
        if existing_user is None: 
            users.create(User(pkey=None, username=user['login']), connection)
        connection.commit()

    response = make_response(redirect(session['target_url'], 302))
    response.set_cookie('github_login', user['login'])
    response.set_cookie('github_auth_token', github['access_token'])
    return response

@app.route(config.get('interface', 'application_root') + '/auth/login')
def redirect_to_github():
    client_id = config.get('github', 'client_id')
    state = str(uuid.uuid4())
    state_tracker.append(state)
    url = ( 'https://github.com/login/oauth/authorize' \
          + '?client_id=%s' \
          + '&state=%s' ) \
          % (client_id, state)
    print 'Redirecting to this place on request', url
    return redirect(url, code='302')
