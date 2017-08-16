import ConfigParser

from flask import Flask

from spudbin.app import app
from spudbin.app import config

# Ignore the linter; these guys need to be here:
from spudbin.app.auth import GithubLogin
from spudbin.app.api import Api, Reports
from spudbin.app.ui import Ui

if __name__ == "__main__":
    app.run(host=config.get('interface', 'host'),
            port=config.get('interface', 'port'))
