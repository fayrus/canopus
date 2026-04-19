from canopus.storage.base import KeyStorageBackend

# Requires: pip install "canopus[aws]"
#
# AWS credential resolution is handled automatically by boto3 in this order:
#   1. Environment variables    — AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY
#   2. ~/.aws/credentials file  — standard AWS CLI profile
#   3. ECS task role            — automatic when running in ECS with a task role assigned
#   4. EC2 instance profile     — automatic when running on EC2 with an IAM role
#
# Self-hosted:  set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY as env vars.
# ECS / EC2:    assign an IAM role with secretsmanager:GetSecretValue permission
#               — no extra configuration needed, boto3 picks it up automatically.


class AWSSecretsBackend(KeyStorageBackend):
    """
    AWS Secrets Manager backend.

    Stores all key versions as a JSON array under a single secret:

        Secret name : <secret_name>  (e.g. "canopus/keys/production")
        Secret value: ["base64key0==", "base64key1==", ...]

    Required env vars:
        CANOPUS_AWS_SECRET_NAME   — name of the secret in AWS Secrets Manager
        CANOPUS_AWS_REGION        — AWS region (e.g. "us-east-1")

    The IAM policy for the role/user must allow:
        - secretsmanager:GetSecretValue
        - secretsmanager:PutSecretValue
        - secretsmanager:CreateSecret  (only on first run)
    """

    def __init__(self, secret_name: str, region: str):
        self.secret_name = secret_name
        self.region = region

    def load(self) -> list[bytes]:
        raise NotImplementedError(
            "AWSSecretsBackend is not yet implemented. "
            "Contributions welcome: see canopus/storage/aws_secrets.py"
        )

    def save(self, keys: list[bytes]) -> None:
        raise NotImplementedError(
            "AWSSecretsBackend is not yet implemented. "
            "Contributions welcome: see canopus/storage/aws_secrets.py"
        )
