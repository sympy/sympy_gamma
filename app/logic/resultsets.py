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

    def format_input(self, input_repr):
        if 'format_input_function' in self.card_info:
            return self.card_info['format_input_function'](input_repr)
        return input_repr

    def format_output(self, output, formatter):
        if 'format_output_function' in self.card_info:
            return self.card_info['format_output_function'](output, formatter)
        return formatter(output)


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

def is_complex(input_evaluated):
    try:
        return sympy.I in input_evaluated.atoms()
    except AttributeError:
        return False

def is_trig(input_evaluated):
    try:
        if any(input_evaluated.find(func) for func in (sympy.sin, sympy.cos,
                                                       sympy.tan, sympy.csc,
                                                       sympy.sec,
                                                       sympy.cot)):
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


# Result cards

no_pre_output = lambda *args: ""

roots = ResultCard("Roots", "solve(%s, {_var})",
                   lambda statement, var, *args: var)
integral = ResultCard("Integral", "integrate(%s, {_var})", sympy.Integral)
diff = ResultCard("Derivative", "diff(%s, {_var})", sympy.Derivative)
series = ResultCard("Series expansion around 0", "series(%s, {_var}, 0, 10)",
                    no_pre_output)
digits = ResultCard("Digits in base-10 expansion of number", "len(str(%s))",
                    no_pre_output,
                    format_input_function=format_long_integer)
factorization = ResultCard("Factors less than 100",
                           "sympy.ntheory.factorint(%s, limit=100)",
                           no_pre_output,
                           format_input_function=format_long_integer,
                           format_output_function=format_dict_title("Factor",
                                                                    "Times"))
float_approximation = ResultCard("Floating-point approximation",
                                 "%s.evalf()", no_pre_output)
fractional_approximation = ResultCard("Fractional approximation",
                                      "nsimplify(%s)", no_pre_output)
absolute_value = ResultCard("Absolute value", "Abs(%s)",
                            lambda s, *args: "|{}|".format(s))
polar_angle = ResultCard("Angle in the complex plane",
                         "atan2(*(%s).as_real_imag()).evalf()",
                         lambda s, *args:
                         sympy.atan2(*sympy.sympify(s).as_real_imag()))
conjugate = ResultCard("Complex conjugate", "conjugate(%s)",
                       lambda s, *args: sympy.conjugate(s))
trigexpand = ResultCard("Alternate form", "(%s).expand(trig=True)",
                        lambda s, *args: s)


result_sets = [
    (is_integral, extract_integrand, [integral]),
    (is_integer, default_variable,
     [digits, float_approximation, factorization]),
    (is_rational, default_variable, [float_approximation]),
    (is_float, default_variable, [fractional_approximation]),
    (is_numbersymbol, default_variable, [float_approximation]),
    (is_complex, default_variable, [absolute_value, polar_angle,
                                    conjugate]),
    (is_trig, do_nothing, [trigexpand]),
    (lambda x: True, do_nothing, [roots, diff, integral, series])
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