from storages.backends.s3boto3 import S3Boto3Storage
import os

class WhiteboardStorage(S3Boto3Storage):
    bucket_name = os.environ["BUCKET_NAME"]
