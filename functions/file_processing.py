import os
import errno
import json
from pathlib import Path
import botocore
from PIL import Image
from settings import flags, scan_directories, local_image_listing_file
from config.config import SOURCE_BUCKET_NAME, TARGET_BUCKET_NAME, put_objs
from functions import get_digital_ocean_images, standardize_digits


def copy_file(_resource, source_key, target_key):

    """
    :param _resource: object, boto3.resource('s3')
    :param source_key:
    :param target_key:
    :return:
    """

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


def create_structure_and_copy(_resource, image_group_path, source_prefix,
                              image_listing, image_group_id):
    # Create target path objects in S3 bucket
    put_params = dict(put_objs)

    dir_sources = '/'.join((image_group_path, scan_directories['sources']))
    dir_images = '/'.join((image_group_path, scan_directories['images']))
    dir_web = '/'.join((image_group_path, scan_directories['web']))

    for path_name in (dir_sources, dir_images, dir_web):
        # print(f'Creating directory: {path_name}')
        put_params['Key'] = f'{path_name}/'
        _resource.meta.client.put_object(**put_params)

    # Copy scans from source to target_sources_dir without renaming and resizing
    # List of file names ['scan01.jpg', 'scan02.jpg'] in source_images_dir

    for image in image_listing['images']:
        # Rename and copy scans from source_images_dir into target_sources_dir
        source_key = ''.join((source_prefix, image))
        target_key = '/'.join((dir_sources, image))
        copy_file(_resource, source_key, target_key)

        # Copy and rename scans from target_sources_dir в target_images_dir
        standard_idx = standardize_digits(image)
        image_ext = Path(image).suffix
        renamed_image = f'{image_group_id}.{standard_idx}{image_ext}'

        # update the source to be previous target (we copy to 'sources', then 'sources' to 'images')
        source_key = target_key
        target_key = '/'.join((dir_images, renamed_image))
        copy_file(_resource, source_key, target_key)


def process_image(local_file_path, image_name, dir_web):

    img = Image.open(local_file_path)
    dpi = img.info['dpi']
    viewing = "top-to-bottom" if img.width >= img.height else "left-to-right"
    # img.load()

    if flags['process_resize'] and all(i > 72 for i in dpi):
        img.save(local_file_path, dpi=(72.0, 72.0))

    image_meta = {'width': img.width, 'height': img.height, 'dpi': dpi, 'viewing': viewing}
    image_processed_key = '/'.join((dir_web, image_name))

    return image_processed_key, image_meta


def create_web_files(_resource, image_group_path):
    dir_images = '/'.join((image_group_path, scan_directories['images']))
    dir_web = '/'.join((image_group_path, scan_directories['web']))
    _bucket = _resource.Bucket(TARGET_BUCKET_NAME)
    # Preparing compressed and resized scans for web,
    #     copy it from target_images_dir to target_web_dir
    # TODO: resizing scans code here
    renamed_image_listing = get_digital_ocean_images(_resource, f'{dir_images}/')

    # temp local directory for storing downloaded/processed image files
    local_dir_path = '/'.join(('data', '_tmp_images', dir_images))
    print(local_dir_path)

    try:
        os.makedirs(local_dir_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            print(f"ERROR: creation of local image directory '{local_dir_path}' failed")
    else:
        print(f"created local image directory '{local_dir_path}'")

    print(f'Download, process, and upload images for web...')
    for image_name in renamed_image_listing['images']:
        # download image file from S3
        local_file_path = '/'.join((local_dir_path, image_name))

        # check if file exists locally already or if overwrite is set to true
        if not Path(local_file_path).is_file() or flags['download_overwrite']:
            image_key = '/'.join((dir_images, image_name))
            _bucket.download_file(image_key, local_file_path)

        # process image file locally
        image_processed_key, image_meta = process_image(local_file_path, image_name, dir_web)
        # add the image meta to image listing
        renamed_image_listing['images_dict'][image_name].update(image_meta)

        if flags['process_upload']:
            try:
                _resource.meta.client.upload_file(
                    local_file_path,
                    TARGET_BUCKET_NAME,
                    image_processed_key,
                    ExtraArgs={'ContentType': 'image/jpeg', 'ACL': 'public-read'}
                )
            except botocore.exceptions.ClientError as e:
                print('upload error', e)

    # if we've uploaded the images to web, then switch out path for manifest in next step
    renamed_image_listing['path'] = dir_web
    local_image_list = '/'.join((local_dir_path, '_image_listing.json'))
    with open(local_image_list, 'w') as file:
        json.dump(renamed_image_listing, file)

    return renamed_image_listing


def upload_manifest(_resource, local_manifest, new_manifest_key):

    print(f"uploading manifest: {new_manifest_key}")

    try:
        _resource.meta.client.upload_file(
            local_manifest,
            TARGET_BUCKET_NAME,
            new_manifest_key,
            ExtraArgs={'ContentType': 'application/json', 'ACL': 'public-read'}
        )

    except botocore.exceptions.ClientError as e:
        print('upload error', e)
