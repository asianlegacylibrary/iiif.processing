import botocore
from config.config import SOURCE_BUCKET_NAME, TARGET_BUCKET_NAME, put_objs
from functions import get_directory_images


# TODO: скопировать файлы
def copy_files(_resource, files_listing, source_dir, target_dir):

    """
    :param _resource: object, boto3.resource('s3')
    :param files_listing: list of file names ['scan01.jpg', 'scan02.jpg']
    :param source_dir:
    :param target_dir:
    :return:
    """

    for image in files_listing['images']:
        source_key = ''.join((source_dir, image))
        target_key = '/'.join((target_dir, image))

        print(f"copy file: source_bucket_name='{SOURCE_BUCKET_NAME}', "
              f"source_key='{source_key}' \n  => target_bucket_name='{TARGET_BUCKET_NAME}', "
              f"target_key='{target_key}'")

        copy_source = {
            'Bucket': SOURCE_BUCKET_NAME,
            'Key': source_key,
        }

        try:
            _resource.meta.client.copy(
                copy_source,
                Bucket=TARGET_BUCKET_NAME,
                Key=target_key,
            )
        except botocore.exceptions.ClientError:
            print(f"ERROR: botocore.exceptions.ClientError (copying file {source_key} => {target_key})")


# TODO: скопировать файлы
def copy_file(_resource, source_key, target_key):

    """
    :param _resource: object, boto3.resource('s3')
    :param source_key:
    :param target_key:
    :return:
    """

    print(f"copy file: source_bucket_name='{SOURCE_BUCKET_NAME}', "
          f"source_key='{source_key}' \n  => target_bucket_name='{TARGET_BUCKET_NAME}', "
          f"target_key='{target_key}'")

    copy_source = {
        'Bucket': SOURCE_BUCKET_NAME,
        'Key': source_key,
    }

    try:
        _resource.meta.client.copy(
            copy_source,
            Bucket=TARGET_BUCKET_NAME,
            Key=target_key,
        )
    except botocore.exceptions.ClientError:
        print(f"ERROR: botocore.exceptions.ClientError (copying file {source_key} => {target_key})")


def create_structure_and_copy(_resource, dir_sources, dir_images, dir_web, source_prefix,
                              image_listing, image_group_id):
    # Create target path objects in S3 bucket
    put_params = dict(put_objs)

    for path_name in (dir_sources, dir_images, dir_web):
        print(f'Creating directory: {path_name}')
        put_params['Key'] = f'{path_name}/'
        _resource.meta.client.put_object(**put_params)

    # Copy scans from source to target_sources_dir without renaming and resizing
    # List of file names ['scan01.jpg', 'scan02.jpg'] in source_images_dir

    # Rename and copy scans from source_images_dir into target_sources_dir
    for image in image_listing['images']:
        source_key = ''.join((source_prefix, image))
        target_key = '/'.join((dir_sources, image))
        copy_file(_resource, source_key, target_key)

    # Copy and rename scans from target_sources_dir в target_images_dir
    image_ext = image_listing['images'][0].split(".")[-1]  # scans extension

    # TODO: переделать на def - копирование с переименованием
    for i, image in enumerate(image_listing['images']):
        # Format for renaming: image_group_id.000X.jpg
        renamed_image = '.'.join([image_group_id, ('%04d' % (i + 1)), image_ext])
        source_key = '/'.join((dir_sources, image))
        target_key = '/'.join((dir_images, renamed_image))
        copy_file(_resource, source_key, target_key)

        # temp
        target_key = '/'.join((dir_web, renamed_image))
        copy_file(_resource, source_key, target_key)
