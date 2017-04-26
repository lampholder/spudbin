from flask import Flask
from flask import jsonify
from flask import redirect
from flask import request

import requests
import sqlite3
import uuid

from datetime import datetime
from werkzeug.routing import BaseConverter, ValidationError

app = Flask(__name__)

conn = sqlite3.connect('tokens.db')

class DateConverter(BaseConverter):
    """Extracts a ISO8601 date from the path and validates it."""

    regex = r'\d{4}-\d{2}-\d{2}'

    def to_python(self, value):
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError()

    def to_url(self, value):
        return value.strftime('%Y-%m-%d')

app.url_map.converters['date'] = DateConverter

state_thing = []

@app.route('/callback/', methods=['GET'])
def login_complete():
    if request.args['state'] not in state_thing:
        raise Exception
    payload = {'client_id': '1d4a7a5d9ea0d7d0d2e5',
               'client_secret': '04ba5b5171e39058c37e9729a8106e734f7bbe51',
               'code': request.args['code'],
               'redirect_uri': 'https://spudb.in/callback/complete',
               'state': request.args['state']}
    response = requests.post('https://github.com/login/oauth/access_token', data=payload, headers={'Accept': 'application/json'}).json()

    user = requests.get('https://api.github.com/user', params={'access_token': response['access_token']}).json()
    c = conn.cursor();
    print c.execute('delete from humans where login=?', (user['login'], ))
    print c.execute('insert into humans values (null, ?, ?)', (user['login'], response['access_token']))
    conn.commit();
    return user['login']

@app.route('/login')
def redirect_to_github():
    client_id = '1d4a7a5d9ea0d7d0d2e5'
    redirect_uri = 'https://spudb.in/callback/'
    state = str(uuid.uuid4())
    state_thing.append(state)
    url = ( 'https://github.com/login/oauth/authorize' \
          + '?client_id=%s' \
          + '&redirect_uri=%s' \
          + '&state=%s' ) \
          % (client_id, redirect_uri, state)
    return redirect(url, code='302')

@app.route("/template/<string:user>/<date:date>", methods=['GET'])
def get_template(user, date):
    return jsonify(user=user,
                   date=date,
                   template={'id': 1,
                             'buckets':[{'bucket': 'working', 'tags': ['good'], 'description': 'working hard, yeah'},
                                        {'bucket': 'slacking', 'tags': ['bad'], 'description': 'mooching around, wasting time'}]
                            }
                  )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
