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


def get_image_listing(_resource):
    print(f"get_image_listing (spaces_dir={operation_parameters['Prefix']})")

    op = dict(operation_parameters)
    paginator = _resource.meta.client.get_paginator('list_objects')

    # pretty(operation_parameters)
    massive_image_listing = []
    for d in create_directory_listing():
        print(d, d.split('/')[-2])
        
        op['Prefix'] = d
        page_iterator = paginator.paginate(**op)

        image_listing = {}
        # paginate
        for page in page_iterator:
            # page contents correspond to image groups
            images = []
            page_key = page['ResponseMetadata'].get('RequestId',
                                                    'some_key')  # need a random key gen if no req id present
            for group in page['Contents']:
                if group.get('Size', 0) < MIN_IMAGE_SIZE:
                    continue
                [dir_path, image_name] = os.path.split(group.get('Key'))
                # images.append(os.path.join(config['endpoint_url'], dir_path, image_name))
                # images.append(os.path.join(BUCKET_ENDPOINT, dir_path, image_name))
                images.append('/'.join((BUCKET_ENDPOINT, dir_path, image_name)))

            if images:
                image_listing.update({'key': d.split('/')[-2], 'images': images})
                # image_listing.update({page_key: images})

        # print(image_listing)
        if image_listing:
            massive_image_listing.append(image_listing)

    # return image_listing
    return massive_image_listing


def get_directory_images(_resource, source_address):
    print(f"get_directory_images (prefix={source_address})")

    op = dict(operation_parameters)
    op['Prefix'] = source_address

    paginator = _resource.meta.client.get_paginator('list_objects')
    page_iterator = paginator.paginate(**op)

    image_listing = {}
    # paginate
    for page in page_iterator:
        print(page)
        # page contents correspond to image groups
        images = []
        page_key = page['ResponseMetadata'].get('RequestId',
                                                'some_key')  # need a random key gen if no req id present
        for group in page['Contents']:
            if group.get('Size', 0) < MIN_IMAGE_SIZE:
                continue
            [dir_path, image_name] = os.path.split(group.get('Key'))
            images.append(image_name)

        if images:
            image_listing.update({
                'key': page_key,
                'path': dir_path,
                'source_path': source_address,
                'images': images})

    return image_listing


def list_directory_files(address):
    print(f"list_directory_files(spaces_dir={address})")

    session = boto3.session.Session()
    resource = session.resource('s3', **config)

    paginator = resource.meta.client.get_paginator('list_objects')

    # pretty(operation_parameters)
    # op = operation_parameters.update()
    d = operation_parameters['Prefix']

    page_iterator = paginator.paginate(**operation_parameters)

    image_listing = {}
    # paginate
    for page in page_iterator:
        # page contents correspond to image groups
        images = []
        page_key = page['ResponseMetadata'].get('RequestId', 'some_key')  # need a random key gen if no req id present
        for group in page['Contents']:
            if group.get('Size', 0) < MIN_IMAGE_SIZE:
                continue
            [dir_path, image_name] = os.path.split(group.get('Key'))
            # images.append(os.path.join(config['endpoint_url'], dir_path, image_name))
            # images.append(os.path.join(BUCKET_ENDPOINT, dir_path, image_name))
            images.append('/'.join((BUCKET_ENDPOINT, dir_path, image_name)))

        if images:
            image_listing.update({'key': d, 'images': images})
        # image_listing.update({page_key: images})

    return image_listing
