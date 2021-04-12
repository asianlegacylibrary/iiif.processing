import pandas as pd
import re
from tqdm import tqdm
from functions import build_args, create_bucket_policy, authorize_google, set_google_sheets, \
    get_sheet_id, get_sheet_data, copy_record, gather_scan_data, configure_logger, process_manifest, \
    standardize_digits, get_s3_objects
from settings import source_prefix, source_bucket, google, web_bucket, general_prefix

# set up error logs
configure_logger()
manifest = False

if __name__ == "__main__":

    args = build_args()
    options = vars(args)

    create_bucket_policy()

    print(args)
    print(options)



    main_prefix = f'{source_prefix}/ramachandra_2/'
    fixed_item_prefix = "ISKS1RC"

    # input = 'ramachandra_1_2'
    input = 'previously_gathered'

    # GET CATALOG DATA ##############################################
    # catalog data found in Google Sheets currently
    _sheets, _ = authorize_google(**google)  # can also obtain _drive service here
    # set config details for which sheets act as I/O
    sheet_config = set_google_sheets(input_name=input, output_name=args.output, **google)
    sheet_config = get_sheet_id(_sheets, **sheet_config)

    print(sheet_config)


    # catalog_data = get_sheet_data(_sheets, **sheet_config)
    # scan_data = gather_scan_data(source_bucket, main_prefix, fixed_item_prefix)
    # scan_data = pd.DataFrame(scan_data)
    #
    # print(f'shape of CATALOG data is {catalog_data.shape}')
    # print(f'shape of SCAN data is {scan_data.shape}')
    # scan_cols = scan_data.columns.difference(catalog_data.columns).insert(0, 'series')
    # # with merged records
    # full_input = pd.merge(catalog_data, scan_data[scan_cols], left_on='series', right_on='series', how='inner')
    # write_sheet_data(_sheets, full_input, output_name='full_input', **sheet_config)
    # quit()

    full_input = get_sheet_data(_sheets, **sheet_config)

    # print(f'shape of input is {full_input.shape}')
    # check in on web scans folder (all-library-web) for manifest generation
    if manifest:
        scan_dirs = []
        for d in get_s3_objects(bucket=web_bucket, prefix=general_prefix):
            d = d.replace("/", "")
            scan_dirs.append(d)

        scan_dir_paths = pd.Series(sorted(set(scan_dirs)))  # create a set
        print(scan_dir_paths.head())
        full_input = full_input[full_input.itemuid.isin(scan_dir_paths)]

    full_input = full_input.to_dict(orient='records')

    # write to google sheets
    # process
    # copy sources to images
    # full_input.apply(lambda x: copy_record(x, options, full_input.shape[0]), axis=1)
    for record in tqdm(full_input, position=1):
        # 1. copy records
        if manifest:
            process_manifest(record, options)
        else:
            copy_record(record, options)
        # 2. create manifests
        #

    # build manifests

    # write results to google sheets


