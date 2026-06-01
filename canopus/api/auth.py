import hmac

from flask import jsonify, request

from canopus.config import Config


def _unauthorized(message: str, code: str):
    return jsonify({'status': 'error', 'data': {'message': message, 'code': code}}), 401


def require_api_key():
    """
    Before-request hook. Validates the X-Canopus-Token header.
    Auth is skipped when CANOPUS_API_KEY is not configured (development mode).
    Uses constant-time comparison to prevent timing attacks.
    """
    api_key = Config.API_KEY
    if not api_key:
        return None  # auth disabled

    token = request.headers.get('X-Canopus-Token', '')
    if not token:
        return _unauthorized('Missing X-Canopus-Token header', 'UNAUTHORIZED')

    if not hmac.compare_digest(token, api_key):
        return _unauthorized('Invalid API key', 'UNAUTHORIZED')

    return None


def require_rotate_key():
    """
    Validates the X-Canopus-Rotate-Token header for /rotate-key.
    Falls back to the main API key if CANOPUS_ROTATE_KEY is not set.
    Auth is skipped entirely when CANOPUS_API_KEY is not configured (development mode).
    """
    if not Config.API_KEY:
        return None  # auth disabled globally

    rotate_key = Config.ROTATE_KEY or Config.API_KEY
    token = request.headers.get('X-Canopus-Rotate-Token', '')
    if not token:
        return _unauthorized('Missing X-Canopus-Rotate-Token header', 'UNAUTHORIZED')

    if not hmac.compare_digest(token, rotate_key):
        return _unauthorized('Invalid rotate key', 'UNAUTHORIZED')

    return None
