from storages.backends.s3boto3 import S3Boto3Storage

class WhiteboardStorage(S3Boto3Storage):
    bucket_name = "whiteboards"  # or os.environ["BUCKET_NAME"]
