from flask import Flask

app = Flask('spudbin')

from spudbin.api import GithubLogin
from spudbin.api import Api

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
