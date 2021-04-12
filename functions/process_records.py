import collections
import logging
from tqdm import tqdm
from botocore import exceptions
from settings import _client, target_s3_url, image_bucket, source_bucket, \
    debug_found_directories, debug_exists_directories, debug_requires_copy, \
    manifest_template, canvas_template, seq_template, catalog_field_names, image_group_records, _resource, \
    manifest_bucket, web_bucket
from functions import build_manifest, get_image_listing, create_structure_and_copy, \
    upload_manifest, download_image_for_meta
from classes import TermColors, Timer


def write_results_to_terminal():
    print(f'{TermColors.OKBLUE}Processed records for: {debug_found_directories}{TermColors.ENDC}')
    print(f'{TermColors.WARNING}These directories skipped, already exist: {debug_exists_directories}{TermColors.ENDC}')
    print(f'{TermColors.OKCYAN}These require to run COPY: {debug_requires_copy}{TermColors.ENDC}')

    print(f'Processed image group records: {image_group_records}')


def process_file(data):
    header_line = data.readline().replace(" ", "").replace("#", "")
    field_names = header_line.split('\t').toLower()
    # Last element will be '\n', it's invalid field name,
    #  so use "rename=True" to auto-rename such fields to "_1", "_2" etc
    CsvLineClass = collections.namedtuple('CSVLine', field_names, rename=True)

    for line in data:
        web_image_listing = None  # reset the image listing, in cases we're pulling locally
        record = CsvLineClass._make(line.split('\t'))
        if not process_record(record, web_image_listing):
            continue

    write_results_to_terminal()


def process_dataframe(data, options):
    tqdm.pandas()
    data.progress_apply(lambda x: process_record(x, options), axis=1)
    write_results_to_terminal()


# PROCESS RECORD ################################################
# Each record represents an image group (group of images / scans)
# RECORD = 1 image group, 1 manifest, multiple images
# manifest is the viewing data for an image group
# need to create an ITEM record that links to the image group
@Timer(name="record")
def process_record(record, options):

    # define necessary fields from record, create image group vars
    item_uid = record[catalog_field_names['item_uid']]
    record_source_path = record[catalog_field_names['directory_path']]
    image_group_uid = record[catalog_field_names['image_group_uid']]
    image_group_path = '/'.join((item_uid, image_group_uid))

    # COPY // Copy images from staging and create a directory structure for (source, images, web)
    if options["copy"] == 'True':

        if options['image_group_overwrite'] == False:
            results = _client.list_objects(Bucket=source_bucket, Prefix=image_group_path)
            if 'Contents' in results:
                logging.warning(f'\n{image_group_path} exists in the all-library-images S3')
                # debug_exists_directories.append(image_group_path)
                return False

        # gather image listing from digital ocean for this catalog record
        image_listing = get_image_listing(_resource, record_source_path, image_group_path, source_bucket)

        create_structure_and_copy(_resource, image_group_path,
                                  record_source_path, image_listing, image_group_uid, source_bucket, image_bucket)

    # MANIFEST // Generate the manifest.json for the IIIF server
    if options["manifest"] == 'True':
        # results = _client.list_objects(Bucket=image_bucket, Prefix=image_group_path)
        # print(results)
        try:
            resp = _client.head_object(Bucket=image_bucket, Prefix=image_group_path)
            print(resp)
        except exceptions.ClientError:
            print(f'\n{image_group_path} has not been copied to all-library-images S3')
            return False

        # if 'Contents' not in results:
        #     print(f'\n{image_group_path} has not been copied to all-library-images S3')
        #     # debug_exists_directories.append(image_group_path)
        #     return False
        # renamed_image_listing = get_image_listing(_resource, f'{dir_images}/')
        image_listing = get_image_listing(_resource, f'{image_group_path}/', image_group_path,
                                                  image_bucket, source_address=record_source_path)

        image_listing = download_image_for_meta(_resource, image_listing, image_bucket)

        # Is there other data to add to the record here?
        manifest_name = f'{item_uid}.{image_group_uid}.manifest.json'
        # url_suffix = f'{general_prefix}/{item_uid}/{image_group_uid}'
        url_suffix = f'{item_uid}/{image_group_uid}'

        # is this an item? that points to an image group?
        image_group_record = {
            'manifest_url': f'https://{image_bucket}.{target_s3_url}/{url_suffix}/{manifest_name}',
            'item_uid': item_uid,
            'image_group_path': image_listing['target_path'],
            'image_group_uid': image_group_uid,
            'number_of_images': len(image_listing['images'])
        }
        image_group_records.append(image_group_record)

        record_merged = {
            **record.to_dict(),
            **image_group_record
        }

        new_manifest_name = item_uid + '.' + image_group_uid + '.manifest.json'

        local_manifest = build_manifest(image_listing, manifest_template, canvas_template,
                                        seq_template, record_merged)

        upload_manifest(_resource, local_manifest, new_manifest_name)

    # create listing of processed records
    debug_found_directories.append(record_source_path)

    return True


def copy_record(record, options):

    # print(f'Processing {len(debug_found_directories)+1} of {total_records}')
    # define necessary fields from record, create image group vars
    item_uid = record[catalog_field_names['item_uid']]
    record_source_path = record[catalog_field_names['directory_path']]
    image_group_uid = record[catalog_field_names['image_group_uid']]
    # create IG path
    image_group_path = '/'.join((item_uid, image_group_uid))

    if options['image_group_overwrite'] == 'False':
        # results = _client.list_objects(Bucket=image_bucket, Prefix=image_group_path)
        # print(results)
        size_sources = sum(1 for _ in _resource.Bucket(source_bucket).objects.filter(Prefix=record_source_path))
        size_images = sum(1 for _ in _resource.Bucket(image_bucket).objects.filter(Prefix=image_group_path))
        size_web = sum(1 for _ in _resource.Bucket(web_bucket).objects.filter(Prefix=image_group_path))
        if size_images == size_sources == size_web:
            # print(image_group_path, size_sources, size_images, size_web)
            # print(f'\n{image_group_path} exists in the all-library-images S3')
            debug_exists_directories.append(image_group_path)
            return False
        elif 0 < size_images < size_sources:
            print(f'Images: {size_images} /// Source: {size_sources}, for {image_group_path} ({size_sources})')
        elif 0 < size_web < size_images:
            print(f'Web: {size_web} /// Images: {size_images}, for {image_group_path} ({size_sources})')
        else:
            print(f'About to process: {image_group_path} ({size_sources}, {size_images}, {size_web}')

    # gather image listing from digital ocean for this catalog record
    # image_listing = get_image_listing(_resource, record_source_path, image_group_path, source_bucket)
    #
    # if image_listing is None:
    #     print(f'{record_source_path} has no images, skipping...')
    #     logging.warning(f'{record_source_path} has no images, skipping...')
    #     return False

    create_structure_and_copy(_resource, image_group_path,
                              record_source_path, image_group_uid, source_bucket, image_bucket)

    # create listing of processed records
    debug_found_directories.append(record_source_path)

    return True


def process_manifest(record, options):

    # define necessary fields from record, create image group vars
    item_uid = record[catalog_field_names['item_uid']]
    record_source_path = record[catalog_field_names['directory_path']]
    image_group_uid = record[catalog_field_names['image_group_uid']]
    image_group_path = '/'.join((item_uid, image_group_uid))

    # Is there other data to add to the record here?
    manifest_name = f'{item_uid}.{image_group_uid}.manifest.json'
    # url_suffix = f'{general_prefix}/{item_uid}/{image_group_uid}'
    url_suffix = f'{item_uid}/{image_group_uid}'

    # print(f'{image_group_path}/{manifest_name}')

    # try:
    #     _client.head_object(Bucket=manifest_bucket, Key=f'{manifest_name}')
    #     print('exists, skip')
    #     return False
    # except exceptions.ClientError:
    #     pass

    image_listing = get_image_listing(_resource, f'{image_group_path}/', image_group_path,
                                              image_bucket, source_address=record_source_path)

    if image_listing is None or not image_listing:
        logging.warning(f'{record_source_path} has no images, skipping...')
        return False

    image_listing = download_image_for_meta(_resource, image_listing, image_bucket)

    # is this an item? that points to an image group?
    image_group_record = {
        'manifest_url': f'https://{image_bucket}.{target_s3_url}/{url_suffix}/{manifest_name}',
        'item_uid': item_uid,
        'image_group_path': image_listing['target_path'],
        'image_group_uid': image_group_uid,
        'number_of_images': len(image_listing['images'])
    }
    image_group_records.append(image_group_record)

    record_merged = {
        **record,
        **image_group_record
    }

    new_manifest_name = item_uid + '.' + image_group_uid + '.manifest.json'

    local_manifest = build_manifest(image_listing, manifest_template, canvas_template,
                                    seq_template, record_merged)

    upload_manifest(_resource, local_manifest, new_manifest_name)

    # create listing of processed records
    debug_found_directories.append(record_source_path)

    return True