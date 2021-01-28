import collections
import os
from pprint import pprint as pretty
from PIL import Image
import botocore


# For debug-checking current dir hierarchy
def dump_objects(client):
    response = client.list_objects(Bucket='aciptest')
    for i in response['Contents']:
        dir = i.get('Key')
        size = i.get('Size')
        # print(dir, size)
        pretty(i)


# TODO получить cписок файлов в директории
def get_images_files(resource, source_bucket_name, spaces_dir):
    '''
    list of file names ['scan01.jpg', 'scan02.jpg']
    :param resource: object, boto3.resource('s3')
    :param spaces_dir: str, source dir in s3 bucket
    :return: list of file names ['scan01.jpg', 'scan02.jpg']
    '''

    paginator = resource.meta.client.get_paginator('list_objects')
    operation_parameters = {
        'Bucket': source_bucket_name,
        'Prefix': f'{spaces_dir}/',
        # 'Delimiter': '/'
    }
    print(f"get_images_files: source_bucket_name='{source_bucket_name}', spaces_dir='{spaces_dir}'")

    page_iterator = paginator.paginate(**operation_parameters)

    images = []

    # paginate
    try:
        for page in page_iterator:
            # page contents correspond to image groups
            for group in page['Contents']:
                _, image_name = os.path.split(group.get('Key'))
                if image_name:
                    images.append(image_name)
    except Exception:
        print(f'ERROR in get_images_files() on directory: "{spaces_dir}"')
        raise

    return images


# TODO: скопировать файлы
def copy_files(files_listing,
               source_bucket_name, source_dir,
               target_bucket_name, target_dir,
               resource
               ):
    '''

    :param files_listing: list of file names ['scan01.jpg', 'scan02.jpg']
    :param source_bucket_name:
    :param source_dir:
    :param target_bucket_name:
    :param target_dir:
    :param resource: object, boto3.resource('s3')
    :return:
    '''
    pretty(files_listing)

    for image in files_listing:
        source_key = '/'.join((source_dir, image))
        target_key = '/'.join((target_dir, image))
        print(f"copy file: source_bucket_name='{source_bucket_name}', source_key='{source_key}' \n  => target_bucket_name='{target_bucket_name}', target_key='{target_key}'")

        copy_source = {
            'Bucket': source_bucket_name,
            'Key': source_key,
        }
        try:
            resource.meta.client.copy(
                copy_source,
                Bucket=target_bucket_name,
                Key=target_key,
            )
        except botocore.exceptions.ClientError:
            print(f"ERROR: botocore.exceptions.ClientError (copying file {source_key} => {target_key})")


def process_folders(source_tsv="tools/Mantras.tsv", copy_flag=0, manifest_flag=0, resize_flag=0):
    # level='DEBUG' / level='WARNING'
    # boto3.set_stream_logger('botocore', level='WARNING')
    print(f"process_folders(source_tsv='{source_tsv}', copy flag={copy_flag}, manifest flag={manifest_flag}, resize flag={resize_flag}")

    import boto3
    from dotenv import load_dotenv
    from _tools.build_s3_manifests import build_manifest_from_template

    # Init local s3 congiguration from .env file
    load_dotenv()

    config = {
        'region_name': os.environ.get("SPACES_REGION"),
        'endpoint_url': os.environ.get("SPACES_HOST"),
        'aws_access_key_id': os.environ.get("AWS_KEY"),
        'aws_secret_access_key': os.environ.get("AWS_SECRET")
    }

    ENDPOINT_URL = os.environ.get("SPACES_HOST")

    SOURCE_BUCKET_NAME = os.environ.get("SOURCE_BUCKET_NAME")
    TARGET_BUCKET_NAME = os.environ.get("TARGET_BUCKET_NAME")

    # Initialize a session using DigitalOcean Spaces.
    #  (resource is high level and generally returns instances of bucket / objects)
    # ---- object = s3.Object('bucket_name','key')
    # if you need client you can access through resource.meta.client (as below)
    # resource.meta.client.get_paginator('list_objects')

    _resource = boto3.resource('s3', **config)

    print("current working directory:", os.path.abspath(os.path.curdir))

    # TSV file: first line is headers (field names), tab-separated;
    #  all following lines contain raw data, tab-separated.
    # We'll use namedtuple to access field values nicely (csv.Subject etc).
    with open(source_tsv, "rt") as csvfile:
        # Remove all special symbols (spaces and #) from field names.
        header_line = csvfile.readline().replace(" ", "").replace("#", "")
        field_names = header_line.split('\t')

        # Last element will be '\n', it's invalid field name,
        #  so use "rename=True" to auto-rename such fields to "_1", "_2" etc
        CsvLineClass = collections.namedtuple('CSVLine', field_names, rename=True)

        for line in csvfile:
            csv = CsvLineClass._make(line.split('\t'))

            # Correct path name for source images(scans) dir - from here we will copy files
            # ======= TODO MANTRA in csv and Mantras in bucket =======
            source_images_dir = '/'.join((csv.Subject.lower().capitalize(), csv.Series + ' ' + csv.Title))

            # TODO - нужен признак тома, сколько томов у книги? Есть в CSV файле
            # Correct path names for target dirs : ItemUID/.../ItemUID + '-' + image_group_id
            image_id = 'IG.' + csv.ItemUID + '.001'
            image_group_id = csv.ItemUID + '-' + image_id

            target_sources_dir = '/'.join((csv.ItemUID, 'sources', image_group_id))
            target_images_dir = '/'.join((csv.ItemUID, 'images', image_group_id))
            target_web_dir = '/'.join((csv.ItemUID, 'web', image_group_id))

            if copy_flag:
                # Create target path objects in S3 bucket
                for path_name in (target_sources_dir, target_images_dir, target_web_dir):
                    _resource.meta.client.put_object(Bucket=TARGET_BUCKET_NAME,
                                                     Body='Contents',
                                                     Key=path_name + '/'
                                                     )
                    print(path_name)

                # Copy scans from source to target_sources_dir without renaming and resizing
                # List of file names ['scan01.jpg', 'scan02.jpg'] in source_images_dir
                image_listing = get_images_files(_resource, SOURCE_BUCKET_NAME, source_images_dir)
                print(f"copying S3 files from {source_images_dir} to {target_sources_dir}...")

                # Rename and copy scans from source_images_dir into target_sources_dir
                copy_files(image_listing,
                           SOURCE_BUCKET_NAME, source_images_dir,
                           TARGET_BUCKET_NAME, target_sources_dir,
                           _resource
                           )

                # Copy and rename scans from target_sources_dir в target_images_dir
                image_ext = image_listing[0].split(".")[-1]  # scans extension

                # TODO: переделать на def - копирование с переименованием
                for i, image in enumerate(image_listing):
                    # Format for renaming: image_group_id.000X.jpg
                    renamed_image = '.'.join([image_id, ('%04d' % (i + 1)), image_ext])

                    source_key = '/'.join((target_sources_dir, image))

                    copy_source = {'Bucket': SOURCE_BUCKET_NAME,
                                   'Key': source_key
                                   }

                    target_key = '/'.join((target_images_dir, renamed_image))

                    _resource.meta.client.copy(copy_source,
                                               Bucket=TARGET_BUCKET_NAME,
                                               Key=target_key
                                               )
            if resize_flag:
                # Preparing compressed and resized scans for web,
                #     copy it from target_images_dir to target_web_dir
                # TODO: resizing scans code here
                renamed_image_listing = get_images_files(_resource, TARGET_BUCKET_NAME, target_images_dir)

                '''    
                copy_files(renamed_image_listing,
                           TARGET_BUCKET_NAME, target_images_dir,
                           TARGET_BUCKET_NAME, target_web_dir,
                           _resource
                           )
                '''

                # temp local directory for storing downloaded/processed image files
                local_path = '/'.join(('_tmp_images', target_images_dir))
                try:
                    os.makedirs(local_path)
                except OSError:
                    print(f"ERROR: creation of local image directory '{local_path}' failed")
                else:
                    print(f"created local image directory '{local_path}'")

                _bucket = _resource.Bucket(TARGET_BUCKET_NAME)
                for image_name in renamed_image_listing:
                    # download image file from S3
                    local_image_name = '/'.join((local_path, image_name))
                    image_key = '/'.join((target_images_dir, image_name))
                    print(f"downloading image file: image_key='{image_key}' to local_image_name='{local_image_name}'...")
                    _bucket.download_file(image_key, local_image_name)

                    # process image file locally
                    image_processed_name = '/'.join((local_path, 'PROCESSED_' + image_name))
                    print(f"processing local image_name='{image_name}' to '{image_processed_name}'")
                    img = Image.open(local_image_name)
                    img.load()
                    img.save(image_processed_name, dpi=(72.0, 72.0))

                    # upload processed file to S3 (to target_web_dir folder, with the same original image name)
                    image_processed_key = '/'.join((target_web_dir, image_name))
                    print(f"uploading local processed image '{image_name}' to image_processed_key='{image_processed_key}'...")
                    _resource.meta.client.upload_file(
                        image_processed_name,
                        TARGET_BUCKET_NAME,
                        image_processed_key,
                        ExtraArgs={'ContentType': 'image/jpeg'}
                    )

                    # DEBUG: only process 1st file
                    # break

            if manifest_flag:
                # build_manifest_from_template(address='ISKS1RC752/web/ISKS1RC752-IG.ISKS1RC752.001/',
                #                              spaces_dir='ISKS1RC752')
                local_manifest = build_manifest_from_template(target_web_dir + '/', csv.ItemUID)
                # upload manifest to S3 (to ItemUID/web)
                # rename manifest - ItemUID.ImageGroupUID.manifest.json
                new_manifest_name = csv.ItemUID + '.' + image_group_id + '.manifest.json'
                new_manifest_key = '/'.join((csv.ItemUID, 'web', new_manifest_name))
                print(f"uploading local manifest='{local_manifest}' to S3 new_manifest_key='{new_manifest_key}'...")
                _resource.meta.client.upload_file(
                    local_manifest,
                    TARGET_BUCKET_NAME,
                    new_manifest_key,
                    ExtraArgs={'ContentType': 'application/json'}
                )


            # DEBUG: stop after 1st directory
            # quit()


if __name__ == "__main__":
    process_folders()

'''
#------------------------
# REQUIREMENTS:
#------------------------
item uid
	sources
		item_uid.imagegroupuid
		# not renamed
	web
		item_uid.imagegroupuid
		# renamed - imagegroupuid.0001.xxx
	images
		item_uid.imagegroupuid
		# renamed - imagegroupuid.0001.xxx
		# resized 

#------------------------
# EXPECTED RESULTS ISKS1RC748/Images/Item#-IG#/IG.ISKS1RC748.0001.jpg
#------------------------
isks1rc748
 	sources
  		isks1rc748.ig.isks1rc748
				tvm-19018b-p01.jpg
				tvm-19018b-p02.jpg
	 web
  		isks1rc748.ig.isks1rc748
			ig.isks1rc748.0001.jpg
			ig.isks1rc748.0002.jpg
 	images
  		isks1rc748.ig.isks1rc748
			ig.isks1rc748.0001.jpg
			ig.isks1rc748.0002.jpg
'''