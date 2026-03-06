# app.py
import boto3
import os

def read_from_s3():
    s3 = boto3.client(
        's3',
        region_name=os.getenv('AWS_REGION', 'us-east-2')
    )

    bucket = os.getenv('S3_BUCKET_NAME')
    key    = os.getenv('S3_FILE_KEY', 'data/file.txt')

    response = s3.get_object(Bucket=bucket, Key=key)
    content  = response['Body'].read().decode('utf-8')

    print(f" Read from S3: {content}")
    return content

if __name__ == "__main__":
    read_from_s3()