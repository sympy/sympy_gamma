from __future__ import division
from __future__ import absolute_import
import difflib
import collections
import traceback
import sys
import ast
import re
from io import StringIO
import sympy

from sympy.core.relational import Relational
import tokenize as sympy_tokenize
from six.moves import map
from six.moves import zip

from sympy.parsing.sympy_parser import (
    AppliedFunction, implicit_multiplication, split_symbols,
    function_exponentiation, implicit_application, OP, NAME,
    _group_parentheses, _apply_functions, _flatten, _token_callable
)

OTHER_SYMPY_FUNCTIONS = ('sqrt',)

Arguments = collections.namedtuple('Arguments', 'function args kwargs')


class Eval(object):
    def __init__(self, namespace={}):
        self._namespace = namespace

    def get(self, name):
        return self._namespace.get(name)

    def set(self, name, value):
        self._namespace[name] = value

    def eval_node(self, node):
        tree = ast.fix_missing_locations(ast.Expression(node))
        return eval(compile(tree, '<string>', 'eval'), self._namespace)

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
    formatters = {}

    @staticmethod
    def formats_function(name):
        def _formats_function(f):
            LatexVisitor.formatters[name] = f
            return f
        return _formats_function

    def format(self, name, node):
        formatter = LatexVisitor.formatters.get(name)

        if not formatter:
            return None

        return formatter(node, self)

    def visit_Call(self, node):
        buffer = []
        fname = node.func.id

        # Only apply to lowercase names (i.e. functions, not classes)
        if fname in self.__class__.EXCEPTIONS:
            node.func.id = self.__class__.EXCEPTIONS[fname].__name__
            self.latex = sympy.latex(self.evaluator.eval_node(node))
        else:
            result = self.format(fname, node)
            if result:
                self.latex = result
            elif fname[0].islower() and fname not in OTHER_SYMPY_FUNCTIONS:
                buffer.append("\\mathrm{%s}" % fname.replace('_', '\\_'))
                buffer.append('(')

                latexes = []
                for arg in node.args:
                    if isinstance(arg, ast.Call) and getattr(arg.func, 'id', None) and arg.func.id[0].lower() == arg.func.id[0]:
                        latexes.append(self.visit_Call(arg))
                    else:
                        latexes.append(sympy.latex(self.evaluator.eval_node(arg)))

                buffer.append(', '.join(latexes))
                buffer.append(')')

                self.latex = ''.join(buffer)
            else:
                self.latex = sympy.latex(self.evaluator.eval_node(node))
        return self.latex


@LatexVisitor.formats_function('solve')
def format_solve(node, visitor):
    expr = visitor.evaluator.eval_node(node.args[0])
    buffer = [r'\mathrm{solve}\;', sympy.latex(expr)]

    if not isinstance(expr, Relational):
        buffer.append('=0')

    if len(node.args) > 1:
        buffer.append(r'\;\mathrm{for}\;')
    for arg in node.args[1:]:
        buffer.append(sympy.latex(visitor.evaluator.eval_node(arg)))
        buffer.append(r',\, ')
    if len(node.args) > 1:
        buffer.pop()

    return ''.join(buffer)


@LatexVisitor.formats_function('limit')
def format_limit(node, visitor):
    if len(node.args) >= 3:
        return sympy.latex(
            sympy.Limit(*[visitor.evaluator.eval_node(arg) for arg in node.args]))


@LatexVisitor.formats_function('prime')
def format_prime(node, visitor):
    number = sympy.latex(visitor.evaluator.eval_node(node.args[0]))
    return ''.join([number,
                    r'^\mathrm{',
                    ordinal(int(number)),
                    r'}\; \mathrm{prime~number}'])


@LatexVisitor.formats_function('isprime')
def format_isprime(node, visitor):
    number = sympy.latex(visitor.evaluator.eval_node(node.args[0]))
    return ''.join([r'\mathrm{Is~}', number, r'\mathrm{~prime?}'])


@LatexVisitor.formats_function('nextprime')
def format_nextprime(node, visitor):
    number = sympy.latex(visitor.evaluator.eval_node(node.args[0]))
    return r'\mathrm{Least~prime~greater~than~}' + number


@LatexVisitor.formats_function('factorint')
def format_factorint(node, visitor):
    number = sympy.latex(visitor.evaluator.eval_node(node.args[0]))
    return r'\mathrm{Prime~factorization~of~}' + number


@LatexVisitor.formats_function('factor')
def format_factor(node, visitor):
    expression = sympy.latex(visitor.evaluator.eval_node(node.args[0]))
    return r'\mathrm{Factorization~of~}' + expression


@LatexVisitor.formats_function('solve_poly_system')
def format_factorint(node, visitor):
    equations = visitor.evaluator.eval_node(node.args[0])
    variables = tuple(map(visitor.evaluator.eval_node, node.args[1:]))

    if len(variables) == 1:
        variables = variables[0]

    return ''.join([r'\mathrm{Solve~} \begin{cases} ',
                    r'\\'.join(map(sympy.latex, equations)),
                    r'\end{cases} \mathrm{~for~}',
                    sympy.latex(variables)])


@LatexVisitor.formats_function('plot')
def format_plot(node, visitor):
    if node.args:
        function = sympy.latex(visitor.evaluator.eval_node(node.args[0]))
    else:
        keywords = {}
        for keyword in node.keywords:
            keywords[keyword.arg] = visitor.evaluator.eval_node(keyword.value)
        function = sympy.latex(keywords)
    return r'\mathrm{Plot~}' + function


@LatexVisitor.formats_function('rsolve')
def format_rsolve(node, visitor):
    recurrence = sympy.latex(sympy.Eq(visitor.evaluator.eval_node(node.args[0]), 0))
    if len(node.args) == 3:
        conds = visitor.evaluator.eval_node(node.args[2])
        initconds = '\\\\\n'.join('&' + sympy.latex(sympy.Eq(eqn, val)) for eqn, val in conds.items())
        text = r'&\mathrm{Solve~the~recurrence~}' + recurrence + r'\\'
        condstext = r'&\mathrm{with~initial~conditions}\\'
        return r'\begin{align}' + text + condstext + initconds + r'\end{align}'
    else:
        return r'\mathrm{Solve~the~recurrence~}' + recurrence


diophantine_template = (r"\begin{{align}}&{}\\&\mathrm{{where~}}"
                        r"{}\mathrm{{~are~integers}}\end{{align}}")


@LatexVisitor.formats_function('diophantine')
def format_diophantine(node, visitor):
    expression = visitor.evaluator.eval_node(node.args[0])
    symbols = None
    if isinstance(expression, sympy.Basic):
        symbols = expression.free_symbols
    equation = sympy.latex(sympy.Eq(expression, 0))

    result = r'\mathrm{Solve~the~diophantine~equation~}' + equation
    if symbols:
        result = diophantine_template.format(result, tuple(symbols))
    return result


@LatexVisitor.formats_function('summation')
@LatexVisitor.formats_function('product')
def format_diophantine(node, visitor):
    if node.func.id == 'summation':
        klass = sympy.Sum
    else:
        klass = sympy.Product
    return sympy.latex(klass(*list(map(visitor.evaluator.eval_node, node.args))))


@LatexVisitor.formats_function('help')
def format_help(node, visitor):
    if node.args:
        function = visitor.evaluator.eval_node(node.args[0])
        return r'\mathrm{Show~documentation~for~}' + function.__name__
    return r'\mathrm{Show~documentation~(requires~1~argument)}'


class TopCallVisitor(ast.NodeVisitor):
    def __init__(self):
        super(TopCallVisitor, self).__init__()
        self.call = None

    def visit_Call(self, node):
        self.call = node

    def visit_Name(self, node):
        if not self.call:
            self.call = node

    def visit_NameConstant(self, node):
        if not self.call:
            self.call = node


# From https://stackoverflow.com/a/739301/262727
def ordinal(n):
    if 10 <= n % 100 < 20:
        return 'th'
    else:
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, "th")


# TODO: modularize all of this
def latexify(string, evaluator):
    a = LatexVisitor()
    a.evaluator = evaluator
    a.visit(ast.parse(string))
    return a.latex


def topcall(string):
    a = TopCallVisitor()
    a.visit(ast.parse(string))
    if hasattr(a, 'call'):
        return getattr(a.call.func, 'id', None)
    return None


def arguments(string_or_node, evaluator):
    node = None
    if not isinstance(string_or_node, ast.Call):
        a = TopCallVisitor()
        a.visit(ast.parse(string_or_node))

        if hasattr(a, 'call'):
            node = a.call
    else:
        node = string_or_node

    if node:
        if isinstance(node, ast.Call):
            name = getattr(node.func, 'id', None)  # when is it undefined?
            args, kwargs = None, None
            if node.args:
                args = list(map(evaluator.eval_node, node.args))

            kwargs = node.keywords
            if kwargs:
                kwargs = {kwarg.arg: evaluator.eval_node(kwarg.value) for kwarg in kwargs}

            return Arguments(name, args, kwargs)
        elif isinstance(node, ast.Name):
            return Arguments(node.id, [], {})

        elif isinstance(node, ast.NameConstant):
            return Arguments(node.value, [], {})
    return None


re_calls = re.compile(r'(Integer|Symbol|Float|Rational)\s*\([\'\"]?([a-zA-Z0-9\.]+)[\'\"]?\s*\)')


def re_calls_sub(match):
    return match.groups()[1]


def removeSymPy(string):
    try:
        return re_calls.sub(re_calls_sub, string)
    except IndexError:
        return string


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
            if (tok.function[1] == 'Symbol' and
                len(tok.args[1][1]) == 3):
                # Allow implicit function symbol creation
                # TODO XXX need some way to offer alternative parsing here -
                # sometimes we want this and sometimes not, hard to tell when
                # (making it context-sensitive based on input function best)
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
        elif (tok[0] == NAME and
              not _token_callable(tok, local_dict, global_dict) and
              nextTok[0] == OP and nextTok[1] == '('):
            # Constant followed by parenthesis
            result.append((OP, '*'))
        elif (tok[0] == NAME and
              not _token_callable(tok, local_dict, global_dict) and
              nextTok[0] == NAME and
              not _token_callable(nextTok, local_dict, global_dict)):
            # Constant followed by constant
            result.append((OP, '*'))
        elif (tok[0] == NAME and
              not _token_callable(tok, local_dict, global_dict) and
              (isinstance(nextTok, AppliedFunction) or nextTok[0] == NAME)):
            # Constant followed by (implicitly applied) function
            result.append((OP, '*'))
    if tokens:
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


SYNONYMS = {
    u'derivative': 'diff',
    u'derive': 'diff',
    u'integral': 'integrate',
    u'antiderivative': 'integrate',
    u'factorize': 'factor',
    u'graph': 'plot',
    u'draw': 'plot'
}


def synonyms(tokens, local_dict, global_dict):
    """Make some names synonyms for others.

    This is done at the token level so that the "stringified" output that
    Gamma displays shows the correct function name. Must be applied before
    auto_symbol.
    """

    result = []
    for token in tokens:
        if token[0] == NAME:
            if token[1] in SYNONYMS:
                result.append((NAME, SYNONYMS[token[1]]))
                continue
        result.append(token)
    return result


def close_matches(s, global_dict):
    """
    Checks undefined names to see if they are close matches to a defined name.
    """

    tokens = sympy_tokenize.generate_tokens(StringIO(s.strip()).readline)
    result = []
    has_result = False
    all_names = set(global_dict).union(SYNONYMS)

    # strip the token location info to avoid strange untokenize results
    tokens = [(tok[0], tok[1]) for tok in tokens]
    for token in tokens:
        if (token[0] == NAME and
            token[1] not in all_names and
            len(token[1]) > 1):
            matches = difflib.get_close_matches(token[1], all_names)

            if matches and matches[0] == token[1]:
                matches = matches[1:]
            if matches:
                result.append((NAME, matches[0]))
                has_result = True
                continue
        result.append(token)
    if has_result:
        return sympy_tokenize.untokenize(result).strip()
    return None
