import os
import collections
import boto3

from dotenv import load_dotenv
from config.config import config, flags, TARGET_BUCKET_TEST_ENDPOINT, SOURCE_BUCKET_TEST_ENDPOINT, TARGET_BUCKET_NAME
from functions import configure_logger, list_client_directories, build_manifest_template_structure, build_manifest, \
    get_directory_images, create_structure_and_copy, create_web_files


load_dotenv()

# https://aciptest.sfo2.digitaloceanspaces.com/ISKS1RC748/web/ISKS1RC748-IG.ISKS1RC748.001/
# https://aciptest.sfo2.digitaloceanspaces.com/ISKS1RC748/web/ISKS1RC748-IG.ISKS1RC748.001/IG.ISKS1RC748.001.0001.JPG

if __name__ == "__main__":
    print("current working directory:", os.path.abspath(os.path.curdir))

    # set up error logs
    configure_logger()

    # get session / resource for S3
    _session = boto3.session.Session()
    _resource = _session.resource('s3', **config)
    _client = boto3.client('s3', **config)

    # create the structure for manifests
    manifest_structure, canvas_template = build_manifest_template_structure()

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
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    test_dir = 'ayurveda'  # 'ayurveda'
    # source_tsv = os.path.abspath(os.path.join(ROOT_DIR, "data/Mantras.tsv"))
    source_tsv = os.path.abspath(os.path.join(ROOT_DIR, f"data/{test_dir}.tsv"))
    print(source_tsv)

    with open(source_tsv, "rt") as csv_file:
        # Remove all special symbols (spaces and #) from field names.
        header_line = csv_file.readline().replace(" ", "").replace("#", "")
        field_names = header_line.split('\t')
        # Last element will be '\n', it's invalid field name,
        #  so use "rename=True" to auto-rename such fields to "_1", "_2" etc
        CsvLineClass = collections.namedtuple('CSVLine', field_names, rename=True)
        # print(header_line, field_names, CsvLineClass)
        debug_tracking_found_directories = []
        for line in csv_file:
            record = CsvLineClass._make(line.split('\t'))

            # Correct path name for source images(scans) dir - from here we will copy files
            # ======= TODO MANTRA in csv and Mantras in bucket =======
            source_images_dir = '/'.join((record.Subject.lower().capitalize(), record.Series + ' ' + record.Title))
            source_prefix = f'{SOURCE_BUCKET_TEST_ENDPOINT}{source_images_dir}/'

            # check if CSV record exists in staging S3 bucket
            current_directory = record.Subject.lower().capitalize()
            client_directories = list_client_directories(_client, bucket='acip',
                                                         main_directory=f'staging_test/{current_directory}/')

            if not source_prefix.lower() in (d.lower() for d in client_directories):
                continue
            else:
                print(record)
                for d in client_directories:
                    if source_prefix.lower() == d.lower():
                        source_prefix = d
                        debug_tracking_found_directories.append(source_prefix)

            # TODO - нужен признак тома, сколько томов у книги? Есть в CSV файле
            # Correct path names for target dirs : ItemUID/.../ItemUID + '-' + image_group_id
            image_group_id = 'IG.' + record.ItemUID + '.001'

            target_sources_dir = '/'.join((TARGET_BUCKET_TEST_ENDPOINT, record.ItemUID, image_group_id, 'sources'))
            target_images_dir = '/'.join((TARGET_BUCKET_TEST_ENDPOINT, record.ItemUID, image_group_id, 'images'))
            target_web_dir = '/'.join((TARGET_BUCKET_TEST_ENDPOINT, record.ItemUID, image_group_id, 'web'))
            # print(target_web_dir, target_images_dir, target_sources_dir)

            image_listing = get_directory_images(_resource, source_prefix)
            print(f'Path has {len(image_listing["images"])} images', image_listing['images'])

            if flags['copy']:
                create_structure_and_copy(_resource, target_sources_dir, target_images_dir,
                                          target_web_dir, source_prefix, image_listing, image_group_id)

            if flags['create_web_files']:
                create_web_files(_resource, target_images_dir, target_web_dir)

            if flags['manifest']:
                web_image_listing = get_directory_images(_resource, f'{target_web_dir}/')
                print(f'Path has {len(web_image_listing["images"])} images', web_image_listing['images'])

                local_manifest = build_manifest(web_image_listing, manifest_structure, canvas_template)
                # upload manifest to S3 (to ItemUID/web)
                # rename manifest - ItemUID.ImageGroupUID.manifest.json
                new_manifest_name = record.ItemUID + '.' + image_group_id + '.manifest.json'
                new_manifest_key = '/'.join((TARGET_BUCKET_TEST_ENDPOINT, record.ItemUID,
                                             image_group_id, new_manifest_name))

                print(f"uploading local manifest='{local_manifest}' to S3 new_manifest_key='{new_manifest_key}'...")

                _resource.meta.client.upload_file(
                    local_manifest,
                    TARGET_BUCKET_NAME,
                    new_manifest_key,
                    ExtraArgs={'ContentType': 'application/json', 'ACL': 'public-read'}
                )

        print(f'Processed TSV lines for: {debug_tracking_found_directories}')
