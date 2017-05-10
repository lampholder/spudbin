import ConfigParser
from spudbin.app import app, config

if __name__ == "__main__":
    app.run(host=config.get('interface', 'host'),
            port=config.get('interface', 'port'))
