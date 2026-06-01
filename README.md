# Canopus

A lightweight encryption-as-a-service inspired by HashiCorp Vault. Canopus exposes a simple HTTP API to encrypt and decrypt data, with support for key rotation and pluggable storage backends.

## Features

- Encrypt and decrypt strings, numbers, JSON objects, and arrays
- Key versioning — ciphertexts carry their key version, old versions remain decryptable after rotation
- Pluggable storage backends: local file, SQLite, PostgreSQL/MySQL, environment variable, AWS Secrets Manager (stub)
- Pluggable cipher backends with compliance-oriented options (HIPAA, HITRUST, SOC2, PCI DSS)
- Consistent JSON API with machine-readable error codes

## Authentication

All endpoints require an `X-Canopus-Token` header when `CANOPUS_API_KEY` is configured:

```http
POST /encrypt
X-Canopus-Token: your-secret-key
```

If `CANOPUS_API_KEY` is not set, authentication is disabled — useful for local development. In production, always set a strong API key.

## Quickstart

**Requirements:** Python 3.12+

```bash
git clone https://github.com/fayrus/canopus.git
cd canopus
python -m venv venv && source venv/bin/activate
python -m pip install -e .
python app.py
```

The server starts on `http://localhost:2107`.

## API

### Encrypt

```http
POST /encrypt
Content-Type: application/json

{"plaintext": "hello world"}
```

```json
{
  "status": "success",
  "data": {
    "ciphertext": "canopus:v0:gAAAAABp..."
  }
}
```

### Decrypt

```http
POST /decrypt
Content-Type: application/json

{"ciphertext": "canopus:v0:gAAAAABp..."}
```

```json
{
  "status": "success",
  "data": {
    "plaintext": "hello world"
  }
}
```

### Rotate key

```http
POST /rotate-key
X-Canopus-Rotate-Token: your-rotate-key
```

```json
{
  "status": "success",
  "data": {
    "message": "Key rotated successfully",
    "key_version": 1
  }
}
```

Rate limited to **5 requests per hour** per IP. The endpoint can be disabled entirely via `CANOPUS_ROTATION_ENABLED=false`.

All error responses follow the same structure:

```json
{
  "status": "error",
  "data": {
    "message": "Human-readable description",
    "code": "MACHINE_READABLE_CODE"
  }
}
```

## Ciphertext format

```
canopus:v{version}:{cipher}:{token}
```

Both the key version and cipher are embedded in the ciphertext — clients never need to track them separately. The cipher alias is a single character to minimize string length.

## Cipher backends

Select the cipher via `CANOPUS_CIPHER` environment variable.

| Alias | Cipher | Use case |
|---|---|---|
| `f` | AES-128-CBC + HMAC-SHA256 (Fernet) | Default — general purpose |
| `g` | AES-256-GCM | HIPAA, HITRUST, SOC2, PCI DSS |
| `c` | AES-256-CBC + HMAC-SHA256 | FIPS 140-2 conservative environments |

```bash
CANOPUS_CIPHER=g   # use AES-256-GCM for compliance
```

> **Note:** The cipher alias is kept intentionally opaque in the ciphertext — `g` does not publicly advertise which algorithm is in use.

## Configuration

All configuration is done via environment variables.

| Variable | Default | Description |
|---|---|---|
| `CANOPUS_API_KEY` | _(empty)_ | API key for authentication. Leave empty to disable (dev mode) |
| `CANOPUS_ROTATE_KEY` | _(empty)_ | Separate key required to call `/rotate-key` via `X-Canopus-Rotate-Token`. Falls back to `CANOPUS_API_KEY` if unset |
| `CANOPUS_ROTATION_ENABLED` | `true` | Set to `false` to disable `/rotate-key` entirely |
| `CANOPUS_CIPHER` | `f` | Active cipher: `f` (Fernet), `g` (AES-256-GCM), `c` (AES-256-CBC) |
| `CANOPUS_STORAGE_BACKEND` | `file` | Active storage backend |
| `CANOPUS_DEBUG` | `false` | Enable Flask debug mode |
| `CANOPUS_PORT` | `2107` | Port to listen on |

## Storage backends

### `file` (default)

Stores keys in a local file. Simple, zero dependencies.

```bash
CANOPUS_STORAGE_BACKEND=file
CANOPUS_KEYS_FILE=keys.txt   # optional, default: keys.txt
```

### `sqlite`

Stores keys in a SQLite database. No extra dependencies.

```bash
CANOPUS_STORAGE_BACKEND=sqlite
CANOPUS_SQLITE_PATH=canopus.db   # optional, default: canopus.db
```

### `database`

Stores keys in any SQLAlchemy-supported database (PostgreSQL, MySQL, SQLite).

```bash
CANOPUS_STORAGE_BACKEND=database
CANOPUS_DATABASE_URL=postgresql://user:pass@host/dbname
```

Install the required driver:

```bash
# PostgreSQL
python -m pip install "canopus[postgres]"

# MySQL
python -m pip install "canopus[mysql]"
```

### `env`

Loads keys from an environment variable. **Read-only** — key rotation is not supported with this backend.
Useful for ephemeral environments or testing.

```bash
CANOPUS_STORAGE_BACKEND=env
CANOPUS_KEYS=<base64-fernet-key>   # comma-separated for multiple versions
```

Generate a key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### `aws_secrets`

Stores keys in AWS Secrets Manager. Requires `pip install "canopus[aws]"`.

> **Status:** stub — contributions welcome. See [`canopus/storage/aws_secrets.py`](canopus/storage/aws_secrets.py).

```bash
CANOPUS_STORAGE_BACKEND=aws_secrets
CANOPUS_AWS_SECRET_NAME=canopus/keys/production
CANOPUS_AWS_REGION=us-east-1        # optional, default: us-east-1
```

AWS credentials are resolved automatically by boto3:
- **ECS / EC2:** assign an IAM task/instance role — no extra config needed
- **Self-hosted:** set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

Minimum IAM permissions required:

```json
{
  "Effect": "Allow",
  "Action": [
    "secretsmanager:GetSecretValue",
    "secretsmanager:PutSecretValue",
    "secretsmanager:CreateSecret"
  ],
  "Resource": "arn:aws:secretsmanager:<region>:<account>:secret:canopus/*"
}
```

## Docker

Build and run the image locally:

```bash
cp .env.example .env
docker build -t canopus:dev .
docker run --rm --env-file .env -p 2107:2107 canopus:dev
```

## Development

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
```

## Name

Canopus is named after the Decree of Canopus (238 BC) — a precursor to the Rosetta Stone, inscribed in three scripts so it could be read by all. The parallel felt right for a service that transforms data between readable and unreadable forms.

## License

[GNU Affero General Public License v3.0](LICENSE) — if you run a modified version of Canopus as a network service, you must make the source code available to its users. You may use Canopus as part of a larger system, but any modifications to Canopus itself must remain open source.
