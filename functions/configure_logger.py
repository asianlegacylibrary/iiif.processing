import sys
import logging
from functions import Logger
from settings import logging_config


# -------------------------------------------------------------------------------------------------
#
# -------------------------------------------------------------------------------------------------
def configure_logger():
    # configure the logger
    sys.stdout = Logger()
    # levels: debug, info, warning, error, critical
    # example --> logging.warning('This will get logged to a file')
    logging.basicConfig(
        level=logging.INFO,
        filename=logging_config["filename"],
        filemode=logging_config["mode"],
        format=logging_config["formatter"]
    )

    # set the logging for google api client to ERROR only, it has a lot of warnings
    logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

