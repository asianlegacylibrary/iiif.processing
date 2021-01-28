import sys
import logging
from functions import Logger, conf_log


# -------------------------------------------------------------------------------------------------
#
# -------------------------------------------------------------------------------------------------
def configure_logger():
    # configure the logger
    sys.stdout = Logger()
    # levels: debug, info, warning, error, critical
    # example --> logging.warning('This will get logged to a file')
    logging.basicConfig(
        # level=logging.DEBUG,
        filename=conf_log["filename"],
        filemode=conf_log["mode"],
        format=conf_log["formatter"]
    )
