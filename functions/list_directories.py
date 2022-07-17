import os
from botocore.exceptions import ClientError
from settings import image_min_size, operation_parameters_archive, _client
from classes import Timer


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

    if not image_listing:
        return None

    return image_listing


def get_s3_objects(bucket, prefix="", suffix=""):

    kwargs = {
        'Bucket': bucket,
        'Prefix': prefix,
        'Delimiter': '/'
    }

    paginator = _client.get_paginator('list_objects_v2')
    result = paginator.paginate(**kwargs)
    print('results', result)
    for o in result.search('CommonPrefixes'):
        # print(type(o), o.get('Prefix').encode('utf-8'))
        if type(o) is dict:
            yield o.get('Prefix')
            # yield o['Prefix'].decode('utf-8')
