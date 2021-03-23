import os
import errno
import json
import logging
from pathlib import Path
import botocore
from PIL import Image

from settings import flags, scan_directories, orientation, image_processing, source_bucket, image_bucket, \
    operation_params, main_bucket, _client, manifest_bucket
from functions import get_image_listing, standardize_digits
from typing import Tuple, Union
import numpy as np
import cv2
import math
from deskew import determine_skew

options_temp = False

def process_rotate(
        image: np.ndarray, angle: float, background: Union[int, Tuple[int, int, int]]
) -> np.ndarray:

    old_width, old_height = image.shape[:2]
    angle_radian = math.radians(angle)

    width = abs(np.sin(angle_radian) * old_height) + abs(np.cos(angle_radian) * old_width)
    height = abs(np.sin(angle_radian) * old_width) + abs(np.cos(angle_radian) * old_height)

    image_center = tuple(np.array(image.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
    rot_mat[1, 2] += (width - old_width) / 2
    rot_mat[0, 2] += (height - old_height) / 2

    return cv2.warpAffine(image, rot_mat, (int(round(height)), int(round(width))), borderValue=background)


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


def _copy_file(_resource, source_key, target_key):

    """
    :param _resource: object, boto3.resource('s3')
    :param source_key:
    :param target_key:
    :return:
    """

    copy_source = {
        'Bucket': source_bucket,
        'Key': source_key,
    }

    try:
        _resource.meta.client.copy(
            copy_source,
            Bucket=image_bucket,
            Key=target_key,
        )
    except botocore.exceptions.ClientError:
        print(f"ERROR: botocore.exceptions.ClientError (copying file {source_key} => {target_key})")


def create_structure_and_copy(_resource, image_group_path, source_prefix,
                              image_listing, image_group_id):

    # Copy scans from source to target_sources_dir without renaming and resizing
    # List of file names ['scan01.jpg', 'scan02.jpg'] in source_images_dir
    # print(source_prefix, image_group_path)

    if options_temp == False:
        results = _client.list_objects(Bucket=image_bucket, Prefix=image_group_path)

        # print(f'Do not overwrite, already exists {results}')
        if 'Contents' in results:
            print(f'{image_group_path} exists in the all-library-image S3')
            # debug_exists_directories.append(image_group_path)
            return False

    for image in image_listing['images']:
        # Rename and copy scans from source_images_dir into target_sources_dir
        # from_bucket = main_bucket
        # to_bucket = source_bucket
        # from_key = ''.join((source_prefix, image))
        # to_key = '/'.join((image_group_path, image))
        #
        # params = {
        #     'from_bucket': from_bucket,
        #     'to_bucket': to_bucket,
        #     'from_key': from_key,
        #     'to_key': to_key
        # }
        #
        # copy_file(_resource, **params)

        # Copy and rename scans from target_sources_dir в target_images_dir
        standard_idx = standardize_digits(image)
        image_ext = Path(image).suffix
        renamed_image = f'{image_group_id}.{standard_idx}{image_ext}'



        # update the source to be previous target (we copy to 'sources', then 'sources' to 'images')
        from_bucket = main_bucket
        to_bucket = image_bucket
        # from_key = to_key
        from_key = ''.join((source_prefix, image))
        to_key = '/'.join((image_group_path, renamed_image))

        params = {
            'from_bucket': from_bucket,
            'to_bucket': to_bucket,
            'from_key': from_key,
            'to_key': to_key
        }

        copy_file(_resource, **params)

        #### NOTE >>> LAMBDA FUNCTION HERE ###########################################
        # This is where the lambda function would trigger
        # When the renamed image is copied into 'images' folder
        # The event of a new image appearing would trigger copy / process image to 'web' folder'
        #### #########################################################################


def _create_structure_and_copy(_resource, image_group_path, source_prefix,
                              image_listing, image_group_id):
    # Create target path objects in S3 bucket
    put_params = dict(operation_params)
    put_params['Bucket'] = image_bucket

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
        #### NOTE >>> LAMBDA FUNCTION HERE ###########################################
        # This is where the lambda function would trigger
        # When the renamed image is copied into 'images' folder
        # The event of a new image appearing would trigger copy / process image to 'web' folder'
        #### #########################################################################

def process_image(local_file_path, image_name, dir_web):

    # img = Image.open(local_file_path)
    # width = img.width
    # height = img.height

    # dpi = img.info['dpi']
    #
    # img.load()

    img = cv2.imread(local_file_path)
    height, width, _ = img.shape

    if image_processing['resize'] and any(i > image_processing['scaling'] for i in [height, width]):

        scale_percent = image_processing['scaling']/max([height, width])
        width = int(img.shape[1] * scale_percent)
        height = int(img.shape[0] * scale_percent)

        img = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)

    viewing = orientation['landscape'] if width >= height else orientation['portrait']

    if image_processing['rotate']:
        grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        angle = determine_skew(grayscale)
        if angle is not None and float(angle):
            img = process_rotate(img, angle, (0, 0, 0))

    # overwrite img file
    cv2.imwrite(local_file_path, img)

    image_meta = {'width': width, 'height': height, 'viewing': viewing}
    image_processed_key = '/'.join((dir_web, image_name))

    return image_processed_key, image_meta


def create_web_files(_resource, image_group_path):
    _bucket = _resource.Bucket(image_bucket)

    dir_images = '/'.join((image_group_path, scan_directories['images']))
    dir_web = '/'.join((image_group_path, scan_directories['web']))

    renamed_image_listing = get_image_listing(_resource, f'{dir_images}/')
    if not renamed_image_listing:
        return None
    # temp local directory for storing downloaded/processed image files
    local_dir_path = '/'.join(('data', '_tmp_images', dir_images))

    try:
        os.makedirs(local_dir_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            logging.error(f"ERROR: creation of local image directory '{local_dir_path}' failed")
    else:
        logging.info(f"created local image directory '{local_dir_path}'")

    # print(f'Download, process, and upload images for web...')
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

        if flags['file_upload']:
            try:
                _resource.meta.client.upload_file(
                    local_file_path,
                    image_bucket,
                    image_processed_key,
                    ExtraArgs={'ContentType': 'image/jpeg', 'ACL': 'public-read'}
                )
            except botocore.exceptions.ClientError as e:
                logging.error('upload error', e)

    # if we've uploaded the images to web, then switch out path for manifest in next step
    renamed_image_listing['target_path'] = dir_web
    local_image_list = '/'.join((local_dir_path, '_image_listing.json'))
    with open(local_image_list, 'w') as file:
        json.dump(renamed_image_listing, file)

    return renamed_image_listing


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


def download_image_for_meta(_resource, image_listing, bucket=main_bucket):

    download_path = 'source_path' if bucket == main_bucket else 'target_path'
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
