from flask import Flask

from spudbin.app import app

from spudbin.app.auth import GithubLogin
from spudbin.app.api import Api

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
