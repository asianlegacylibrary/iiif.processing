import sys
from settings import logging_config


class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open(logging_config["filename"], "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()
