"""I hate all this voodoo being in a __init__.py file :("""
import ConfigParser
import json

from flask import Flask

from spudbin.util import DateConverter

config = ConfigParser.RawConfigParser()
config.read('spudbin.conf')

admins = tuple(json.loads(config.get('app', 'admin')))

app = Flask(__name__,
            static_url_path=config.get('interface', 'application_root') + '/static',
            static_folder='static')

app.url_map.converters['date'] = DateConverter

app.secret_key = 'n\xe1\x87\xaaX\xff\xcb\x07\x10\xec\xac\xccX;\x0e\x1f,\xcd\xb2\x8drKf\xa9'

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response
