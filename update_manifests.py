import json
from functions import configure_logger, upload_manifest
from settings import manifest_bucket, _resource

# set up error logs
configure_logger()

# define the links that need to be updated (find and replace)
http_link = 'http://157.245.187.36:8182'
https_link = 'https://loupe.asianlegacylibrary.org'

# local manifest dir path
local_dir_path = '/'.join(('data', 'manifests'))

# access manifest bucket
_bucket = _resource.Bucket(manifest_bucket)

# keep track of processed keys
# write to file and read back on start up
local_processed_file_path = '/'.join(('data', 'processed_keys.txt'))

previous_keys = []
with open(local_processed_file_path, 'r') as file:
    previous_key_file = file.read()

previous_keys = [x.strip() for x in previous_key_file.split(',')]


try:

    for idx, s3_object in enumerate(_bucket.objects.all()):

        # check if in previously processed keys
        if s3_object.key in previous_keys:
            print(f'{s3_object.key} already processed...')
            continue

        # print(f"Processing manifest {idx}: {s3_object.key}")

        # set local path for download and upload
        local_file_path = '/'.join((local_dir_path, s3_object.key))

        # Download the JSON manifest
        _bucket.download_file(s3_object.key, local_file_path)

        # Find and Replace HTTP >> HTTPS locally
        with open(local_file_path, 'r') as file:
            file_data = file.read()

        # Replace the target string
        file_data = file_data.replace(http_link, https_link)

        # encode to JSON and dump to local file
        json_data = json.loads(file_data)
        with open(local_file_path, 'w') as file:
            json.dump(json_data, file)

        # upload the manifest, it will be a new version of same file (versioning enabled on s3)
        upload_manifest(_resource, local_file_path, s3_object.key)

        # since it all went well, let's add the new key to our processed list
        previous_keys.append(s3_object.key)

        if idx % 100 == 0:
            print(f'WE ARE ON MANIFEST NUMBER {idx}!!! ({s3_object.key})')

except KeyboardInterrupt:
    with open(local_processed_file_path, 'w') as f:
        f.write(', '.join(previous_keys))
finally:
    with open(local_processed_file_path, 'w') as f:
        f.write(', '.join(previous_keys))