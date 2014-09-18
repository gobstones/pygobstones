from test_utils import append_file
import datetime


class TestLogger(object):
    def __init__(self, filename):
        self.filename = filename                        
    def log(self, message):
        append_file(self.filename, self.log_header() + "\n" + message + "\n")
    def log_header(self):
        return "[%s] -----------------------------" % (datetime.datetime.now(),)
    
log = TestLogger("test.log").log