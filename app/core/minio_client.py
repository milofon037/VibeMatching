from io import BytesIO

from minio import Minio
from minio.error import S3Error

from app.core.config import settings


class MinioStorage:
    def __init__(self) -> None:
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket

    def ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload_bytes(self, object_name: str, payload: bytes, content_type: str) -> str:
        self.ensure_bucket()
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_name,
            data=BytesIO(payload),
            length=len(payload),
            content_type=content_type,
        )
        return f"s3://{self.bucket}/{object_name}"

    def remove_object_by_url(self, object_url: str) -> None:
        prefix = f"s3://{self.bucket}/"
        if not object_url.startswith(prefix):
            return
        object_name = object_url.removeprefix(prefix)
        if not object_name:
            return
        try:
            self.client.remove_object(self.bucket, object_name)
        except S3Error:
            # If object is already missing, DB cleanup should still proceed.
            return
