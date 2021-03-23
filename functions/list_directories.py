import os
import boto3
from botocore.exceptions import ClientError
from settings import operation_params, image_min_size, operation_parameters_archive, main_bucket


def list_test_directories(**kwargs):
    client = boto3.client('s3', **kwargs)
    result = client.list_objects(**operation_params)
    return result


def list_all_directories(_client, main_directory='/', bucket='acip'):
    op = dict(operation_params)
    op['Prefix'] = main_directory
    op['Bucket'] = bucket
    dirs = []

    try:
        result = _client.list_objects(**op)
    except ClientError as e:
        print('error', e)
        return None
    response = s3.list_objects_v2(
        Bucket=bucket,
        Prefix='DIR1/DIR2',
        MaxKeys=100)


def list_client_directories(_client, bucket='acip', main_directory=''):
    op = dict(operation_parameters_archive)
    op['Prefix'] = main_directory
    op['Bucket'] = bucket
    dirs = []

    try:
        result = _client.list_objects_v2(**op)
    except ClientError as e:
        print('error', e)
        return None

    if 'CommonPrefixes' in result:
        for o in result.get('CommonPrefixes', None):
            dirs.append(o.get('Prefix'))

    return dirs


def get_image_listing(_resource, from_address, to_address, from_bucket, source_address=None):

    op = dict(operation_parameters_archive)
    op['Bucket'] = from_bucket
    op['Prefix'] = from_address

    paginator = _resource.meta.client.get_paginator('list_objects')
    page_iterator = paginator.paginate(**op)


    image_listing = {}
    # paginate
    for page in page_iterator:
        if 'Contents' not in page:
            continue

        # page contents correspond to image groups
        images = []
        images_dict = {}
        images_meta = {}
        page_key = page['ResponseMetadata'].get('RequestId',
                                                'some_key')  # need a random key gen if no req id present
        for group in page['Contents']:
            if group.get('Size', 0) < image_min_size:
                continue
            [dir_path, image_name] = os.path.split(group.get('Key'))
            images.append(image_name)
            images_dict[image_name] = {}

        if images:
            image_listing.update({
                'key': page_key,
                'source_path': source_address if source_address is not None else from_address,
                'target_path': to_address,
                'images_meta': images_meta,
                'images': images,
                'images_dict': images_dict
            })

    return image_listing


def _get_digital_ocean_images(_resource, source_address):

    op = dict(operation_parameters_archive)
    op['Bucket'] = main_bucket
    op['Prefix'] = source_address

    paginator = _resource.meta.client.get_paginator('list_objects')
    page_iterator = paginator.paginate(**op)


    image_listing = {}
    # paginate
    for page in page_iterator:

        if 'Contents' not in page:
            continue

        # page contents correspond to image groups
        images = []
        images_dict = {}
        page_key = page['ResponseMetadata'].get('RequestId',
                                                'some_key')  # need a random key gen if no req id present
        for group in page['Contents']:
            if group.get('Size', 0) < image_min_size:
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