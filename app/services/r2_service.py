from __future__ import annotations

import mimetypes
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import boto3
from botocore.config import Config

from app.config import settings


class R2Storage:
    def __init__(self) -> None:
        self.endpoint = settings.r2_endpoint
        self.access_key_id = settings.r2_access_key_id
        self.secret_access_key = settings.r2_secret_access_key
        self.bucket = settings.r2_bucket
        self.region = settings.r2_region or "auto"
        self.public_url = settings.r2_public_url.rstrip("/")

        if not all([self.endpoint, self.access_key_id, self.secret_access_key, self.bucket]):
            raise ValueError("Cloudflare R2 credentials are not configured")

        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            region_name=self.region,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            config=Config(signature_version="s3v4"),
        )

    def upload_bytes(self, key: str, data: bytes, content_type: str | None = None) -> str:
        mime_type = content_type or mimetypes.guess_type(key)[0] or "application/octet-stream"
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=mime_type,
        )
        return self.public_url + "/" + key.lstrip("/")

    def generate_presigned_url(self, key: str, expires_seconds: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )

    def upload_local_file(self, key: str, file_path: str | Path, content_type: str | None = None) -> str:
        path = Path(file_path)
        return self.upload_bytes(key=key, data=path.read_bytes(), content_type=content_type)


def get_r2_storage() -> R2Storage:
    return R2Storage()
