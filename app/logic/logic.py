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
            result = [
                    {"title": "Input", "input": s},
                    {"title": "SymPy", "input": s, "output": r},
                    ]
            code = """\
s = %s
a = s.atoms(Symbol)
if len(a) == 1:
    x = a.pop()
    result = %s
else:
    result = None
result
"""
            line = "diff(%s, x)" % s
            r = a.eval(code % (s, line), use_none_for_exceptions=True)
            if r and r != "None":
                result.append(
                        {"title": "Derivative", "input": line,
                            "output": r})
            line = "integrate(%s, x)" % s
            r = a.eval(code % (s, line), use_none_for_exceptions=True)
            if r and r != "None":
                result.append(
                        {"title": "Indefinite integral", "input": line,
                            "output": r})
            return result
        else:
            return None
