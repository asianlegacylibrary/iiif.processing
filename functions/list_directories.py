import os
import boto3
from botocore.exceptions import ClientError
from config.config import MIN_IMAGE_SIZE, BUCKET_ENDPOINT, operation_parameters, config, SOURCE_BUCKET_TEST_ENDPOINT


def list_test_directories():
    client = boto3.client('s3', **config)
    result = client.list_objects(**operation_parameters)
    return result


def list_client_directories(_client, bucket='acip', main_directory=''):
    op = dict(operation_parameters)
    op['Prefix'] = main_directory
    op['Bucket'] = bucket
    dirs = []

    try:
        result = _client.list_objects(**op)
    except ClientError as e:
        print('error', e)
        return None

    if 'CommonPrefixes' in result:
        for o in result.get('CommonPrefixes', None):
            dirs.append(o.get('Prefix'))

    return dirs


def get_digital_ocean_images(_resource, source_address):
    op = dict(operation_parameters)
    op['Prefix'] = source_address

    paginator = _resource.meta.client.get_paginator('list_objects')
    page_iterator = paginator.paginate(**op)

    image_listing = {}
    # paginate
    for page in page_iterator:
        # print(page)
        # page contents correspond to image groups
        images = []
        images_dict = {}
        page_key = page['ResponseMetadata'].get('RequestId',
                                                'some_key')  # need a random key gen if no req id present
        for group in page['Contents']:
            if group.get('Size', 0) < MIN_IMAGE_SIZE:
                continue
            [dir_path, image_name] = os.path.split(group.get('Key'))
            images.append(image_name)
            images_dict[image_name] = {}

        if images:
            image_listing.update({
                'key': page_key,
                'path': dir_path,
                'source_path': source_address,
                'images': images,
                'images_dict': images_dict
            })

    return image_listing
