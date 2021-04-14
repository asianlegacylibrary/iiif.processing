import argparse
from configparser import ConfigParser
import sys
import os
from settings import ROOT_DIR


def file_path(string):
    if os.path.isfile(string):
        return string
    else:
        raise FileNotFoundError(string)


def build_args(argv=None):
    # Do argv default this way, as doing it in the functional
    # declaration sets it at compile time.
    if argv is None:
        argv = sys.argv

    # Parse any conf_file specification
    # We make this parser with add_help=False so that
    # it doesn't parse -h and print help.
    defaults_parser = argparse.ArgumentParser(
        description=__doc__,
        # formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False
    )

    defaults_parser.add_argument("-d",
                                 "--defaults",
                                 help="Specify defaults config file",
                                 metavar="DEFAULTS",
                                 type=file_path,
                                 default=file_path('defaults.ini'))

    args, remaining_argv = defaults_parser.parse_known_args()

    # defaults = {"copy": False, "web": False, "manifest": False}
    defaults_dict = {}

    if args.defaults:
        config = ConfigParser()
        config.read([args.defaults])
        defaults_dict.update(dict(config.items("Defaults")))

    # print(defaults_dict)
    # Parse rest of arguments
    # Don't suppress add_help here so it will handle -h
    parser = argparse.ArgumentParser(
        # Inherit options from config_parser
        parents=[defaults_parser]
        )
    parser.set_defaults(**defaults_dict)

    # add command line args here
    parser.add_argument('-i',
                        '--input',
                        help='input google sheets')
    parser.add_argument('-o',
                        '--output',
                        help='output google sheets')

    parser.add_argument('-c',
                        '--copy',
                        action='store_true',
                        help='copy images and dir structure from staging to production')

    parser.add_argument('-m',
                        '--manifest',
                        action='store_true',
                        help='create and upload manifest')

    parser.add_argument('-k',
                        '--check_buckets',
                        action='store_true',
                        help='check object counts in each bucket')

    parser.add_argument('-f',
                        '--file',
                        action='store_true',
                        help='use TSV as file input')

    args = parser.parse_args(remaining_argv)
    return args