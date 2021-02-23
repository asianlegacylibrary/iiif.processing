# Import the argparse library
import argparse
from configparser import SafeConfigParser

import os
import sys

# Create the parser
parser = argparse.ArgumentParser(description='Process catalog and scan images to IIIF')

# Add the arguments
# ACTIONS, store_true means it is false unless specified, store_false means it is true unless specified

# store_true
# copy, --copy, -c // copy images and dir structure from staging to production
# create_web_files, --web, -w // create web directory and process images for web
# manifest, --manifest, -m // create and upload manifest
# input_from_file, --file, -f // input data coming from a file, need to add PATH TO FILE if this is true

# optional, if optional start with dash (-)
parser.add_argument('-c',
                    '--copy',
                    action='store_true',
                    help='copy images and dir structure from staging to production')

# store_false
# process_all_images_for_manifest: True
# file_upload: True
# download_overwrite: True
# image_group_overwrite: True
# test_run: True
# copy_input: True


# Execute parse_args()
args = parser.parse_args()




# example positional arg
# parser.add_argument('Path',
#                        metavar='path',
#                        type=str,
#                        help='the path to list')
# input_path = args.Path
# if not os.path.isdir(input_path):
#     print('The path specified does not exist')
#     sys.exit()
#
# for line in os.listdir(input_path):
#     if args.long:  # Simplified long listing
#         size = os.stat(os.path.join(input_path, line)).st_size
#         line = '%10d  %s' % (size, line)
#     print(line)
