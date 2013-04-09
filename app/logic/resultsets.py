import sys
import json
import sympy
from sympy.core.function import FunctionClass
import docutils.core
from operator import itemgetter
import diffsteps
import intsteps


class FakeSymPyFunction(object):
    """Used to delay evaluation of a SymPy function.

    In logic.py, add a namespace entry to ``sympify`` that shadows the
    function to be delayed whose value is
    ``fake_sympy_function('function_name')``.

    """
    def __init__(self, fname, args, kwargs):
        self.function = fname
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        if self.kwargs:
            kwargs = ', '.join(key + '=' + repr(arg)
                               for key, arg in self.kwargs.items())
            kwargs = ', ' + kwargs
        else:
            kwargs = ''
        return '{function}({args}{kwargs})'.format(
            function=self.function,
            args=', '.join(map(repr, self.args)),
            kwargs=kwargs
        )

    def as_latex(self):
        if self.kwargs:
            kwargs = ', '.join(key + '=' + sympy.latex(arg)
                               for key, arg in self.kwargs.items())
            kwargs = ', ' + kwargs
        else:
            kwargs = ''
            return '{function}({args}{kwargs})'.format(
                function='\\mathrm{' + self.function.replace('_', '\\_') + '}',
                args=', '.join(map(sympy.latex, self.args)),
                kwargs=kwargs
            )

    def xreplace(self, kwargs):
        def _replacer(expr):
            try:
                return expr.xreplace(kwargs)
            except (TypeError, AttributeError):
                return expr
        self.args = list(map(_replacer, self.args))
        return self

    @staticmethod
    def make_result_card(func, title, **kwargs):
        def eval_fake(evaluator, variable, parameters=None):
            func_data = evaluator.get('input_evaluated')
            return func(*func_data.args)

        return FakeResultCard(
            title,
            "%s",
            no_pre_output,
            eval_method=eval_fake,
            **kwargs
        )


def fake_sympy_function(fname):
    def _faker(*args, **kwargs):
        return FakeSymPyFunction(fname, args, kwargs)
    return _faker


class ResultCard(object):
    """
    Operations to generate a result card.

    title -- Title of the card

    result_statement -- Statement evaluated to get result

    pre_output_function -- Takes input expression and a symbol, returns a
    SymPy object
    """
    def __init__(self, title, result_statement, pre_output_function,
                 **kwargs):
        self.card_info = kwargs
        self.title = title
        self.result_statement = result_statement
        self.pre_output_function = pre_output_function

    def eval(self, evaluator, variable, parameters=None):
        if parameters is None:
            parameters = {}
        parameters = self.default_parameters(parameters)
        line = self.result_statement.format(_var=variable, **parameters)
        line = line % 'input_evaluated'
        result = evaluator.eval(line, use_none_for_exceptions=True)

        if self.card_info.get('sympify') or 'sympify' not in self.card_info:
            return sympy.sympify(result)
        return result

    def format_input(self, input_repr, variable, **parameters):
        if parameters is None:
            parameters = {}
        parameters = self.default_parameters(parameters)
        if 'format_input_function' in self.card_info:
            return self.card_info['format_input_function'](
                self.result_statement, input_repr, variable)
        return self.result_statement.format(_var=variable, **parameters) % input_repr

    def format_output(self, output, formatter):
        if 'format_output_function' in self.card_info:
            return self.card_info['format_output_function'](output, formatter)
        return formatter(output)

    def format_title(self, input_evaluated):
        if self.card_info.get('format_title_function'):
            return self.card_info['format_title_function'](self.title,
                                                           input_evaluated)
        return self.title

    def default_parameters(self, kwargs):
        if 'parameters' in self.card_info:
            for arg in self.card_info['parameters']:
                kwargs.setdefault(arg, '')
        return kwargs


class FakeResultCard(ResultCard):
    """ResultCard whose displayed expression != actual code.

    Used when creating the result to be displayed involves code that a user
    would not normally need to do, e.g. calculating plot points (where a
    user would simply use ``plot``)."""

    def __init__(self, *args, **kwargs):
        super(FakeResultCard, self).__init__(*args, **kwargs)
        assert 'eval_method' in kwargs

    def eval(self, evaluator, variable, parameters=None):
        if parameters is None:
            parameters = {}
        return self.card_info['eval_method'](evaluator, variable, parameters)


class MultiResultCard(ResultCard):
    """Tries multiple statements and displays the first that works."""

    def __init__(self, title, *cards):
        super(MultiResultCard, self).__init__(title, '', lambda *args: '')
        self.cards = cards
        self.cards_used = []

    def eval(self, evaluator, variable, parameters):
        self.cards_used = []
        original = sympy.sympify(evaluator.eval("input_evaluated"))
        results = []
        for card in self.cards:
            result = card.eval(evaluator, variable, parameters)
            if result != None and result != original and result not in results:
                # TODO Implicit state is bad, come up with better API
                self.cards_used.append(card)
                results.append((card, result))
        if results:
            return results
        return "None"

    def format_input(self, input_repr, variable):
        html = ["<ul>"]
        html.extend(
            "<li>" + str(c.format_input(input_repr, variable)) + "</li>"
            for c in self.cards_used)
        html.append("</ul>")
        return "\n".join(html)

    def format_output(self, output, formatter):
        html = ["<ul>"]
        for card, result in output:
            html.append("<li>")
            html.append(card.format_output(result, formatter))
            html.append("</li>")
        html.append("</ul>")
        return "\n".join(html)


# Decide which result card set to use

TRUE_AND_FIND_MORE = "True, and look for more result sets"

def is_fake_function(function):
    def _check(input_evaluated):
        return (isinstance(input_evaluated, FakeSymPyFunction) and
                input_evaluated.function == function)
    return _check

def is_derivative(input_evaluated):
    return isinstance(input_evaluated, sympy.Derivative)

def is_integral(input_evaluated):
    return isinstance(input_evaluated, sympy.Integral)

def is_integer(input_evaluated):
    return isinstance(input_evaluated, sympy.Integer)

def is_rational(input_evaluated):
    return isinstance(input_evaluated, sympy.Rational)

def is_float(input_evaluated):
    return isinstance(input_evaluated, sympy.Float)

def is_numbersymbol(input_evaluated):
    return isinstance(input_evaluated, sympy.NumberSymbol)

def is_constant(input_evaluated):
    # is_constant reduces trig identities (even with simplify=False?) so we
    # check free_symbols instead
    return (hasattr(input_evaluated, 'free_symbols') and
            not input_evaluated.free_symbols)

def is_complex(input_evaluated):
    try:
        return sympy.I in input_evaluated.atoms()
    except (AttributeError, TypeError):
        return False

def is_trig(input_evaluated):
    try:
        if (isinstance(input_evaluated, sympy.Basic) and
            any(input_evaluated.find(func)
                for func in (sympy.sin, sympy.cos, sympy.tan,
                             sympy.csc, sympy.sec, sympy.cot))):
            return TRUE_AND_FIND_MORE
        return False
    except AttributeError:
        return False

def is_uncalled_function(input_evaluated):
    return hasattr(input_evaluated, '__call__') and not isinstance(input_evaluated, sympy.Basic)


# Functions to convert input and extract variable used

def extract_integrand(input_evaluated, variable):
    assert isinstance(input_evaluated, sympy.Integral)
    if len(input_evaluated.limits[0]) > 1:  # if there are limits
        variable = input_evaluated.limits
    elif len(input_evaluated.variables) == 1:
        variable = (input_evaluated.variables[0],)
    return input_evaluated.function, variable

def extract_derivative(input_evaluated, variable):
    assert isinstance(input_evaluated, sympy.Derivative)
    if len(input_evaluated.variables) == 1:
        variable = input_evaluated.variables[0]
    return input_evaluated.expr, variable

def extract_series(input_evaluated, variable):
    assert (isinstance(input_evaluated, FakeSymPyFunction) and
            input_evaluated.function == 'series')
    args = input_evaluated.args
    if len(args) >= 2:
        return input_evaluated, args[1]
    elif len(args) == 1:
        try:
            equation = sympy.sympify(args[0])
            return input_evaluated, equation.free_symbols.pop()
        except SympifyError:
            pass
    return input_evaluated, variable

def extract_solve(input_evaluated, variable):
    assert (isinstance(input_evaluated, FakeSymPyFunction) and
            input_evaluated.function == 'solve')
    args = input_evaluated.args
    if len(args) >= 2:
        return input_evaluated, args[1:]
    elif len(args) == 1:
        try:
            equation = sympy.sympify(args[0])
            return input_evaluated, equation.free_symbols.pop()
        except SympifyError:
            pass
    return input_evaluated, variable

def extract_solve_poly_system(input_evaluated, variable):
    assert (isinstance(input_evaluated, FakeSymPyFunction) and
            input_evaluated.function == 'solve_poly_system')
    args = input_evaluated.args
    if len(args) >= 2:
        return input_evaluated, args[1:]
    return input_evaluated, None

def do_nothing(input_evaluated, variable):
    return input_evaluated, variable

def default_variable(input_evaluated, variable):
    return input_evaluated, sympy.Symbol('x')


# Formatting functions

def format_nothing(arg, formatter):
    return arg

def format_steps(arg, formatter):
    return '<div class="steps">{}</div>'.format(arg)

def format_long_integer(line, integer, variable):
    intstr = str(integer)
    if len(intstr) > 100:
        # \xe2 is Unicode ellipsis
        return intstr[:20] + "..." + intstr[len(intstr) - 21:]
    return line % intstr

def format_integral(line, integrand, limits):
    return line.format(_var=', '.join(map(repr, limits))) % integrand

def format_dict_title(*title):
    def _format_dict(dictionary, formatter):
        html = ['<table>',
                '<thead><tr><th>{}</th><th>{}</th></tr></thead>'.format(*title),
                '<tbody>']
        for key, val in sorted(dictionary.iteritems(), key=itemgetter(0)):
            html.append('<tr><td>{}</td><td>{}</td></tr>'.format(key, val))
        html.append('</tbody></table>')
        return '\n'.join(html)
    return _format_dict

def format_list(items, formatter):
    try:
        html = ['<ul>']
        for item in items:
            html.append('<li>{}</li>'.format(formatter(item)))
        html.append('</ul>')
        return '\n'.join(html)
    except TypeError:  # not iterable, like None
        return formatter(items)

def format_series_fake_title(title, evaluated):
    if len(evaluated.args) >= 3:
        about = evaluated.args[2]
    else:
        about = 0
    if len(evaluated.args) >= 4:
        up_to = evaluated.args[3]
    else:
        up_to = 6
    return title.format(about, up_to)

DIAGRAM_CODE = """
<div class="factorization-diagram" data-primes="{primes}">
    <div></div>
    <p><a href="http://mathlesstraveled.com/2012/10/05/factorization-diagrams/">About this diagram</a></p>
</div>
"""

def format_factorization_diagram(factors, formatter):
    primes = []
    for prime in reversed(sorted(factors)):
        times = factors[prime]
        primes.extend([prime] * times)
    return DIAGRAM_CODE.format(primes=primes)

GRAPHING_CODE = """
<div class="graph"
     data-function="{function}"
     data-variable="{variable}"
     data-xvalues="{xvalues}"
     data-yvalues="{yvalues}">
</div>
"""

def format_graph(graph_data, formatter):
    return GRAPHING_CODE.format(**graph_data)

def eval_graph(evaluator, variable, parameters=None):
    if parameters is None:
        parameters = {}

    xmin, xmax = parameters.get('xmin', -10), parameters.get('xmax', 10)
    from sympy.plotting.plot import LineOver1DRangeSeries
    func = evaluator.eval("input_evaluated")

    free_symbols = sympy.sympify(func).free_symbols
    if len(free_symbols) != 1 or variable not in free_symbols:
        raise ValueError("Cannot graph function of multiple variables")

    try:
        series = LineOver1DRangeSeries(
            func, (variable, xmin, xmax),
            nb_of_points=150)
        # returns a list of [[x,y], [next_x, next_y]] pairs
        series = series.get_segments()
    except TypeError:
        raise ValueError("Cannot graph function")

    xvalues = []
    yvalues = []

    def limit_y(y):
        CEILING = 1e8
        if y > CEILING:
            y = CEILING
        if y < -CEILING:
            y = -CEILING
        return y

    for point in series:
        xvalues.append(point[0][0])
        yvalues.append(limit_y(point[0][1]))
    xvalues.append(series[-1][1][0])
    yvalues.append(limit_y(series[-1][1][1]))
    return {
        'function': sympy.jscode(sympy.sympify(func)),
        'variable': repr(variable),
        'xvalues': json.dumps(xvalues),
        'yvalues': json.dumps(yvalues)
    }

def eval_factorization(evaluator, variable, parameters=None):
    number = evaluator.eval("input_evaluated")
    factors = sympy.ntheory.factorint(number, limit=100)
    smallfactors = {}
    for factor in factors:
        if factor <= 100:
            smallfactors[factor] = factors[factor]
    return smallfactors

def eval_factorization_diagram(evaluator, variable, parameters=None):
    # Raises ValueError (stops card from appearing) if the factors are too
    # large so that the diagram will look nice
    number = int(evaluator.eval("input_evaluated"))
    if number > 256:
        raise ValueError("Number too large")
    factors = sympy.ntheory.factorint(number, limit=101)
    smallfactors = {}
    for factor in factors:
        if factor <= 256:
            smallfactors[factor] = factors[factor]
        else:
            raise ValueError("Number too large")
    return smallfactors

def eval_integral(evaluator, variable, parameters=None):
    return sympy.integrate(evaluator.get("input_evaluated"), *variable)

def eval_diffsteps(evaluator, variable, paramters=None):
    return diffsteps.print_html_steps(evaluator.get("input_evaluated"), variable)

def eval_intsteps(evaluator, variable, paramters=None):
    if len(variable) != 1:
        raise ValueError("Can only give steps for single integrals")
    variable = variable[0]

    try:
        # For definite integrals
        variable = variable[0]
    except TypeError:
        pass

    return intsteps.print_html_steps(evaluator.get("input_evaluated"), variable)

# http://www.python.org/dev/peps/pep-0257/
def trim(docstring):
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxint
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxint:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)

def eval_function_docs(evaluator, variable, parameters=None):
    docstring = trim(evaluator.get("input_evaluated").__doc__)
    return docutils.core.publish_parts(docstring, writer_name='html4css1',
                                       settings_overrides={'_disable_config': True})['html_body']

# Result cards

no_pre_output = lambda *args: ""

all_cards = {
    'roots': ResultCard(
        "Roots",
        "solve(%s, {_var})",
        lambda statement, var, *args: var),

    'integral': ResultCard(
        "Integral",
        "integrate(%s, {_var})",
        sympy.Integral),

    'integral_fake': FakeResultCard(
        "Integral",
        "integrate(%s, {_var})",
        lambda i, var: sympy.Integral(i, *var),
        eval_method=eval_integral,
        format_input_function=format_integral
    ),

    'diff': ResultCard("Derivative",
                       "diff(%s, {_var})",
                       sympy.Derivative),

    'diffsteps': FakeResultCard(
        "Derivative Steps",
        "diff(%s, {_var})",
        no_pre_output,
        format_output_function=format_steps,
        eval_method=eval_diffsteps),

    'intsteps': FakeResultCard(
        "Integral Steps",
        "integrate(%s, {_var})",
        no_pre_output,
        format_output_function=format_steps,
        eval_method=eval_intsteps,
        format_input_function=format_integral),

    'series': ResultCard(
        "Series expansion around 0",
        "series(%s, {_var}, 0, 10)",
        no_pre_output),

    'digits': ResultCard(
        "Digits in base-10 expansion of number",
        "len(str(%s))",
        no_pre_output,
        format_input_function=format_long_integer),

    'factorization': FakeResultCard(
        "Factors less than 100",
        "factorint(%s, limit=100)",
        no_pre_output,
        format_input_function=format_long_integer,
        format_output_function=format_dict_title("Factor", "Times"),
        eval_method=eval_factorization),

    'factorizationDiagram': FakeResultCard(
        "Factorization Diagram",
        "factorint(%s, limit=256)",
        no_pre_output,
        format_output_function=format_factorization_diagram,
        eval_method=eval_factorization_diagram),

    'float_approximation': ResultCard(
        "Floating-point approximation",
        "(%s).evalf({digits})",
        no_pre_output,
        parameters=['digits'],
        sympify=False),

    'fractional_approximation': ResultCard(
        "Fractional approximation",
        "nsimplify(%s)",
        no_pre_output),

    'absolute_value': ResultCard(
        "Absolute value",
        "Abs(%s)",
        lambda s, *args: "|{}|".format(s)),

    'polar_angle': ResultCard(
        "Angle in the complex plane",
        "atan2(*(%s).as_real_imag()).evalf()",
        lambda s, *args: sympy.atan2(*sympy.sympify(s).as_real_imag())),

    'conjugate': ResultCard(
        "Complex conjugate",
        "conjugate(%s)",
        lambda s, *args: sympy.conjugate(s)),

    'trigexpand': ResultCard(
        "Alternate form",
        "(%s).expand(trig=True)",
        lambda statement, var, *args: statement),

    'trigsimp': ResultCard(
        "Alternate form",
        "trigsimp(%s)",
        lambda statement, var, *args: statement),

    'trigsincos': ResultCard(
        "Alternate form",
        "(%s).rewrite(csc, sin, sec, cos, cot, tan)",
        lambda statement, var, *args: statement
    ),

    'trigexp': ResultCard(
        "Alternate form",
        "(%s).rewrite(sin, exp, cos, exp, tan, exp)",
        lambda statement, var, *args: statement
    ),

    'graph': FakeResultCard(
        "Graph",
        "plot(%s)",
        no_pre_output,
        format_output_function=format_graph,
        eval_method=eval_graph,
        parameters=['xmin', 'xmax']),

    'function_docs': FakeResultCard(
        "Documentation",
        "help(%s)",
        no_pre_output,
        eval_method=eval_function_docs,
        format_output_function=format_nothing
    ),

    'series_fake': FakeSymPyFunction.make_result_card(
        sympy.series,
        "Series expansion about {0} up to {1}",
        format_title_function=format_series_fake_title),

    'solve_fake': FakeSymPyFunction.make_result_card(
        sympy.solve,
        "Solutions",
        format_output_function=format_list),

    'solve_poly_system_fake': FakeSymPyFunction.make_result_card(
        sympy.solve_poly_system,
        "Solutions",
        format_output_function=format_list)
}

def get_card(name):
    return all_cards.get(name, None)

all_cards['trig_alternate'] = MultiResultCard(
    "Alternate form",
    get_card('trigexpand'),
    get_card('trigsimp'),
    get_card('trigsincos'),
    get_card('trigexp')
)


result_sets = [
    (is_integral, extract_integrand, ['integral_fake', 'intsteps']),
    (is_derivative, extract_derivative, ['diff', 'diffsteps', 'graph']),
    (is_fake_function('series'), extract_series, ['series_fake']),
    (is_fake_function('solve'), extract_solve, ['solve_fake']),
    (is_fake_function('solve_poly_system'), extract_solve_poly_system,
     ['solve_poly_system_fake']),
    (is_integer, default_variable,
     ['digits', 'float_approximation',
                 'factorization', 'factorizationDiagram']),
    (is_rational, default_variable, ['float_approximation']),
    (is_float, default_variable, ['fractional_approximation']),
    (is_numbersymbol, default_variable, ['float_approximation']),
    (is_constant, default_variable, ['float_approximation']),
    (is_complex, default_variable,
     ['absolute_value', 'polar_angle', 'conjugate']),
    (is_trig, do_nothing, ['trig_alternate']),
    (is_uncalled_function, default_variable, ['function_docs']),
    (lambda x: True, do_nothing, ['graph', 'roots', 'diff', 'integral', 'series'])
]

def find_result_set(input_evaluated):
    ci, rc = None, []
    for (predicate, convert_input, result_cards) in result_sets:
        result = predicate(input_evaluated)
        if result is True:
            if ci:
                rc.extend(result_cards)
                return ci, rc
            return convert_input, result_cards
        elif result is TRUE_AND_FIND_MORE:
            ci = convert_input
            rc.extend(result_cards)
