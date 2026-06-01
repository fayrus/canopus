from canopus.api import create_app
from canopus.config import Config

app = create_app()

if __name__ == '__main__':
    app.run(host=Config.HOST, debug=Config.DEBUG, port=Config.PORT)
