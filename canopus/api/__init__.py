from flask import Flask, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from canopus.config import get_cipher_backend, get_storage_backend
from canopus.core import crypto, keys

limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])


def create_app() -> Flask:
    app = Flask(__name__)
    limiter.init_app(app)

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({
            'status': 'error',
            'data': {'message': 'Rate limit exceeded', 'code': 'RATE_LIMIT_EXCEEDED'},
        }), 429

    cipher = get_cipher_backend()
    keys.init(get_storage_backend(), cipher)
    crypto.init_cipher(cipher)
    from canopus.api.routes import bp
    app.register_blueprint(bp)
    return app
