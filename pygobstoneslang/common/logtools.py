import logging
import sys

class SingleLevelFilter(logging.Filter):
    def __init__(self, passlevel, reject):
        self.passlevel = passlevel
        self.reject = reject

    def filter(self, record):
        if self.reject:
            return (record.levelno != self.passlevel)
        else:
            return (record.levelno == self.passlevel)
        
def default_handlers():
    handlers = []
    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.addFilter(SingleLevelFilter(logging.INFO, True))
    handlers.append(error_handler)
    out_handler = logging.StreamHandler(sys.stdout)
    out_handler.addFilter(SingleLevelFilter(logging.INFO, False))
    handlers.append(out_handler)
    return handlers        

def get_logger(name, handlers=None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not handlers:
        handlers = default_handlers()
    for handler in handlers:
        logger.addHandler(handler)        
    return logger