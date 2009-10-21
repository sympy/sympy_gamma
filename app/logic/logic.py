from utils import Eval

class SymPyGamma(object):

    def eval(self, s):
        r = self.try_sympy(s)
        if r:
            return r
        return [
                {"title": "Input", "input": s,
                    "output": "Can't handle the input."},
                ]

    def try_sympy(self, s):
        namespace = {}
        exec "from sympy.interactive import *" in {}, namespace
        a = Eval(namespace)
        # change to True to spare the user from exceptions:
        r = a.eval(s, use_none_for_exceptions=False)
        if r is not None:
            return [
                    {"title": "Input", "input": s},
                    {"title": "Eval", "input": s, "output": r},
                    ]
        else:
            return None
