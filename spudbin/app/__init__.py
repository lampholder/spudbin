"""I hate all this voodoo being in a __init__.py file :("""

from flask import Flask

from spudbin.util import DateConverter

app = Flask(__name__)

app.url_map.converters['date'] = DateConverter
app.secret_key = 'n\xe1\x87\xaaX\xff\xcb\x07\x10\xec\xac\xccX;\x0e\x1f,\xcd\xb2\x8drKf\xa9'
