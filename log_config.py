import logging

DEFAULT_LOG = "./results/log"


def setup_logging(logfile: str = DEFAULT_LOG):
    file_handler = logging.FileHandler(logfile, mode="w")
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    logging.basicConfig(level=logging.INFO, handlers=[file_handler])
