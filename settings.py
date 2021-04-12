import os
import yaml
from dotenv import load_dotenv
import boto3
from templates.load_template_settings import load_templates

# define global config settings
# do not need to make these globals...what are globals for?

load_dotenv()

# spaces = {
#     'region_name': os.environ.get("SPACES_REGION"),
#     'endpoint_url': os.environ.get("SPACES_HOST"),
#     'aws_access_key_id': os.environ.get("DO_FOR_AWS_KEY"),
#     'aws_secret_access_key': os.environ.get("DO_FOR_AWS_SECRET")
# }

aws_creds = {
    'aws_access_key_id': os.environ.get("AWS_KEY"),
    'aws_secret_access_key': os.environ.get("AWS_SECRET")
}

# create client for S3
# get session / resource for S3
# _session = boto3.session.Session()
# _resource = _session.resource('s3', **spaces)
# _client = boto3.client('s3', **spaces)
_client = boto3.client('s3', **aws_creds)
_resource = boto3.resource('s3', **aws_creds)

operation_params = {
    'Bucket': '',
    'Body': 'Contents',
    'Key': ''
}

operation_parameters_archive = {
    'Bucket': '',
    'Delimiter': '/'
}


debug_found_directories = []
debug_exists_directories = []
debug_not_found_directories = []
debug_requires_copy = []

image_group_records = []

m_template = '_manifest_template.json'
c_template = '_canvas_template.json'
s_template = '_sequence_template.json'

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(ROOT_DIR, 'templates')
MANIFEST_DIR = os.path.join(ROOT_DIR, 'manifests')

# create the structure for manifests
manifest_template, canvas_template, seq_template = load_templates(TEMPLATE_DIR, m_template, c_template, s_template)

provider = 'aws'

with open('config.yaml') as c:
    config = yaml.load(c, Loader=yaml.FullLoader)
    flags = config['flags']
    source_bucket = f"{config['provider'][provider]['all_bucket']}-sources"
    image_bucket = f"{config['provider'][provider]['all_bucket']}-images"
    web_bucket = f"{config['provider'][provider]['all_bucket']}-web"
    manifest_bucket = f"{config['provider'][provider]['all_bucket']}-manifests"
    main_prefix = config['provider'][provider]['main_prefix']
    source_prefix = config['provider'][provider]['source_prefix']
    general_prefix = config['provider'][provider]['general_prefix']
    target_s3_url = config['provider'][provider]['target_s3_url']
    test_data_file = config['test_data']
    scan_directories = config['scan_directories']
    local_image_listing_file = config['local_image_listing_file']
    local_source_input_file = f'data/{config["local_source_input_file"]}'
    orientation = config['orientation']
    image_processing = config['image_processing']
    image_min_size = config['MIN_IMAGE_SIZE']
    google = config['google']
    logging_config = config['logging_config']
    catalog_field_names = config['catalog_field_names']
