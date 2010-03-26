import traceback
import sys
from StringIO import StringIO

class Eval(object):

    def __init__(self, namespace={}):
        self._namespace = namespace

    def eval(self, x, use_none_for_exceptions=False):
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
                r = sys.stdout.read() + r
            finally:
                sys.stdout = old_stdout
            return r
        except:
            if use_none_for_exceptions:
                return
            etype, value, tb = sys.exc_info()
            # If we decide in the future to remove the first frame from the
            # traceback (since it links to our code, so it could be confusing
            # to the user), it's easy to do:
            #tb = tb.tb_next
            s = "".join(traceback.format_exception(etype, value, tb))
            return s
