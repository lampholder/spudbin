"""I hate all this voodoo being in a __init__.py file :("""
import ConfigParser
import json
import sys

from flask import Flask

from spudbin.util import DateConverter
from spudbin.util import CustomJSONEncoder

#TODO: This really doesn't feel like it should be here :(
if len(sys.argv) != 2:
    sys.stderr.write('No config file filename provided; please run: python run.py <config_filename>\n')
    exit(1)
config_file = sys.argv[1]

config = ConfigParser.RawConfigParser()
config.read(config_file)

admins = config.get('app', 'admin').split(',')

app = Flask(__name__,
            static_url_path=config.get('interface', 'application_root') + '/static',
            static_folder='static')

app.url_map.converters['date'] = DateConverter

app.json_encoder = CustomJSONEncoder

app.secret_key = 'n\xe1\x87\xaaX\xff\xcb\x07\x10\xec\xac\xccX;\x0e\x1f,\xcd\xb2\x8drKf\xa9'

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response
