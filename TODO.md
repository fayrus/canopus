# Canopus — Roadmap

## Phase 1 — Foundation

### 1. Project structure ✓
- [x] Create package layout: `canopus/`, `tests/`, `docs/`
- [x] Move `main.py` logic into `canopus/` modules (`api/`, `core/`, `storage/`)
- [x] Add `pyproject.toml` (replace bare `requirements.txt`)
- [x] Update `.gitignore` to exclude `keys.txt` and other secrets

### 2. Key Storage abstraction (drivers) ✓
- [x] Define `KeyStorageBackend` abstract interface
- [x] Implement `LocalFileBackend` (migrate current behavior)
- [x] Implement `SQLiteBackend`
- [x] Implement `EnvBackend` (keys from environment variables, for dev)
- [x] Implement `DatabaseBackend` — Postgres / MySQL / SQLite via SQLAlchemy
- [x] Stub `AWSSecretsBackend` (interface only, implementation later)

### 3. Environment-based config ✓
- [x] Create `canopus/config.py` driven by env vars
  - `CANOPUS_STORAGE_BACKEND` — selects the active driver
  - `CANOPUS_DEBUG` — replaces hardcoded `debug=True`
  - `CANOPUS_PORT` — configurable port
- [x] Remove all hardcoded paths and values from source

### 4. Cipher abstraction (compliance) ✓
- [x] Define `CipherBackend` abstract interface
- [x] Implement `FernetCipher` — `f` — AES-128-CBC + HMAC-SHA256 (default, current behavior)
- [x] Implement `AES256GCMCipher` — `g` — AES-256-GCM (HIPAA / HITRUST / SOC2 / PCI DSS)
- [x] Implement `AES256CBCCipher` — `c` — AES-256-CBC + HMAC-SHA256 (FIPS 140-2 conservative)
- [x] Update ciphertext format: `canopus:v{version}:{cipher_alias}:{token}`
- [x] Config: `CANOPUS_CIPHER` env var — selects the active cipher (default: `f`)
- [x] Update OpenAPI spec to document new ciphertext format and cipher aliases

## Phase 2 — Quality

### 5. Tests ✓
- [x] Set up `pytest` with coverage
- [x] Unit tests for `encrypt_data` / `decrypt_data` per cipher
- [x] Unit tests for each storage backend
- [x] Integration tests for API endpoints (`/encrypt`, `/decrypt`, `/rotate-key`)

### 6. Code cleanup ✓
- [x] Remove dead code in `main.py` (or delete the file entirely)

## Phase 3 — Operational

### 7. Authentication ✓
- [x] API key middleware via `X-Canopus-Token` header
- [x] Config: `CANOPUS_API_KEY` env var

### 8. Dockerfile + README ✓
- [x] `README.md` with quickstart, API reference, and driver docs
- [x] `Dockerfile` with multi-stage build (builder + runtime)
- [x] `docker-compose.yml` — profiles for file, PostgreSQL, and MySQL
