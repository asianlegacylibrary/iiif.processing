import os
import pandas as pd
from string_grouper import match_strings, match_most_similar, group_similar_strings, StringGrouper
from settings import flags, google, _client, source_bucket_endpoint, image_group_records
from functions import configure_logger, authorize_google, get_sheet_data, process_dataframe, \
    copy_input, set_google_sheets, get_sheet_id, list_client_directories, write_sheet_data, get_digital_ocean_images


# NOTE: settings.py is prepping all options / config

if __name__ == "__main__":
    print(f'current working directory: {os.path.abspath(os.path.curdir)}')
    print(f'Processing steps: COPY={flags["copy"]} // WEB={flags["create_web_files"]} // MANIFEST={flags["manifest"]}')

    # set up error logs
    configure_logger()

    # GET A LISTING OF ALL SCAN DIRECTORIES #########################
    digital_ocean_scan_dirs = []
    for d in list_client_directories(_client, main_directory=source_bucket_endpoint):
        tmp_dir = list_client_directories(_client, main_directory=d)
        digital_ocean_scan_dirs.append(tmp_dir)

    scan_dir_paths = sorted(set(sum(digital_ocean_scan_dirs, [])))  # create a set

    scan_dirs = {}
    for s in scan_dir_paths:
        key = s.split('/')[-2]  # -2 because an S3 directory obj always ends in a /
        if len(key) < 1 or key is None:
            continue
        scan_dirs[key] = s

    print(list(scan_dirs.keys()))

    # GET CATALOG DATA ##############################################
    # catalog data found in Google Sheets currently
    _sheets, _ = authorize_google(**google)  # can also obtain _drive service here
    # set config details for which sheets act as I/O
    sheet_config = set_google_sheets(input_name='test', **google)
    sheet_config = get_sheet_id(_sheets, **sheet_config)

    print(sheet_config)
    # COPY INPUT DATA TO WORKING SHEET, not necessary but safer
    # if flags['copy_input']:
    #     sheet_config = copy_input(_sheets, **sheet_config)

    # DOWNLOAD DATA TO DATAFRAME ####################################
    input_data = get_sheet_data(_sheets, **sheet_config)
    print(f'shape of data is {input_data.shape}')

    # FUZZY MATCHING BETWEEN SCAN DIRECTORIES AND CATALOG TITLES ####
    # lots of differences between the two, so need robust way to match
    # Note: made small change to string_grouper function for match_most_similar
    # Note: create series for scan directory path (prefix) in digital ocean, use to find dirs in process step
    matched = pd.DataFrame({
        'directory_name': pd.Series(list(scan_dirs.keys())),
        'directory_path': pd.Series(list(scan_dirs.values())),
        'matched_catalog_title': match_most_similar(input_data['title'], pd.Series(list(scan_dirs.keys())))
         })

    # MERGE THE SCAN DIRECTORY NAME INTO THE CATALOG RECORDS #########
    # we'll only keep records that match, inner join
    full_input = pd.merge(input_data, matched, left_on='title', right_on='matched_catalog_title', how='inner')
    write_sheet_data(_sheets, full_input, output_name='full_input', **sheet_config)

    # at this point we'll write to google sheets to see how we're doing
    # write_sheet_data(_sheets, df, **sheet_config)

    # FINALLY PROCESS THE DATA #######################################
    # 1. Create proper DO directory structure (source, images, web)
    # 2. Process web directory files (tilt and resolution)
    # 3. Create manifest
    process_dataframe(full_input)

    # and write image group records to Google Sheets (get to MySQL for indexing at some point)
    write_sheet_data(_sheets, pd.DataFrame(image_group_records), output_name='image_groups', **sheet_config)

    # END ############################################################

    # IF NOT USING GOOGLE SHEETS DATA, CAN PULL FROM LOCAL FILE ######
    # if flags['input_from_file']:
    #     with open(local_source_input_file, mode="rt", encoding="utf-8") as file:
    #         # Remove all special symbols (spaces and #) from field names.
    #         process_file(file)
