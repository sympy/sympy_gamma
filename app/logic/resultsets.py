import sys
import json
import sympy
from sympy.core.function import FunctionClass
import docutils.core
from operator import itemgetter
import diffsteps
import intsteps


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

    def eval(self, evaluator, components, parameters=None):
        if parameters is None:
            parameters = {}
        else:
            parameters = parameters.copy()

        parameters = self.default_parameters(parameters)

        for component, val in components.items():
            parameters[component] = val

        variable = components['variable']

        line = self.result_statement.format(_var=variable, **parameters)
        line = line % 'input_evaluated'
        result = evaluator.eval(line, use_none_for_exceptions=True,
                                repr_expression=False)

        return result

    def format_input(self, input_repr, components, **parameters):
        if parameters is None:
            parameters = {}
        parameters = self.default_parameters(parameters)
        variable = components['variable']
        if 'format_input_function' in self.card_info:
            return self.card_info['format_input_function'](
                self.result_statement, input_repr, components)
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

    def __repr__(self):
        return "<ResultCard '{}'>".format(self.title)


class FakeResultCard(ResultCard):
    """ResultCard whose displayed expression != actual code.

    Used when creating the result to be displayed involves code that a user
    would not normally need to do, e.g. calculating plot points (where a
    user would simply use ``plot``)."""

    def __init__(self, *args, **kwargs):
        super(FakeResultCard, self).__init__(*args, **kwargs)
        assert 'eval_method' in kwargs

    def eval(self, evaluator, components, parameters=None):
        if parameters is None:
            parameters = {}
        return self.card_info['eval_method'](evaluator, components, parameters)


class MultiResultCard(ResultCard):
    """Tries multiple statements and displays the first that works."""

    def __init__(self, title, *cards):
        super(MultiResultCard, self).__init__(title, '', lambda *args: '')
        self.cards = cards
        self.cards_used = []

    def eval(self, evaluator, components, parameters):
        self.cards_used = []
        results = []

        # TODO Implicit state is bad, come up with better API
        # in particular a way to store variable, cards used
        for card in self.cards:
            try:
                result = card.eval(evaluator, components, parameters)
            except ValueError:
                continue
            if result != None:
                if not any(result == r[1] for r in results):
                    self.cards_used.append(card)
                    results.append((card, result))
        if results:
            self.input_repr = evaluator.get("input_evaluated")
            self.components = components
            return results
        return "None"

    def format_input(self, input_repr, components):
        return None

    def format_output(self, output, formatter):
        if not isinstance(output, list):
            return output
        html = ["<ul>"]
        for card, result in output:
            html.append("<li>")
            html.append('<div class="cell_input">')
            html.append(card.format_input(self.input_repr, self.components))
            html.append('</div>')
            html.append(card.format_output(result, formatter))
            html.append("</li>")
        html.append("</ul>")
        return "\n".join(html)


# Decide which result card set to use

def is_derivative(input_evaluated):
    return isinstance(input_evaluated, sympy.Derivative)

def is_integral(input_evaluated):
    return isinstance(input_evaluated, sympy.Integral)

def is_integer(input_evaluated):
    return isinstance(input_evaluated, sympy.Integer)

def is_rational(input_evaluated):
    return isinstance(input_evaluated, sympy.Rational) and not input_evaluated.is_Integer

def is_float(input_evaluated):
    return isinstance(input_evaluated, sympy.Float)

def is_numbersymbol(input_evaluated):
    return isinstance(input_evaluated, sympy.NumberSymbol)

def is_constant(input_evaluated):
    # is_constant reduces trig identities (even with simplify=False?) so we
    # check free_symbols instead
    return (hasattr(input_evaluated, 'free_symbols') and
            not input_evaluated.free_symbols)

def is_approximatable_constant(input_evaluated):
    # is_constant, but exclude Integer/Float/infinity
    return (hasattr(input_evaluated, 'free_symbols') and
            not input_evaluated.free_symbols and
            not input_evaluated.is_Integer and
            not input_evaluated.is_Float and
            input_evaluated.is_finite is not True)

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
            return True
    except AttributeError:
        pass
    return False

def is_not_constant_basic(input_evaluated):
    return not is_constant(input_evaluated) and isinstance(input_evaluated, sympy.Basic)

def is_uncalled_function(input_evaluated):
    return hasattr(input_evaluated, '__call__') and not isinstance(input_evaluated, sympy.Basic)

def is_matrix(input_evaluated):
    return isinstance(input_evaluated, sympy.Matrix)


# Functions to convert input and extract variable used

def default_variable(arguments, evaluated):
    try:
        variables = list(evaluated.atoms(sympy.Symbol))
    except:
        variables = []

    return {
        'variables': variables,
        'variable': variables[0] if variables else None
    }

def extract_first(arguments, evaluated):
    result = default_variable(arguments, evaluated)
    result['input_evaluated'] = arguments[1][0]
    return result

def extract_integral(arguments, evaluated):
    limits = arguments[1][1:]
    variables = []

    if not limits:
        variables = [arguments[1][0].atoms(sympy.Symbol).pop()]
        limits = variables
    else:
        for limit in limits:
            if isinstance(limit, tuple):
                variables.append(limit[0])
            else:
                variables.append(limit)

    return {
        'integrand': arguments[1][0],
        'variables': variables,
        'variable': variables[0],
        'limits': limits
    }

def extract_derivative(arguments, evaluated):
    variables = list(sorted(arguments[1][0].atoms(sympy.Symbol), key=lambda x: x.name))

    variable = arguments[1][1:]
    if variable:
        variables.remove(variable[0])
        variables.insert(0, variable[0])

    return {
        'function': arguments[1][0],
        'variables': variables,
        'variable': variables[0],
        'input_evaluated': arguments[1][0]
    }

def extract_plot(arguments, evaluated):
    result = extract_first(arguments, evaluated)
    result['variables'] = list(arguments.args[0].atoms(sympy.Symbol))
    result['variable'] = result['variables'][0]
    return result

# Formatting functions

def format_by_type(result, formatter):
    if isinstance(result, (list, tuple)):
        return format_list(result, formatter)
    else:
        return formatter(result)

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

def format_integral(line, result, components):
    if components['limits']:
        limits = ', '.join(map(repr, components['limits']))
    else:
        limits = ', '.join(map(repr, components['variables']))

    return line.format(_var=limits) % components['integrand']

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
        if len(items) == 0:
            return "<p>No result</p>"
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

def format_approximator(approximation, formatter):
    obj, digits = approximation
    return formatter(obj, r'\approx', obj.evalf(digits))

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

def eval_graph(evaluator, components, parameters=None):
    if parameters is None:
        parameters = {}

    variable = components['variable']

    xmin, xmax = parameters.get('xmin', -10), parameters.get('xmax', 10)
    from sympy.plotting.plot import LineOver1DRangeSeries
    func = evaluator.get("input_evaluated")

    free_symbols = func.free_symbols

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

def eval_factorization(evaluator, components, parameters=None):
    number = evaluator.get("input_evaluated")

    if number == 0:
        raise ValueError("Can't factor 0")

    factors = sympy.ntheory.factorint(number, limit=100)
    smallfactors = {}
    for factor in factors:
        if factor <= 100:
            smallfactors[factor] = factors[factor]
    return smallfactors

def eval_factorization_diagram(evaluator, components, parameters=None):
    # Raises ValueError (stops card from appearing) if the factors are too
    # large so that the diagram will look nice
    number = int(evaluator.eval("input_evaluated"))
    if number > 256:
        raise ValueError("Number too large")
    elif number == 0:
        raise ValueError("Can't factor 0")
    factors = sympy.ntheory.factorint(number, limit=101)
    smallfactors = {}
    for factor in factors:
        if factor <= 256:
            smallfactors[factor] = factors[factor]
        else:
            raise ValueError("Number too large")
    return smallfactors

def eval_integral(evaluator, components, parameters=None):
    return sympy.integrate(components['integrand'], *components['limits'])

def eval_integral_manual(evaluator, components, parameters=None):
    return sympy.integrals.manualintegrate(components['integrand'],
                                           components['variable'])

def eval_diffsteps(evaluator, components, parameters=None):
    function = components.get('function', evaluator.get('input_evaluated'))

    return diffsteps.print_html_steps(function,
                                      components['variable'])

def eval_intsteps(evaluator, components, parameters=None):
    integrand = components.get('integrand', evaluator.get('input_evaluated'))

    return intsteps.print_html_steps(integrand, components['variable'])

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

def eval_function_docs(evaluator, components, parameters=None):
    docstring = trim(evaluator.get("input_evaluated").__doc__)
    return docutils.core.publish_parts(docstring, writer_name='html4css1',
                                       settings_overrides={'_disable_config': True})['html_body']

def eval_approximator(evaluator, components, parameters=None):
    if parameters is None:
        raise ValueError
    digits = parameters.get('digits', 10)
    return (evaluator.get('input_evaluated'), digits)

# Result cards

no_pre_output = lambda *args: ""

all_cards = {
    'roots': ResultCard(
        "Roots",
        "solve(%s, {_var})",
        lambda statement, var, *args: var,
        format_output_function=format_list),

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

    'integral_manual': ResultCard(
        "Integral",
        "sympy.integrals.manualintegrate(%s, {_var})",
        sympy.Integral),

    'integral_manual_fake': FakeResultCard(
        "Integral",
        "sympy.integrals.manualintegrate(%s, {_var})",
        lambda i, var: sympy.Integral(i, *var),
        eval_method=eval_integral_manual,
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
        parameters=['digits']),

    'fractional_approximation': ResultCard(
        "Fractional approximation",
        "nsimplify(%s)",
        no_pre_output),

    'absolute_value': ResultCard(
        "Absolute value",
        "Abs(%s)",
        lambda s, *args: sympy.Abs(s, evaluate=False)),

    'polar_angle': ResultCard(
        "Angle in the complex plane",
        "atan2(*(%s).as_real_imag()).evalf()",
        lambda s, *args: sympy.atan2(*s.as_real_imag())),

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

    'root_to_polynomial': ResultCard(
        "Polynomial with this root",
        "minpoly(%s)",
        no_pre_output
    ),

    'matrix_inverse': ResultCard(
        "Inverse of matrix",
        "(%s).inv()",
        lambda statement, var, *args: sympy.Pow(statement, -1, evaluate=False)
    ),

    'matrix_eigenvals': ResultCard(
        "Eigenvalues",
        "(%s).eigenvals()",
        no_pre_output,
        format_output_function=format_dict_title("Eigenvalue", "Multiplicity")
    ),

    'matrix_eigenvectors': ResultCard(
        "Eigenvectors",
        "(%s).eigenvects()",
        no_pre_output,
        format_output_function=format_list
    ),

    'approximator': FakeResultCard(
        "Approximator_NOT_USER_VISIBLE",
        "%s",
        no_pre_output,
        eval_method=eval_approximator,
        format_output_function=format_approximator
    ),
}

def get_card(name):
    return all_cards.get(name, None)

all_cards['trig_alternate'] = MultiResultCard(
    "Alternate forms",
    get_card('trigexpand'),
    get_card('trigsimp'),
    get_card('trigsincos'),
    get_card('trigexp')
)

all_cards['integral_alternate'] = MultiResultCard(
    "Antiderivative forms",
    get_card('integral'),
    get_card('integral_manual')
)

all_cards['integral_alternate_fake'] = MultiResultCard(
    "Antiderivative forms",
    get_card('integral_fake'),
    get_card('integral_manual_fake')
)

result_sets = [
    ('integrate', extract_integral, ['integral_alternate_fake', 'intsteps']),
    ('diff', extract_derivative, ['diff', 'diffsteps']),
    ('factorint', extract_first, ['factorization', 'factorizationDiagram']),
    ('plot', extract_plot, ['graph']),
    (is_integer, None, ['digits', 'factorization', 'factorizationDiagram']),
    (is_complex, None, ['absolute_value', 'polar_angle', 'conjugate']),
    (is_rational, None, ['float_approximation']),
    (is_float, None, ['fractional_approximation']),
    (is_approximatable_constant, None, ['root_to_polynomial']),
    (is_uncalled_function, None, ['function_docs']),
    (is_trig, None, ['trig_alternate']),
    (is_matrix, None, ['matrix_inverse', 'matrix_eigenvals', 'matrix_eigenvectors']),
    (is_not_constant_basic, None, ['graph', 'roots', 'diff', 'integral_alternate', 'series'])
]

def is_function_handled(function_name):
    """Do any of the result sets handle this specific function?"""
    return any(name == function_name for (name, _, _) in result_sets)

def find_result_set(function_name, input_evaluated):
    """
    Finds a set of result cards based on function name and evaluated input.

    Returns:

    - Function that parses the evaluated input into components. For instance,
      for an integral this would extract the integrand and limits of integration.
      This function will always extract the variables.
    - List of result cards.
    - Flag indicating whether the result cards 'handle' the function call. For
      instance, 'simplify(x)' will generate a 'Result' card to show the result.
      But for 'factorint(123)', since one of the result cards already shows the
      result, this is unnecessary.
    """
    result = []
    result_converter = default_variable

    for predicate, converter, result_cards in result_sets:
        if predicate == function_name:
            if converter:
                result_converter = converter
            for card in result_cards:
                if card not in result:
                    result.append(card)
        elif callable(predicate) and predicate(input_evaluated):
            if converter:
                result_converter = converter
            for card in result_cards:
                if card not in result:
                    result.append(card)

    return result_converter, result
