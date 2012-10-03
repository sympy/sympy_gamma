import json
import sympy
from operator import itemgetter


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

    def eval(self, evaluator, variable):
        line = self.result_statement.format(_var=variable) % 'input_evaluated'
        return sympy.sympify(evaluator.eval(line, use_none_for_exceptions=True))

    def format_input(self, input_repr, variable):
        line = self.result_statement.format(_var=variable)
        if 'format_input_function' in self.card_info:
            return line % self.card_info['format_input_function'](input_repr)
        return line % input_repr

    def format_output(self, output, formatter):
        if 'format_output_function' in self.card_info:
            return self.card_info['format_output_function'](output, formatter)
        return formatter(output)


class FakeResultCard(ResultCard):
    """ResultCard whose displayed expression != actual code.

    Used when creating the result to be displayed involves code that a user
    would not normally need to do, e.g. calculating plot points (where a
    user would simply use ``plot``)."""

    def __init__(self, *args, **kwargs):
        super(FakeResultCard, self).__init__(*args, **kwargs)
        assert 'eval_method' in kwargs

    def eval(self, evaluator, variable):
        return self.card_info['eval_method'](evaluator, variable)


class MultiResultCard(ResultCard):
    """Tries multiple statements and displays the first that works."""

    def __init__(self, title, *cards):
        super(MultiResultCard, self).__init__(title, '', lambda *args: '')
        self.cards = cards
        self.cards_used = []

    def eval(self, evaluator, variable):
        self.cards_used = []
        original = sympy.sympify(evaluator.eval("input_evaluated"))
        results = []
        for card in self.cards:
            result = card.eval(evaluator, variable)
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


# Functions to convert input and extract variable used

def extract_integrand(input_evaluated, variable):
    assert isinstance(input_evaluated, sympy.Integral)
    if len(input_evaluated.limits[0]) > 1:  # if there are limits]
        variable = input_evaluated.limits[0]
    elif len(input_evaluated.variables) == 1:
        variable = input_evaluated.variables[0]
    return input_evaluated.function, variable

def do_nothing(input_evaluated, variable):
    return input_evaluated, variable

def default_variable(input_evaluated, variable):
    return input_evaluated, sympy.Symbol('x')


# Formatting functions

def format_long_integer(integer):
    intstr = str(integer)
    if len(intstr) > 100:
        # \xe2 is Unicode ellipsis
        return intstr[:20] + "..." + intstr[len(intstr) - 21:]
    return intstr

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

def eval_graph(evaluator, variable):
    from sympy.plotting.plot import LineOver1DRangeSeries
    func = evaluator.eval("input_evaluated")
    series = LineOver1DRangeSeries(func, (variable, -10, 10), nb_of_points=200)
    series = series.get_points()
    return {
        'function': sympy.jscode(sympy.sympify(func)),
        'variable': repr(variable),
        'xvalues': json.dumps(series[0].tolist()),
        'yvalues': json.dumps(series[1].tolist())
    }

def eval_factorization(evaluator, variable):
    number = evaluator.eval("input_evaluated")
    factors = sympy.ntheory.factorint(number, limit=100)
    smallfactors = {}
    for factor in factors:
        if factor <= 100:
            smallfactors[factor] = factors[factor]
    return smallfactors

# Result cards

no_pre_output = lambda *args: ""

roots = ResultCard(
    "Roots",
    "solve(%s, {_var})",
    lambda statement, var, *args: var)

integral = ResultCard(
    "Integral",
    "integrate(%s, {_var})",
    sympy.Integral)

diff = ResultCard("Derivative",
    "diff(%s, {_var})",
    sympy.Derivative)

series = ResultCard(
    "Series expansion around 0",
    "series(%s, {_var}, 0, 10)",
    no_pre_output)

digits = ResultCard(
    "Digits in base-10 expansion of number",
    "len(str(%s))",
    no_pre_output,
    format_input_function=format_long_integer)

factorization = FakeResultCard(
    "Factors less than 100",
    "factorint(%s, limit=100)",
    no_pre_output,
    format_input_function=format_long_integer,
    format_output_function=format_dict_title("Factor", "Times"),
    eval_method=eval_factorization)

float_approximation = ResultCard(
    "Floating-point approximation",
    "(%s).evalf()",
    no_pre_output)

fractional_approximation = ResultCard(
    "Fractional approximation",
    "nsimplify(%s)",
    no_pre_output)

absolute_value = ResultCard(
    "Absolute value",
    "Abs(%s)",
    lambda s, *args: "|{}|".format(s))

polar_angle = ResultCard(
    "Angle in the complex plane",
    "atan2(*(%s).as_real_imag()).evalf()",
    lambda s, *args: sympy.atan2(*sympy.sympify(s).as_real_imag()))

conjugate = ResultCard(
    "Complex conjugate",
    "conjugate(%s)",
    lambda s, *args: sympy.conjugate(s))

trigexpand = ResultCard(
    "Alternate form",
    "(%s).expand(trig=True)",
    lambda statement, var, *args: statement)

trigsimp = ResultCard(
    "Alternate form",
    "trigsimp(%s)",
    lambda statement, var, *args: statement)

trigsincos = ResultCard(
    "Alternate form",
    "(%s).rewrite(csc, sin, sec, cos, cot, tan)",
    lambda statement, var, *args: statement
)


trigexp = ResultCard(
    "Alternate form",
    "(%s).rewrite(sin, exp, cos, exp, tan, exp)",
    lambda statement, var, *args: statement
)

trig_alternate = MultiResultCard(
    "Alternate form",
    trigexpand,
    trigsimp,
    trigsincos,
    trigexp
)

graph = FakeResultCard(
    "Graph",
    "plot(%s)",
    no_pre_output,
    format_output_function=format_graph,
    eval_method=eval_graph)


result_sets = [
    (is_integral, extract_integrand, [integral]),
    (is_integer, default_variable,
     [digits, float_approximation, factorization]),
    (is_rational, default_variable, [float_approximation]),
    (is_float, default_variable, [fractional_approximation]),
    (is_numbersymbol, default_variable, [float_approximation]),
    (is_constant, default_variable, [float_approximation]),
    (is_complex, default_variable, [absolute_value, polar_angle,
                                    conjugate]),
    (is_trig, do_nothing, [trig_alternate]),
    (lambda x: True, do_nothing, [graph, roots, diff, integral, series])
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
