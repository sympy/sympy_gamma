from utils import Eval
from sympy import pprint 

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
        if not len(s):
            return
        r = a.eval(u'pprint(%s)' % s, use_none_for_exceptions=False)
        if r is not None:
            result = [
                    {"title": "Input", "input": s},
                    {"title": "SymPy", "input": s, "output": r},
                    ]
            code = """\
s = %s
a = s.atoms(Symbol)
if len(a):
    x = a.pop()
    result = %s
else:
    result = None
pprint(result)
"""
            line = "simplify(%s)" % s
            simplified = a.eval(line, use_none_for_exceptions=True)
            r = a.eval(code % (simplified, line), use_none_for_exceptions=True)
            if simplified and simplified != "None" and simplified != s:
                result.append(
                        {"title": "Simplification", "input": line,
                            "output": r})
            line = "solve(%s, x)" % simplified
            r = a.eval(code % (simplified, line), use_none_for_exceptions=True)
            if r and r != "None":
                result.append(
                        {"title": "Roots", "input": line,
                            "output": r})
            line = "diff(%s, x)" % simplified
            r = a.eval(code % (simplified, line), use_none_for_exceptions=True)
            if r and r != "None":
                result.append(
                        {"title": "Derivative", "input": line,
                            "output": r})
            line = "integrate(%s, x)" % simplified
            r = a.eval(code % (simplified, line), use_none_for_exceptions=True)
            if r and r != "None":
                result.append(
                        {"title": "Indefinite integral", "input": line,
                            "output": r})
            line = "series(%s, x, 0, 10)" % simplified
            r = a.eval(code % (simplified, line), use_none_for_exceptions=True)
            if r and r != "None":
                result.append(
                        {"title": "Series expansion around 0", "input": line,
                            "output": r})
            for item in result:
                for k in item:
                        item[k] = item[k].replace('None', '')
            return result
        else:
            return None
