from datetime import date
import pandas as pd
from functions import build_args, create_bucket_policy, process_dataframe, \
    authorize_google, set_google_sheets, get_sheet_id, write_sheet_data, get_sheet_data, get_s3_objects
from settings import source_prefix, source_bucket, google

args = build_args()
options = vars(args)

create_bucket_policy()

print(args)

main_prefix = f'{source_prefix}/ramachandra_2/'
fixed_item_prefix = "ISKS2RC"

# GET CATALOG DATA ##############################################
# catalog data found in Google Sheets currently
_sheets, _ = authorize_google(**google)  # can also obtain _drive service here
# set config details for which sheets act as I/O
sheet_config = set_google_sheets(input_name=args.input, output_name=args.output, **google)
sheet_config = get_sheet_id(_sheets, **sheet_config)
catalog_data = get_sheet_data(_sheets, **sheet_config)

# GET A LISTING OF ALL SCAN DIRECTORIES #########################
scan_dirs = []
# for d in list_client_directories(_client, bucket=main_bucket, main_directory=main_prefix):
#     tmp_dir = list_client_directories(_client, bucket=main_bucket, main_directory=d)
for d in get_s3_objects(bucket=source_bucket, prefix=main_prefix):
    scan_dirs.append(d)

scan_dir_paths = sorted(set(scan_dirs))  # create a set
print(scan_dir_paths)

# scan_dirs = {}
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

scan_data = pd.DataFrame(scan_listing)

print(f'shape of CATALOG data is {catalog_data.shape}')
print(f'shape of SCAN data is {scan_data.shape}')

scan_cols = scan_data.columns.difference(catalog_data.columns).insert(0, 'series')
# scan_cols = scan_cols.insert(0, 'series')

# with merged records
full_input = pd.merge(catalog_data, scan_data[scan_cols], left_on='series', right_on='series', how='inner')

write_sheet_data(_sheets, full_input, output_name='full_input', **sheet_config)

# write to google sheets
# process
# copy sources to images
# build manifests
process_dataframe(full_input, options)

# write results to google sheets


