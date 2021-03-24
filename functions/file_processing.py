import os
import errno
import logging
from pathlib import Path
import botocore
import cv2

from settings import flags, orientation, manifest_bucket, source_bucket
from functions import standardize_digits


options_temp = False


def copy_file(_resource, **kwargs):

    from_source = {
        'Bucket': kwargs['from_bucket'],
        'Key': kwargs['from_key'],
    }

    try:
        _resource.meta.client.copy(
            from_source,
            Bucket=kwargs['to_bucket'],
            Key=kwargs['to_key'],
        )
    except botocore.exceptions.ClientError:
        print(f"ERROR: botocore.exceptions.ClientError (copying file {kwargs['from_bucket']}{kwargs['from_key']} =>"
              f" {kwargs['to_bucket']}{kwargs['to_key']})")


def create_structure_and_copy(_resource, image_group_path, source_prefix,
                              image_listing, image_group_id, from_bucket, to_bucket):



    for image in image_listing['images']:

        standard_idx = standardize_digits(image)
        image_ext = Path(image).suffix
        renamed_image = f'{image_group_id}.{standard_idx}{image_ext}'

        from_key = ''.join((source_prefix, image))
        to_key = '/'.join((image_group_path, renamed_image))

        kwargs = {
            'from_bucket': from_bucket,
            'to_bucket': to_bucket,
            'from_key': from_key,
            'to_key': to_key
        }

        copy_file(_resource, **kwargs)


def upload_manifest(_resource, local_manifest, new_manifest_key):

    logging.info(f"uploading manifest: {new_manifest_key}")

    try:
        _resource.meta.client.upload_file(
            local_manifest,
            manifest_bucket,
            new_manifest_key,
            ExtraArgs={'ContentType': 'application/json', 'ACL': 'public-read'}
        )

    except botocore.exceptions.ClientError as e:
        logging.error('upload error', e)


def download_image_for_meta(_resource, image_listing, bucket=source_bucket):

    download_path = 'source_path' if bucket == source_bucket else 'target_path'
    _bucket = _resource.Bucket(bucket)
    # temp local directory for storing downloaded/processed image files
    local_dir_path = '/'.join(('data', '_tmp_images', image_listing[download_path]))

    try:
        os.makedirs(local_dir_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            logging.error(f"ERROR: creation of local image directory '{local_dir_path}' failed")
    else:
        logging.info(f"created local image directory '{local_dir_path}'")

    # print(f'Download, process, and upload images for web...')
    if len(image_listing['images']) < 1:
        return False

    img_idx = 1 if len(image_listing['images']) > 1 else 0
    image_name = image_listing['images'][img_idx]

    # download image file from S3
    local_file_path = '/'.join((local_dir_path, image_name))

    # check if file exists locally already or if overwrite is set to true
    if not Path(local_file_path).is_file() or flags['download_overwrite']:
        image_key = '/'.join((image_listing[download_path], image_name))
        _bucket.download_file(image_key, local_file_path)

    # process image file locally
    img = cv2.imread(local_file_path)
    height, width, _ = img.shape
    viewing = orientation['landscape'] if width >= height else orientation['portrait']
    image_meta = {'width': width, 'height': height, 'viewing': viewing}

    # add the image meta to image listing
    image_listing['images_meta'] = image_meta
    return image_listing
