from datetime import date
import pandas as pd
from functions import list_client_directories, build_args, create_bucket_policy, process_dataframe, \
    authorize_google, set_google_sheets, get_sheet_id, write_sheet_data
from settings import _client, main_prefix, source_bucket, google, main_bucket

args = build_args()
options = vars(args)

create_bucket_policy()

print(args)

# GET CATALOG DATA ##############################################
# catalog data found in Google Sheets currently
_sheets, _ = authorize_google(**google)  # can also obtain _drive service here
# set config details for which sheets act as I/O
sheet_config = set_google_sheets(output_name=args.output, **google)
sheet_config = get_sheet_id(_sheets, **sheet_config)


# GET A LISTING OF ALL SCAN DIRECTORIES #########################
scan_dirs = []
for d in list_client_directories(_client, bucket=main_bucket, main_directory=main_prefix):
    tmp_dir = list_client_directories(_client, bucket=main_bucket, main_directory=d)
    scan_dirs.append(tmp_dir)

scan_dir_paths = sorted(set(sum(scan_dirs, [])))  # create a set
print(scan_dir_paths)

# scan_dirs = {}
scan_listing = []
fixed_prefix = "ISKS2RC"

for s in scan_dir_paths:
    key = s.split('/')[-2]  # -2 because an S3 directory obj always ends in a /
    if len(key) < 1 or key is None:
        continue

    # split the key into its SERIES and TITLE
    # ex. 12502 Jyotirvilasa in marathi >>> SERIES: 12502, TITLE: Jyotirvilasa in marathi
    series, title = key.split(' ', 1)
    if not series.isdigit() or title is None:
        continue

    scan_listing.append({
        'key': key,
        'work_uid': f'W.{fixed_prefix}{series}.001',
        'item_uid': f'{fixed_prefix}{series}',
        'image_group_uid': f'IG.{fixed_prefix}{series}.001',
        'series': series,
        'title': title,
        'directory_path': s,
        'description': f'Manifest built on {date.today()}'
    })
    # scan_dir[key] = s

write_sheet_data(_sheets, pd.DataFrame(scan_listing), output_name='aws_input', **sheet_config)

process_dataframe(pd.DataFrame(scan_listing), options)


