"""
S3-compatible storage service for JADWA PDF reports.
Works with MinIO (dev) and real AWS S3 (prod).
"""

import os
from typing import Optional

import boto3
from botocore.config import Config as BotoConfig

from app.core.config import settings


class S3StorageService:
    """S3/MinIO storage for PDF report files."""

    def __init__(self):
        kwargs = {
            "service_name": "s3",
            "region_name": settings.AWS_REGION,
            "config": BotoConfig(signature_version="s3v4"),
        }
        if settings.S3_ENDPOINT:
            kwargs["endpoint_url"] = settings.S3_ENDPOINT
        if settings.AWS_ACCESS_KEY_ID:
            kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        if settings.AWS_SECRET_ACCESS_KEY:
            kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

        self.client = boto3.client(**kwargs)
        self.bucket = settings.S3_BUCKET

    def upload_pdf(self, file_path: str, object_key: str) -> str:
        """Upload a PDF file to S3. Returns the object key."""
        self.client.upload_file(
            Filename=file_path,
            Bucket=self.bucket,
            Key=object_key,
            ExtraArgs={"ContentType": "application/pdf"},
        )
        return object_key

    def generate_presigned_url(self, object_key: str, expires_in: int = 3600) -> str:
        """Generate a presigned download URL.

        If S3_PUBLIC_ENDPOINT is set, replaces the internal endpoint
        in the URL with the public one (for MinIO in Docker).
        """
        url = self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": object_key},
            ExpiresIn=expires_in,
        )
        # Replace internal Docker hostname with public endpoint
        if settings.S3_PUBLIC_ENDPOINT and settings.S3_ENDPOINT:
            url = url.replace(settings.S3_ENDPOINT, settings.S3_PUBLIC_ENDPOINT)
        return url

    def delete_object(self, object_key: str) -> None:
        """Delete an object from S3."""
        self.client.delete_object(Bucket=self.bucket, Key=object_key)

    def object_exists(self, object_key: str) -> bool:
        """Check if an object exists in S3."""
        try:
            self.client.head_object(Bucket=self.bucket, Key=object_key)
            return True
        except Exception:
            return False


# Module-level singleton
_storage: Optional[S3StorageService] = None


def get_storage() -> S3StorageService:
    """Get the singleton storage service instance."""
    global _storage
    if _storage is None:
        _storage = S3StorageService()
    return _storage
