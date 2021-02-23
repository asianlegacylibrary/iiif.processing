import os
import yaml
from dotenv import load_dotenv
import boto3
from templates.load_template_settings import load_templates

# define global config settings
global spaces
global flags
global target_bucket
global source_bucket
global target_bucket_endpoint
global source_bucket_endpoint
global test_data_file
global scan_directories
global local_image_listing_file
global orientation
global image_scale_dimension
global catalog_field_names

global debug_found_directories
global debug_exists_directories
global debug_not_found_directories
global debug_requires_copy

global image_group_records

global m_template
global c_template
global s_template
global _session
global _resource
global _client

global ROOT_DIR

global logging_config

load_dotenv()

spaces = {
    'region_name': os.environ.get("SPACES_REGION"),
    'endpoint_url': os.environ.get("SPACES_HOST"),
    'aws_access_key_id': os.environ.get("AWS_KEY"),
    'aws_secret_access_key': os.environ.get("AWS_SECRET")
}

# get session / resource for S3
_session = boto3.session.Session()
_resource = _session.resource('s3', **spaces)
_client = boto3.client('s3', **spaces)


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

# create the structure for manifests
manifest_template, canvas_template, seq_template = load_templates(TEMPLATE_DIR, m_template, c_template, s_template)


with open('config.yaml') as c:
    config = yaml.load(c, Loader=yaml.FullLoader)
    flags = config['flags']
    target_bucket = config['digital_ocean']['target_bucket']
    source_bucket = config['digital_ocean']['source_bucket']
    target_bucket_endpoint = config['digital_ocean']['target_bucket_endpoint']
    source_bucket_endpoint = config['digital_ocean']['source_bucket_endpoint']
    test_data_file = config['test_data']
    scan_directories = config['scan_directories']
    local_image_listing_file = config['local_image_listing_file']
    local_source_input_file = f'data/{config["local_source_input_file"]}'
    orientation = config['orientation']
    image_processing = config['image_processing']
    google = config['google']
    logging_config = config['logging_config']
    catalog_field_names = config['catalog_field_names']
