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

def is_integral(input_evaluated):
    return isinstance(input_evaluated, sympy.Integral)

def is_integer(input_evaluated):
    return isinstance(input_evaluated, sympy.Integer)


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

roots = ResultCard("Roots", "solve(%s, {_var})",
                   lambda statement, var, *args: var)
integral = ResultCard("Integral", "integrate(%s, {_var})", sympy.Integral)
diff = ResultCard("Derivative", "diff(%s, {_var})", sympy.Derivative)
series = ResultCard("Series expansion around 0", "series(%s, {_var}, 0, 10)",
                    lambda *args: "")
digits = ResultCard("Digits in base-10 expansion of number", "len(str(%s))",
                    lambda *args: "",
                    format_input_function=format_long_integer)
factorization = ResultCard("Factors less than 1000",
                           "sympy.ntheory.factorint(%s, limit=1000)",
                           lambda *args: "",
                           format_input_function=format_long_integer,
                           format_output_function=format_dict_title("Factor",
                                                                    "Times"))

result_sets = [
    (is_integral, extract_integrand, [integral]),
    (is_integer, default_variable, [digits, factorization]),
    (lambda x: True, do_nothing, [roots, diff, integral, series])
]

def find_result_set(input_evaluated):
    for (predicate, convert_input, result_cards) in result_sets:
        if predicate(input_evaluated):
            return convert_input, result_cards