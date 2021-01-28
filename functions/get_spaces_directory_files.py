import os
from dotenv import load_dotenv
import boto3
from config.config import config, operation_parameters, BUCKET_ENDPOINT


# boto3.set_stream_logger('botocore', level='DEBUG')

load_dotenv()


def go_through_directory():
    
    client = boto3.client('s3', **config)

    result = client.list_objects(**operation_parameters)
    dirs = []
    for o in result.get('CommonPrefixes'):
        # print('sub folder : ', o.get('Prefix'))
        print(o)
        dirs.append(o.get('Prefix'))

    # return result
    return dirs


def get_spaces_directory_files():

    session = boto3.session.Session()
    # client is low level, returns dicts
    # client = session.client('s3', **config)

    # resource is high level and generally returns instances of bucket / objects
    # if you need client you can access through resource.meta.client (as below)
    resource = session.resource('s3', **config)

    # response = client.list_objects(Bucket='acip')
    paginator = resource.meta.client.get_paginator('list_objects')

    page_iterator = paginator.paginate(**operation_parameters)

    image_listing = {}
    # paginate
    for page in page_iterator:
        # page contents correspond to image groups
        images = []
        page_key = page['ResponseMetadata'].get('RequestId', 'some_key')  # need a random key gen if no req id present
        for group in page['Contents']:
            [dir_path, image_name] = os.path.split(group.get('Key'))
            images.append(os.path.join(BUCKET_ENDPOINT, dir_path, image_name))

        image_listing.update({page_key: images})

    return image_listing
