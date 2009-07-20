import traceback
import sys
import logging

# always print stuff on the screen:
logging.basicConfig(level=logging.INFO)

def log_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            logging.info("Exception raised")
            etype, value, tb = sys.exc_info()
            s = "".join(traceback.format_exception(etype, value, tb))
            logging.info(s)
            logging.info("-"*40)
            raise
    return wrapper

class Eval(object):

    def __init__(self):
        self._namespace = {}

    def eval(self, text):
        try:
            exec text in {}, self._namespace
            return str(self._namespace)
        except:
            etype, value, tb = sys.exc_info()
            s = "".join(traceback.format_exception(etype, value, tb))
            return s
