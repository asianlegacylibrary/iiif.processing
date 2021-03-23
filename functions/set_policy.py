import json
import boto3
from settings import _client, source_bucket

def create_bucket_policy():
    print(source_bucket)
    # Create a bucket policy
    bucket_policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Sid': 'AddPerm',
            'Effect': 'Allow',
            'Principal': '*',
            'Action': ['*'],
            'Resource': f'arn:aws:s3:::{source_bucket}/*'
        }]
    }

    # Convert the policy from JSON dict to string
    bucket_policy = json.dumps(bucket_policy)

    # Set the new policy
    _client.put_bucket_policy(Bucket=source_bucket, Policy=bucket_policy)
