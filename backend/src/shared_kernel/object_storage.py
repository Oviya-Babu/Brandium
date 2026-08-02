"""S3-compatible object storage client (MinIO local / S3 cloud, Technology
Stack §7). All object access is mediated through the backend — no direct
tenant-to-storage access, keeping IAM complexity on the operations side."""
from __future__ import annotations

import uuid

from src.config import get_settings


class ObjectStorageClient:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._bucket = self._settings.s3_bucket_name

    def _client(self):
        import boto3

        return boto3.client(
            "s3",
            endpoint_url=self._settings.s3_endpoint_url,
            aws_access_key_id=self._settings.s3_access_key,
            aws_secret_access_key=self._settings.s3_secret_key,
            region_name=self._settings.s3_region,
        )

    def put_object(self, *, org_id: uuid.UUID, key_prefix: str, filename: str, content: bytes) -> str:
        """Returns the storage_ref (bucket-relative key) — never a
        publicly-resolvable URL, since access is always mediated through
        this backend, not direct-to-storage."""
        key = f"{org_id}/{key_prefix}/{uuid.uuid4()}-{filename}"
        self._client().put_object(Bucket=self._bucket, Key=key, Body=content)
        return key

    def get_object(self, storage_ref: str) -> bytes:
        response = self._client().get_object(Bucket=self._bucket, Key=storage_ref)
        return response["Body"].read()
