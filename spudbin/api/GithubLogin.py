import uuid

import requests

from flask import Flask
from flask import jsonify
from flask import redirect
from flask import request

from spudbin.storage import Database
from spudbin.storage import Humans, Human

app = Flask('spudbin')

humans = Humans(Database.connection())
state_tracker = []

@app.route('/callback/', methods=['GET'])
def login_complete():
    if request.args['state'] not in state_tracker:
        raise Exception('Unrecognised state token!')
    payload = {'client_id': '1d4a7a5d9ea0d7d0d2e5',
               'client_secret': '04ba5b5171e39058c37e9729a8106e734f7bbe51',
               'code': request.args['code'],
               'redirect_uri': 'https://spudb.in/callback/complete',
               'state': request.args['state']}
    response = requests.post('https://github.com/login/oauth/access_token',
                             data=payload, headers={'Accept': 'application/json'}).json()

    user = requests.get('https://api.github.com/user',
                        params={'access_token': response['access_token']}).json()

    state_tracker.remove(request.args['state'])

    humans.delete_by_login(user['login'])
    humans.create(Human(pkey=None, login=user['login'], access_token=response['access_token']))
    return user['login']

@app.route('/login')
def redirect_to_github():
    client_id = '1d4a7a5d9ea0d7d0d2e5'
    redirect_uri = 'https://spudb.in/callback/'
    state = str(uuid.uuid4())
    state_tracker.append(state)
    url = ( 'https://github.com/login/oauth/authorize' \
          + '?client_id=%s' \
          + '&redirect_uri=%s' \
          + '&state=%s' ) \
          % (client_id, redirect_uri, state)
    return redirect(url, code='302')
