from pathlib import Path
import json
import collections
from tqdm import tqdm
from settings import flags, target_bucket_endpoint, scan_directories, target_bucket, \
    debug_found_directories, debug_exists_directories, debug_requires_copy, \
    manifest_template, canvas_template, seq_template, _client, _resource, catalog_field_names, image_group_records
from functions import build_manifest, get_digital_ocean_images, create_structure_and_copy, \
    create_web_files, upload_manifest
from classes import TermColors


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

        if flags['test_run']:
            quit()

    write_results_to_terminal()


def process_dataframe(data, options):
    tqdm.pandas()
    data.progress_apply(lambda x: process_record(x, options, web_image_listing=None), axis=1)
    write_results_to_terminal()


# PROCESS RECORD ################################################
# Each record represents an image group (group of images / scans)
# RECORD = 1 image group, 1 manifest, multiple images
# manifest is the viewing data for an image group
# need to create an ITEM record that links to the image group
def process_record(record, options, web_image_listing):
    # define necessary fields from record, create image group vars
    item_uid = record[catalog_field_names['item_uid']]
    digital_ocean_dir_path = record[catalog_field_names['directory_path']]
    # TODO - need a volume tag, how many volumes does the book have? Available in CSV file
    image_group_id = 'IG.' + item_uid + '.001'
    image_group_path = '/'.join((target_bucket_endpoint, item_uid, image_group_id))

    # check if processed directory already exists in digital ocean S3
    if not options["image_group_overwrite"]:
        results = _client.list_objects(Bucket=target_bucket, Prefix=image_group_path)
        if 'Contents' in results:
            debug_exists_directories.append(image_group_path)
            return False

    # gather image listing from digital ocean for this catalog record
    image_listing = get_digital_ocean_images(_resource, digital_ocean_dir_path)

    # COPY // Copy images from staging and create a directory structure for (source, images, web)
    if options["copy"]:
        create_structure_and_copy(_resource, image_group_path,
                                  digital_ocean_dir_path, image_listing, image_group_id)

    # PROCESS // Process the images for the web folder (these are for the manifest)
    # currently this involves resolution and tilt
    if options["web"]:
        web_image_listing = create_web_files(_resource, image_group_path)
        if web_image_listing is None:
            debug_requires_copy.append(digital_ocean_dir_path)
            return False

        # Is there other data to add to the record here?
        manifest_name = f'{item_uid}.{image_group_id}.manifest.json'
        url_suffix = f'{target_bucket_endpoint}/{item_uid}/{image_group_id}'

        # is this an item? that points to an image group?
        image_group_records.append({
            'manifest_url': f'https://{target_bucket}.sfo2.digitaloceanspaces.com/{url_suffix}/{manifest_name}',
            'item_uid': item_uid,
            'image_group_path': web_image_listing['path'],
            'image_group_uid': image_group_id,
            'number_of_images': len(web_image_listing['images'])
        })

    # MANIFEST // Generate the manifest.json for the IIIF server
    if options["manifest"]:
        if web_image_listing is None:
            dir_images = '/'.join((image_group_path, scan_directories['images']))
            local_dir_path = '/'.join(('data', '_tmp_images', dir_images))
            local_image_list = '/'.join((local_dir_path, '_image_listing.json'))
            if Path(local_image_list).is_file():
                with open(local_image_list, 'r') as fp:
                    web_image_listing = json.load(fp)
            else:
                target_web_dir = '/'.join((image_group_path, 'web'))
                web_image_listing = get_digital_ocean_images(_resource, f'{target_web_dir}/')

        new_manifest_name = item_uid + '.' + image_group_id + '.manifest.json'
        new_manifest_key = '/'.join((target_bucket_endpoint, item_uid,
                                     image_group_id, new_manifest_name))

        local_manifest = build_manifest(web_image_listing, manifest_template, canvas_template,
                                        seq_template, record)

        upload_manifest(_resource, local_manifest, new_manifest_key)

    # create listing of processed records
    debug_found_directories.append(digital_ocean_dir_path)
    return True
