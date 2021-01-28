import os
import json
import boto3
from pprint import pprint as pretty
from pathlib import Path
import sys
from config.config import config, spaces_dir
from templates.placeholder_values import p as placeholder_values
from functions import get_spaces_directory_files, go_through_directory, \
    load_templates, update_json_placeholders, update_canvas_items, configure_logger, get_image_index, \
    list_directory_files, list_test_directories, build_manifest_template_structure

from dotenv import load_dotenv

load_dotenv()

# config = {
#     'region_name': os.environ.get("SPACES_REGION"),
#     'endpoint_url': os.environ.get("SPACES_HOST"),
#     'aws_access_key_id': os.environ.get("AWS_KEY"),
#     'aws_secret_access_key': os.environ.get("AWS_SECRET")
# }

# SOURCE_BUCKET_NAME = os.environ.get("SOURCE_BUCKET_NAME")


# Don't list & process images less than N bytes in size (sanity check).


# https://aciptest.sfo2.digitaloceanspaces.com/ISKS1RC748/web/ISKS1RC748-IG.ISKS1RC748.001/
# https://aciptest.sfo2.digitaloceanspaces.com/ISKS1RC748/web/ISKS1RC748-IG.ISKS1RC748.001/IG.ISKS1RC748.001.0001.JPG


if __name__ == "__main__":
    print("current working directory:", os.path.abspath(os.path.curdir))

    configure_logger()

    # get s3 images for manifest

    # request all directories (w/o iterating files itself)
    # spaces_all_dirs = list_test_directories(**config)
    spaces_all_dirs = list_directory_files(spaces_dir)
    print(spaces_all_dirs)
    quit()
    # just list all space pages (might search for a specific page name here)
    for spaces_pages in spaces_all_dirs.get('CommonPrefixes'):
        address = spaces_pages.get('Prefix')
        print(f"address prefix={address}")
        quit()
        spaces_dir = address.split("/")[-2]

        build_manifest_template_structure(address, spaces_dir)

        # DEBUG: break after 1st iteration
        # quit()



# CommonPrefixes to get 1st level directories
# for response in paginator.paginate(**operation_parameters):
#     for x in response.get('CommonPrefixes', []):
#         if x['Prefix'] == 'scans/published/V8LS16868_I8LS16897_3-738/':
#             print(x)
'''
build_manifests(page, spaces_dir)
'''