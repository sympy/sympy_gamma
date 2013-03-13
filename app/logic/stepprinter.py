import sympy
from contextlib import contextmanager

from latexprinter import latex

def functionnames(numterms):
    if numterms == 2:
        return ["f", "g"]
    elif numterms == 3:
        return ["f", "g", "h"]
    else:
        return ["f_{}".format(i) for i in range(numterms)]

class Equals(sympy.Basic):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def _latex(self, printer):
        return '{} = {}'.format(latex(self.left),
                                latex(self.right))

    def __str__(self):
        return '{} = {}'.format(str(self.left), str(self.right))

class Printer(object):
    def __init__(self):
        self.lines = []
        self.level = 0

    def append(self, text):
        self.lines.append(self.level * "\t" + text)

    def finalize(self):
        return "\n".join(self.lines)

    def format_math(self, math):
        return str(math)

    def format_math_display(self, math):
        return self.format_math(math)

    @contextmanager
    def new_level(self):
        self.level += 1
        yield self.level
        self.level -= 1

    @contextmanager
    def new_step(self):
        yield self.level
        self.lines.append('\n')

class LaTeXPrinter(Printer):
    def format_math(self, math):
        return latex(math)

class HTMLPrinter(LaTeXPrinter):
    def __init__(self):
        super(HTMLPrinter, self).__init__()
        self.lines = ['<ol>']

    def format_math(self, math):
        return '<script type="math/tex; mode=inline">{}</script>'.format(
            latex(math))

    def format_math_display(self, math):
        return '<script type="math/tex; mode=display">{}</script>'.format(
            latex(math))

    @contextmanager
    def new_level(self):
        self.level += 1
        self.lines.append(self.level * '    ' + '<ol>')
        yield
        self.lines.append(self.level * '    ' + '</ol>')
        self.level -= 1

    @contextmanager
    def new_step(self):
        self.lines.append(self.level * '    ' + '<li>')
        yield self.level
        self.lines.append(self.level * '    ' + '</li>')

    @contextmanager
    def new_collapsible(self):
        self.lines.append(self.level * '    ' + '<div class="collapsible">')
        yield self.level
        self.lines.append(self.level * '    ' + '</div>')

    def append(self, text):
        self.lines.append((self.level + 1) * '    ' + '<p>{}</p>'.format(text))

    def append_header(self, text):
        self.lines.append((self.level + 1) * '    ' + '<h2>{}</h2>'.format(text))
