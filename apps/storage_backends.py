import boto3
from django.conf import settings


def delete_by_key(key):
    session = boto3.Session(aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, )
    s3client = session.client('s3')
    s3client.delete_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=key
    )
