import os
import yaml
from dotenv import load_dotenv


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

load_dotenv()

spaces = {
    'region_name': os.environ.get("SPACES_REGION"),
    'endpoint_url': os.environ.get("SPACES_HOST"),
    'aws_access_key_id': os.environ.get("AWS_KEY"),
    'aws_secret_access_key': os.environ.get("AWS_SECRET")
}

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
