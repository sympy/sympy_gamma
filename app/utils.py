import traceback
import sys
import logging
from StringIO import StringIO

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

    def eval(self, x):
        globals = self._namespace
        try:
            x = x.strip()
            x = x.replace("\r", "")
            y = x.split('\n')
            if len(y) == 0:
                return ''
            s = '\n'.join(y[:-1]) + '\n'
            t = y[-1]
            try:
                z = compile(t + '\n', '', 'eval')
            except SyntaxError:
                s += '\n' + t
                z = None

            try:
                old_stdout = sys.stdout
                sys.stdout = StringIO()
                eval(compile(s, '', 'exec'), globals, globals)

                if not z is None:
                    r = repr(eval(z, globals))
                else:
                    r = ''
                sys.stdout.seek(0)
                r = r + sys.stdout.read()
            finally:
                sys.stdout = old_stdout
            return r
        except:
            etype, value, tb = sys.exc_info()
            # If we decide in the future to remove the first frame fromt he
            # traceback (since it links to our code, so it could be confusing
            # to the user), it's easy to do:
            #tb = tb.tb_next
            s = "".join(traceback.format_exception(etype, value, tb))
            return s
