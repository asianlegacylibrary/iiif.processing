import os
from dotenv import load_dotenv

load_dotenv()

config = {
    'region_name': os.environ.get("SPACES_REGION"),
    'endpoint_url': os.environ.get("SPACES_HOST"),
    'aws_access_key_id': os.environ.get("AWS_KEY"),
    'aws_secret_access_key': os.environ.get("AWS_SECRET"),

}

conf_gs = {
    "scope": [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ],
    "credentials": {
        "iiif": "config/credentials.json",
        "nlm": "config/credentials_gs_old.json"
    },
    "sheet_key": "1-YPHZj1-YVPs7FW0p5IFKgw4qcGCRklg4WdmDEHuQZs",
    "sheet_key_test": "1scb2UMLbuuDoGYlnOcFvpW9ZjC54Z6bbiEUeEj-LQQs",
    "sheet_mongolia_test": "1SLgnUq4ohrAODB-XNQ6oiVqQxxJmeR0IQPozSpW6xiw",
    "sheet_names_filter": "new",
    "sheet_mongolia_filter": "acip-title-level"
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
    "manifest": True,
    "create_web_files": True
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
