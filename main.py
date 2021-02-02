import os
from pathlib import Path
import json
import collections
import boto3
from settings import flags, test_data_file, spaces, source_bucket_endpoint, target_bucket_endpoint, \
    source_bucket, local_image_listing_file, scan_directories
from functions import configure_logger, list_client_directories, build_manifest_template_structure, build_manifest, \
    get_digital_ocean_images, create_structure_and_copy, create_web_files, upload_manifest


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
source_tsv = os.path.abspath(os.path.join(ROOT_DIR, f"data/{test_data_file}"))

if __name__ == "__main__":
    print(f'current working directory: {os.path.abspath(os.path.curdir)}')
    print(f'Source data coming from {source_tsv}')
    print(f'Processing steps: COPY={flags["copy"]} // WEB={flags["create_web_files"]} // MANIFEST={flags["manifest"]}')

    # set up error logs
    configure_logger()

    # get session / resource for S3
    _session = boto3.session.Session()
    _resource = _session.resource('s3', **spaces)
    _client = boto3.client('s3', **spaces)

    # create the structure for manifests
    manifest_structure, canvas_template, seq_template = build_manifest_template_structure()

    # get catalog records (currently from CSV)

    # for each record
    # -- check that it exists in S3
    # -- COPY
    # -- create copy of source to web and high-rez (source will stay as is)
    # -- create proper directory structure and move files
    # -- PROCESS
    # -- resize etc
    # TSV file: first line is headers (field names), tab-separated;
    #  all following lines contain raw data, tab-separated.
    # We'll use namedtuple to access field values nicely (csv.Subject etc).

    with open(source_tsv, "rt") as csv_file:
        # Remove all special symbols (spaces and #) from field names.
        header_line = csv_file.readline().replace(" ", "").replace("#", "")
        field_names = header_line.split('\t')
        # Last element will be '\n', it's invalid field name,
        #  so use "rename=True" to auto-rename such fields to "_1", "_2" etc
        CsvLineClass = collections.namedtuple('CSVLine', field_names, rename=True)
        # print(header_line, field_names, CsvLineClass)
        debug_tracking_found_directories = []
        web_image_listing = None
        for line in csv_file:
            record = CsvLineClass._make(line.split('\t'))

            # Correct path name for source images(scans) dir - from here we will copy files
            source_images_dir = '/'.join((record.Subject.lower().capitalize(), record.Series + ' ' + record.Title))
            _SOURCE = f'{source_bucket_endpoint}{source_images_dir}/'

            # check if CSV record exists in staging S3 bucket
            current_directory = record.Subject.lower().capitalize()
            client_directories = list_client_directories(_client, bucket='acip',
                                                         main_directory=f'staging_test/{current_directory}/')

            # need to create more robust comparison test between CATALOG and staging DIRECTORY
            if not _SOURCE.replace(" ", "").lower() in (d.replace(" ", "").lower() for d in client_directories):
                continue
            else:
                for d in client_directories:
                    if _SOURCE.replace(" ", "").lower() == d.replace(" ", "").lower():
                        _SOURCE = d
                        print(record)
                        # Subject, Title, Description, Author, AuthorDate, Commentary, Language, Script, Material,
                        # Size_inches, Library, Folios, Publication, Year, Edition,
                        # quit()
                        debug_tracking_found_directories.append(_SOURCE)

            # TODO - need a volume tag, how many volumes does the book have? Available in CSV file
            # Correct path names for target dirs : ItemUID/.../ItemUID + '-' + image_group_id
            image_group_id = 'IG.' + record.ItemUID + '.001'
            image_group_path = '/'.join((target_bucket_endpoint, record.ItemUID, image_group_id))

            image_listing = get_digital_ocean_images(_resource, _SOURCE)
            print(f'Path for {record.ItemUID} has {len(image_listing["images"])} images', image_listing['images'])

            if flags['copy']:
                create_structure_and_copy(_resource, image_group_path, _SOURCE, image_listing, image_group_id)

            if flags['create_web_files']:
                web_image_listing = create_web_files(_resource, image_group_path)

            if flags['manifest']:
                if web_image_listing is None:
                    print('we did not upload web images this iteration...')
                    dir_images = '/'.join((image_group_path, scan_directories['images']))
                    local_dir_path = '/'.join(('data', '_tmp_images', dir_images))
                    local_image_list = '/'.join((local_dir_path, '_image_listing.json'))
                    if Path(local_image_list).is_file():
                        print(f'using existing image listing found here: {local_image_list}')
                        with open(local_image_list, 'r') as fp:
                            web_image_listing = json.load(fp)
                    else:
                        print('recreating image listing from web directory')
                        target_web_dir = '/'.join((image_group_path, 'web'))
                        web_image_listing = get_digital_ocean_images(_resource, f'{target_web_dir}/')
                        # print(f'Path has {len(web_image_listing["images"])} images', web_image_listing['images'])

                new_manifest_name = record.ItemUID + '.' + image_group_id + '.manifest.json'
                new_manifest_key = '/'.join((target_bucket_endpoint, record.ItemUID,
                                             image_group_id, new_manifest_name))

                local_manifest = build_manifest(web_image_listing, manifest_structure, canvas_template, seq_template)
                print(local_manifest)

                upload_manifest(_resource, local_manifest, new_manifest_key)

            if flags['test_run']:
                quit()

        print(f'Processed TSV lines for: {debug_tracking_found_directories}')
