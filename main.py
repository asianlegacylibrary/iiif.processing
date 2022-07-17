import pandas as pd
import re
from tqdm import tqdm
from functions import build_args, create_bucket_policy, authorize_google, set_google_sheets, \
    get_sheet_id, get_sheet_data, copy_record, gather_scan_data, configure_logger, process_manifest, \
    standardize_digits, get_s3_objects, check_bucket_sizes, write_sheet_data
from settings import source_prefix, source_bucket, google, web_bucket, general_prefix, \
    debug_exists_directories, debug_requires_processing, catalog_field_names

# set up error logs
configure_logger()

if __name__ == "__main__":
    args = build_args()
    options = vars(args)

    create_bucket_policy()

    print("ARGS: ", args)
    print("OPTIONS: ", options)


    # create something like collection options, ramachandra / nibs / etc
    # and move some of this to config values

    main_prefix = f'{source_prefix}/nibs_1/' #  f'{source_prefix}/ramachandra_3/'
    fixed_item_prefix = "ISKS1NIBS" #  "ISKS1RC"
    input_previously_gathered = False
    # input = 'ramachandra_1_2' is previously_gathered
    # next change input to ramachandra_1_1
    if input_previously_gathered:
        input = 'previously_gathered'
    else:
        input = 'nibs_1_1'  # 'ramachandra_1_3'

    # GET CATALOG DATA ##############################################
    # catalog data found in Google Sheets currently
    _sheets, _ = authorize_google(**google)  # can also obtain _drive service here

    # set config details for which sheets act as I/O
    sheet_config = set_google_sheets(input_name=input, output_name=options['output'], **google)
    sheet_config = get_sheet_id(_sheets, **sheet_config)
    print(sheet_config)

    # get input data
    if input_previously_gathered:
        full_input = get_sheet_data(_sheets, **sheet_config)
    else:
        catalog_data = get_sheet_data(_sheets, **sheet_config)
        print(source_bucket, main_prefix, fixed_item_prefix)

        scan_data = gather_scan_data(source_bucket, main_prefix, fixed_item_prefix)


        scan_data = pd.DataFrame(scan_data)

        print(f'shape of CATALOG data is {catalog_data.shape}')
        print(f'shape of SCAN data is {scan_data.shape}')

        scan_cols = scan_data.columns.difference(catalog_data.columns).insert(0, 'series')

        # with merged records
        full_input = pd.merge(catalog_data, scan_data[scan_cols], left_on='series', right_on='series', how='inner')

        write_sheet_data(_sheets, full_input, output_name='OUTPUT', **sheet_config)



    # work around to exclude scan folders with known but not addressed errors
    # full_input = full_input[~full_input['series'].isin(args.skip_list.split(','))]

    # check in on web scans folder (all-library-web) for manifest generation
    if str(options['manifest']) == 'True':
        scan_dirs = []
        for d in get_s3_objects(bucket=web_bucket, prefix=general_prefix):
            d = d.replace("/", "")
            scan_dirs.append(d)

        scan_dir_paths = pd.Series(sorted(set(scan_dirs)))  # create a set
        print('Creating manifests...', scan_dir_paths.head())
        full_input = full_input[full_input.itemuid.isin(scan_dir_paths)]


    try:
        full_input = full_input.to_dict(orient='records') # instead of df.apply i'm just for looping
        for record in tqdm(full_input, position=0 if options['check_buckets'] else 1):
            continue_processing = True

            if record[catalog_field_names['item_uid']] is None \
                    or record[catalog_field_names['directory_path']] is None \
                    or record[catalog_field_names['image_group_uid']] is None:
                continue_processing = False

            if str(options['check_buckets']) == 'True' and continue_processing:
                continue_processing, _, create_manifest = check_bucket_sizes(record)


            # 1. copy records
            if str(options['copy']) == 'True' and continue_processing:
                copy_record(record)
                _, _, create_manifest = check_bucket_sizes(record)

            # print('to process: ', debug_requires_processing)
            # print('exists: ', debug_exists_directories)
            # print('create manifest', create_manifest)

            # 2. create manifest
            if str(options['manifest']) == 'True' and create_manifest:
                process_manifest(record)


        if str(options['check_buckets']) == 'True':
            processing_list = list({v['id']: v for v in debug_requires_processing}.values())
            process_df = pd.DataFrame(processing_list)
            processed_list = list({v['id']: v for v in debug_exists_directories}.values())
            processed_df = pd.DataFrame(processed_list)
            write_sheet_data(_sheets, processed_df, output_name='processed_items_nibs', **sheet_config)
            write_sheet_data(_sheets, process_df, output_name='process_items_nibs', **sheet_config)

    except KeyboardInterrupt:
        processing_list = list({v['id']:v for v in debug_requires_processing}.values())
        process_df = pd.DataFrame(processing_list)
        processed_list = list({v['id']: v for v in debug_exists_directories}.values())
        processed_df = pd.DataFrame(processed_list)
        write_sheet_data(_sheets, processed_df, output_name='processed_items_nibs', **sheet_config)
        write_sheet_data(_sheets, process_df, output_name='process_items_nibs', **sheet_config)

    # write results to google sheets


