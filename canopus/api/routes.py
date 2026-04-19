from flask import Blueprint, jsonify, request

from canopus.api import limiter
from canopus.api.auth import require_api_key, require_rotate_key
from canopus.config import Config
from canopus.core.crypto import decrypt_data, encrypt_data
from canopus.core.keys import get_keys, rotate_key

bp = Blueprint('api', __name__)
bp.before_request(require_api_key)

_ERROR_STATUS_CODES = {
    'MISSING_FIELD': 400,
    'INVALID_KEY_VERSION': 400,
    'UNSUPPORTED_TYPE': 422,
    'INVALID_CIPHERTEXT': 400,
    'ROTATION_NOT_SUPPORTED': 501,
    'ROTATION_DISABLED': 403,
    'RATE_LIMIT_EXCEEDED': 429,
    'UNAUTHORIZED': 401,
    'INTERNAL_ERROR': 500,
}


def _respond(result: dict) -> tuple:
    if result['status'] == 'error':
        code = result['data'].get('code', 'INTERNAL_ERROR')
        return jsonify(result), _ERROR_STATUS_CODES.get(code, 400)
    return jsonify(result), 200


@bp.route('/rotate-key', methods=['POST'])
@limiter.limit("5 per hour")
def rotate_key_route():
    if not Config.ROTATION_ENABLED:
        return jsonify({
            'status': 'error',
            'data': {'message': 'Key rotation is disabled', 'code': 'ROTATION_DISABLED'},
        }), 403

    auth_error = require_rotate_key()
    if auth_error:
        return auth_error

    try:
        rotate_key()
    except NotImplementedError as e:
        return jsonify({
            'status': 'error',
            'data': {'message': str(e), 'code': 'ROTATION_NOT_SUPPORTED'},
        }), 501
    new_version = len(get_keys()) - 1
    return jsonify({
        'status': 'success',
        'data': {'message': 'Key rotated successfully', 'key_version': new_version}
    }), 200


@bp.route('/encrypt', methods=['POST'])
def encrypt():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            'status': 'error',
            'data': {'message': 'Request body is required', 'code': 'MISSING_FIELD'},
        }), 400
    key_version = request.args.get('key_version', None, type=int)
    return _respond(encrypt_data(data, key_version))


@bp.route('/decrypt', methods=['POST'])
def decrypt():
    data = request.get_json(silent=True)
    if not data or 'ciphertext' not in data:
        return jsonify({
            'status': 'error',
            'data': {
                'message': 'Missing "ciphertext" key in request body',
                'code': 'MISSING_FIELD',
            },
        }), 400
    return _respond(decrypt_data(data['ciphertext']))
