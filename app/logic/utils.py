from __future__ import division
import traceback
import sys
import ast
import re
from StringIO import StringIO
import sympy
from sympy.core.relational import Relational

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
            expr = self.eval_node(node.args[0])
            buffer = ['\\mathrm{solve}\\;', sympy.latex(expr)]

            if not isinstance(expr, Relational):
                buffer.append('=0')

            if len(node.args) > 1:
                buffer.append('\\;\\mathrm{for}\\;')
            for arg in node.args[1:]:
                buffer.append(sympy.latex(self.eval_node(arg)))
                buffer.append(',\\, ')
            if len(node.args) > 1:
                buffer.pop()

            self.latex = ''.join(buffer)
        elif fname == 'limit' and len(node.args) >= 3:
            self.latex = sympy.latex(sympy.Limit(*list(map(self.eval_node, node.args))))
            return
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
    if hasattr(a, 'call'):
        return getattr(a.call.func, 'id', None)
    return None

re_calls = re.compile(r'(Integer|Symbol|Float|Rational)\s*\([\'\"]?([a-zA-Z0-9\.]+)[\'\"]?\s*\)')

def re_calls_sub(match):
    return match.groups()[1]

def removeSymPy(string):
    try:
        return re_calls.sub(re_calls_sub, string)
    except IndexError:
        return string

from sympy.parsing.sympy_parser import (
    AppliedFunction, implicit_multiplication, split_symbols,
    function_exponentiation, implicit_application, OP, NAME,
    _group_parentheses, _apply_functions, _flatten)

def _implicit_multiplication(tokens, local_dict, global_dict):
    result = []
    for tok, nextTok in zip(tokens, tokens[1:]):
        result.append(tok)
        if (isinstance(tok, AppliedFunction) and
                isinstance(nextTok, AppliedFunction)):
            result.append((OP, '*'))
        elif (isinstance(tok, AppliedFunction) and
              nextTok[0] == OP and nextTok[1] == '('):
            # Applied function followed by an open parenthesis
            if tok.function[1] == 'Symbol' and len(tok.args[1][1]) == 3:
                continue
            result.append((OP, '*'))
        elif (tok[0] == OP and tok[1] == ')' and
              isinstance(nextTok, AppliedFunction)):
            # Close parenthesis followed by an applied function
            result.append((OP, '*'))
        elif (tok[0] == OP and tok[1] == ')' and
              nextTok[0] == NAME):
            # Close parenthesis followed by an implicitly applied function
            result.append((OP, '*'))
        elif (tok[0] == nextTok[0] == OP
              and tok[1] == ')' and nextTok[1] == '('):
            # Close parenthesis followed by an open parenthesis
            result.append((OP, '*'))
        elif (isinstance(tok, AppliedFunction) and nextTok[0] == NAME):
            # Applied function followed by implicitly applied function
            result.append((OP, '*'))
    result.append(tokens[-1])
    return result

def implicit_multiplication(result, local_dict, global_dict):
    """Makes the multiplication operator optional in most cases.

    Use this before :func:`implicit_application`, otherwise expressions like
    ``sin 2x`` will be parsed as ``x * sin(2)`` rather than ``sin(2*x)``.

    Example:

    >>> from sympy.parsing.sympy_parser import (parse_expr,
    ... standard_transformations, implicit_multiplication)
    >>> transformations = standard_transformations + (implicit_multiplication,)
    >>> parse_expr('3 x y', transformations=transformations)
    3*x*y
    """
    for step in (_group_parentheses(implicit_multiplication),
                 _apply_functions,
                 _implicit_multiplication):
        result = step(result, local_dict, global_dict)

    result = _flatten(result)
    return result

def custom_implicit_transformation(result, local_dict, global_dict):
    """Allows a slightly relaxed syntax.

    - Parentheses for single-argument method calls are optional.

    - Multiplication is implicit.

    - Symbol names can be split (i.e. spaces are not needed between
      symbols).

    - Functions can be exponentiated.

    Example:

    >>> from sympy.parsing.sympy_parser import (parse_expr,
    ... standard_transformations, implicit_multiplication_application)
    >>> parse_expr("10sin**2 x**2 + 3xyz + tan theta",
    ... transformations=(standard_transformations +
    ... (implicit_multiplication_application,)))
    3*x*y*z + 10*sin(x**2)**2 + tan(theta)

    """
    for step in (split_symbols, implicit_multiplication,
                 implicit_application, function_exponentiation):
        result = step(result, local_dict, global_dict)

    return result
