from datetime import date
from functions import get_s3_objects

# GET A LISTING OF ALL SCAN DIRECTORIES #########################
def gather_scan_data(from_bucket, from_prefix, fixed_item_prefix):

    scan_dirs = []
    # for d in list_client_directories(_client, bucket=main_bucket, main_directory=main_prefix):
    #     tmp_dir = list_client_directories(_client, bucket=main_bucket, main_directory=d)
    for d in get_s3_objects(bucket=from_bucket, prefix=from_prefix):
        scan_dirs.append(d)

    scan_dir_paths = sorted(set(scan_dirs))  # create a set
    scan_listing = []

    for s in scan_dir_paths:
        key = s.split('/')[-2]  # -2 because an S3 directory obj always ends in a /
        if len(key) < 1 or key is None or key == '':
            continue

        # split the key into its SERIES and TITLE
        # ex. 12502 Jyotirvilasa in marathi >>> SERIES: 12502, TITLE: Jyotirvilasa in marathi
        try:
            series, title = key.split(' ', 1)
        except ValueError:
            print('value error', key)
            continue

        if not series.isdigit() or title is None:
            continue

        scan_listing.append({
            'key': key,
            'work_uid': f'W.{fixed_item_prefix}{series}.001',
            'item_uid': f'{fixed_item_prefix}{series}',
            'image_group_uid': f'IG.{fixed_item_prefix}{series}.001',
            'series': series,
            'title': title,
            'directory_path': s,
            'description': f'Manifest built on {date.today()}'
        })

    return scan_listing
