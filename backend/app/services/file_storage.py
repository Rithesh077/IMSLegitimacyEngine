import os
import shutil
from abc import ABC, abstractmethod
from fastapi import UploadFile

try:
    import boto3
    from botocore.exceptions import NoCredentialsError
except ImportError:
    boto3 = None
    NoCredentialsError = Exception

class FileStorage(ABC):
    @abstractmethod
    async def save(self, file: UploadFile, filename: str) -> str:
        """Save file and return the URL/Path"""
        pass

class LocalStorage(FileStorage):
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    async def save(self, file: UploadFile, filename: str) -> str:
        file_path = os.path.join(self.upload_dir, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # Return relative URL assuming /uploads is mounted
        return f"/uploads/{filename}"

class S3Storage(FileStorage):
    def __init__(self):
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.endpoint_url = os.getenv("AWS_ENDPOINT_URL") # Optional: For self-hosted S3/MinIO
        if boto3 is None:
            raise Exception("boto3 is not installed. Please install it to use S3Storage.")
            
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=self.region,
            endpoint_url=self.endpoint_url
        )

    async def save(self, file: UploadFile, filename: str) -> str:
        try:
            self.s3_client.upload_fileobj(
                file.file,
                self.bucket_name,
                filename,
                ExtraArgs={'ACL': 'public-read'} # Make it public or handle presigned URLs
            )
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{filename}"
        except NoCredentialsError:
            raise Exception("AWS Credentials not available")
        except Exception as e:
            raise Exception(f"S3 Upload Failed: {str(e)}")

def get_storage_service() -> FileStorage:
    storage_type = os.getenv("STORAGE_TYPE", "LOCAL").upper()
    if storage_type == "S3":
        return S3Storage()
    return LocalStorage()
