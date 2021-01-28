import sys

# LOGGER
conf_log = {
    "filename": "log.txt",
    "mode": "w",
    "formatter": '%(name)s - %(levelname)s - %(message)s'
}


class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open(conf_log["filename"], "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()
