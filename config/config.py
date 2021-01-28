import os
import sys
from dotenv import load_dotenv

load_dotenv()

config = {
    'region_name': os.environ.get("SPACES_REGION"),
    'endpoint_url': os.environ.get("SPACES_HOST"),
    'aws_access_key_id': os.environ.get("AWS_KEY"),
    'aws_secret_access_key': os.environ.get("AWS_SECRET"),

}

BUCKET_ENDPOINT = os.environ.get("SPACES_ENDPOINT")
SOURCE_BUCKET_NAME = 'acip'
TARGET_BUCKET_NAME = 'acip'

TARGET_BUCKET_TEST_ENDPOINT = 'scans/unpublished'
SOURCE_BUCKET_TEST_ENDPOINT = 'staging_test/'

ACIP_PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
# sys.path.append(ACIP_PYTHON_DIR)

MANIFEST_ALL_IMAGES = True
MANIFEST_SAVE_DIR = '../manifests'
MIN_IMAGE_SIZE = 32


# data_dir = 'manifests'
# get s3 images for manifest
# spaces_dir = 'V8LS16868_I8LS16897_3-738'

flags = {
    "copy": True,
    "manifest": True

}

put_objs = {
    'Bucket': 'acip',
    'Body': 'Contents',
    'Key': ''
}

operation_parameters = {
    'Bucket': 'acip',
    'Delimiter': '/'
}
