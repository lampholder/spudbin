"""I hate all this voodoo being in a __init__.py file :("""

from flask import Flask

from spudbin.util import DateConverter

app = Flask(__name__)

app.url_map.converters['date'] = DateConverter
app.secret_key = 'He\'s a lumberjack and he\'s okay'
