from spudbin.app import app

from spudbin.app.auth import GithubLogin
from spudbin.app.api import Api
from spudbin.app.ui import Ui

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
