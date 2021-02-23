#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

from _tools.create_s3_target_dirs import process_folders


DEFAULT_TSV_FILENAME = "tools/Mantras.tsv"
DEFAULT_COPY_FLAG = 0
DEFAULT_MANIFEST_FLAG = 0
DEFAULT_SCALE_FLAG = 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('-t', '--tsv', type=str, action='store', help='input *.tsv filename (TSV file should contain list of tab-separated data lines for DigitalOcean folders to process)')
    parser.add_argument('-c', '--copy', type=int, action='store', help='copy images flag (0|1)')
    parser.add_argument('-m', '--manifest', type=int, action='store', help='create manifest flag (0|1)')
    parser.add_argument('-r', '--resize', type=int, action='store', help='resize/tilt images flag (0|1)')
    args = parser.parse_args()

    tsv_filename = args.tsv or DEFAULT_TSV_FILENAME
    copy_flag = int(args.copy or DEFAULT_COPY_FLAG)
    manifest_flag = int(args.manifest or DEFAULT_MANIFEST_FLAG)
    resize_flag = int(args.resize or DEFAULT_SCALE_FLAG)

    print(f"tsv='{tsv_filename}', copy flag={copy_flag}, manifest flag={manifest_flag}, resize flag={resize_flag}")
    process_folders(tsv_filename, copy_flag=copy_flag, manifest_flag=manifest_flag, resize_flag=resize_flag)