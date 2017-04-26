from flask import Flask

from spudbin.api import GithubLogin
from spudbin.api import Api

app = Flask('spudbin')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
