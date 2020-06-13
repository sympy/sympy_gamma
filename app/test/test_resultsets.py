from __future__ import absolute_import
from app.logic import resultsets
from sympy import sympify, I, sqrt


def test_predicates():
    assert not resultsets.is_approximatable_constant(sqrt(2))
    assert not resultsets.is_approximatable_constant(sympify('2'))
    assert resultsets.is_complex(2 * I + 3)
    assert not resultsets.is_complex(3)
