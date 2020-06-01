LIVE_URL = '<a href="https://live.sympy.org">SymPy Live</a>'

LIVE_PROMOTION_MESSAGES = [
    'Need more control? Try ' + LIVE_URL + '.',
    'Want a full Python shell? Use ' + LIVE_URL + '.',
    'Experiment with SymPy at ' + LIVE_URL + '.',
    'Want to compute something more complicated?' +
    ' Try a full Python/SymPy console at ' + LIVE_URL + '.'
]

EXAMPLES = [
    ('Arithmetic', [
        ['Fractions', [('Simplify fractions', '242/33'),
                       ('Rationalize repeating decimals', '0.[123]')]],
        ['Approximations', ['pi', 'E', 'exp(pi)']],
    ]),
    ('Algebra', [
        [None, ['x', '(x+2)/((x+3)(x-4))', 'simplify((x**2 - 4)/((x+3)(x-2)))']],
        ['Polynomial and Rational Functions', [
            ('Polynomial division', 'div(x**2 - 4 + x, x-2)'),
            ('Greatest common divisor', 'gcd(2*x**2 + 6*x, 12*x)'),
            ('&hellip;and least common multiple', 'lcm(2*x**2 + 6*x, 12*x)'),
            ('Factorization', 'factor(x**4/2 + 5*x**3/12 - x**2/3)'),
            ('Multivariate factorization', 'factor(x**2 + 4*x*y + 4*y**2)'),
            ('Symbolic roots', 'solve(x**2 + 4*x*y + 4*y**2)'),
            'solve(x**2 + 4*x*y + 4*y**2, y)',
            ('Complex roots', 'solve(x**2 + 4*x + 181, x)'),
            ('Irrational roots', 'solve(x**3 + 4*x + 181, x)'),
            ('Systems of equations', 'solve_poly_system([y**2 - x**3 + 1, y*x], x, y)'),
        ]],
    ]),
    ('Trigonometry', [
        [None, ['sin(2x)', 'tan(1 + x)']],
    ]),
    ('Calculus', [
        ['Limits', ['limit(tan(x), x, pi/2)', 'limit(tan(x), x, pi/2, dir="-")']],
        ['Derivatives', [
            ('Derive the product rule', 'diff(f(x)*g(x)*h(x))'),
            ('&hellip;as well as the quotient rule', 'diff(f(x)/g(x))'),
            ('Get steps for derivatives', 'diff((sin(x) * x^2) / (1 + tan(cot(x))))'),
            ('Multiple ways to derive functions', 'diff(cot(xy), y)'),
            ('Implicit derivatives, too', 'diff(y(x)^2 - 5sin(x), x)'),
        ]],
        ['Integrals', [
            'integrate(tan(x))',
            ('Multiple variables', 'integrate(2*x + y, y)'),
            ('Limits of integration', 'integrate(2*x + y, (x, 1, 3))'),
            'integrate(2*x + y, (x, 1, 3), (y, 2, 4))',
            ('Improper integrals', 'integrate(tan(x), (x, 0, pi/2))'),
            ('Exact answers', 'integrate(1/(x**2 + 1), (x, 0, oo))'),
            ('Get steps for integrals', 'integrate(exp(x) / (1 + exp(2x)))'),
            'integrate(1 /((x+1)(x+3)(x+5)))',
            'integrate((2x+3)**7)'
        ]],
        ['Series', [
            'series(sin(x), x, pi/2)',
        ]],
    ]),
    ('Number Theory', [
        [None, [
            '1006!',
            'factorint(12321)',
            ('Calculate the 42<sup>nd</sup> prime', 'prime(42)'),
            (r'Calculate \( \varphi(x) \), the Euler totient function', 'totient(42)'),
            'isprime(12321)',
            ('First prime greater than 42', 'nextprime(42)'),
        ]],
        ['Diophantine Equations', [
            'diophantine(x**2 - 4*x*y + 8*y**2 - 3*x + 7*y - 5)',
            'diophantine(2*x + 3*y - 5)',
            'diophantine(3*x**2 + 4*y**2 - 5*z**2 + 4*x*y - 7*y*z + 7*z*x)'
        ]]
    ]),
    ('Discrete Mathematics', [
        ['Boolean Logic', [
            '(x | y) & (x | ~y) & (~x | y)',
            'x & ~x'
        ]],
        ['Recurrences', [
            ('Solve a recurrence relation', 'rsolve(y(n+2)-y(n+1)-y(n), y(n))'),
            ('Specify initial conditions', 'rsolve(y(n+2)-y(n+1)-y(n), y(n), {y(0): 0, y(1): 1})')
        ]],
        ['Summation', [
            'Sum(k,(k,1,m))',
            'Sum(x**k,(k,0,oo))',
            'Product(k**2,(k,1,m))',
            'summation(1/2**i, (i, 0, oo))',
            'product(i, (i, 1, k), (k, 1, n))'
        ]]
    ]),
    ('Plotting', [
        [None, ['plot(sin(x) + cos(2x))',
                ('Multiple plots', 'plot([x, x^2, x^3, x^4])'),
                ('Polar plots', 'plot(r=1-sin(theta))'),
                ('Parametric plots', 'plot(x=cos(t), y=sin(t))'),
                ('Multiple plot types', 'plot(y=x,y1=x^2,r=cos(theta),r1=sin(theta))')]],
    ]),
    ('Miscellaneous', [
        [None, [('Documentation for functions', 'factorial2'),
                'sympify',
                'bernoulli']],
    ]),
]
