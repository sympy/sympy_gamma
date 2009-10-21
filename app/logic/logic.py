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
        a = Eval()
        r = a.eval(s, use_none_for_exceptions=True)
        if r:
            return [
                    {"title": "Input", "input": s},
                    {"title": "Eval", "input": s, "output": r},
                    ]
        else:
            return None
