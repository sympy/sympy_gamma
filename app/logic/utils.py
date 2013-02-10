from __future__ import division
import traceback
import sys
import ast
import re
from StringIO import StringIO
import sympy

class Eval(object):

    def __init__(self, namespace={}):
        self._namespace = namespace

    def get(self, name):
        return self._namespace.get(name)

    def set(self, name, value):
        self._namespace[name] = value

    def eval(self, x, use_none_for_exceptions=False, repr_expression=True):
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
                eval(compile(s, '', 'exec', division.compiler_flag), globals, globals)

                if not z is None:
                    r = eval(z, globals)

                    if repr_expression:
                        r = repr(r)
                else:
                    r = ''

                if repr_expression:
                    sys.stdout.seek(0)
                    r = sys.stdout.read() + r
            finally:
                sys.stdout = old_stdout
            return r
        except:
            if use_none_for_exceptions:
                return
            etype, value, tb = sys.exc_info()
            # If we decide in the future to remove the first frame fromt he
            # traceback (since it links to our code, so it could be confusing
            # to the user), it's easy to do:
            #tb = tb.tb_next
            s = "".join(traceback.format_exception(etype, value, tb))
            return s

class LatexVisitor(ast.NodeVisitor):
    EXCEPTIONS = {'integrate': sympy.Integral, 'diff': sympy.Derivative}

    def eval_node(self, node):
        tree = ast.fix_missing_locations(ast.Expression(node))
        return eval(compile(tree, '<string>', 'eval'), self.namespace)

    def visit_Call(self, node):
        buffer = []
        fname = node.func.id

        # Only apply to lowercase names (i.e. functions, not classes)
        if fname in self.__class__.EXCEPTIONS:
            node.func.id = self.__class__.EXCEPTIONS[fname].__name__
            self.latex = sympy.latex(self.eval_node(node))
        elif fname == 'solve':
            buffer = ['\\mathrm{solve}\\;',
                      sympy.latex(self.eval_node(node.args[0]))]
            if len(node.args) > 1:
                buffer.append('\\;\\mathrm{for}\\;')
            for arg in node.args[1:]:
                buffer.append(sympy.latex(self.eval_node(arg)))
                buffer.append(',\\, ')
            if len(node.args) > 1:
                buffer.pop()
            self.latex = ''.join(buffer)
        elif fname[0].lower() == fname[0]:
            buffer.append("\\mathrm{%s}" % fname.replace('_', '\\_'))
            buffer.append('(')

            latexes = []
            for arg in node.args:
                if isinstance(arg, ast.Call) and arg.func.id[0].lower() == arg.func.id[0]:
                    latexes.append(self.visit_Call(arg))
                else:
                    latexes.append(sympy.latex(self.eval_node(arg)))

            buffer.append(', '.join(latexes))
            buffer.append(')')

            self.latex = ''.join(buffer)
            return ''.join(buffer)

class TopCallVisitor(ast.NodeVisitor):
    def visit_Call(self, node):
        self.call = node

def latexify(string, evaluator):
    a = LatexVisitor()
    a.namespace = evaluator._namespace
    a.visit(ast.parse(string))
    return a.latex

def topcall(string):
    a = TopCallVisitor()
    a.visit(ast.parse(string))
    return a.call

re_calls = re.compile(r'(Integer|Symbol|Float|Rational)\s*\([\'\"]?([a-zA-Z0-9\.]+)[\'\"]?\s*\)')

def re_calls_sub(match):
    return match.groups()[1]

def removeSymPy(string):
    try:
        return re_calls.sub(re_calls_sub, string)
    except IndexError:
        return string
