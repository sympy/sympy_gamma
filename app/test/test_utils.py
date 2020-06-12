from __future__ import absolute_import
from app.logic.logic import Eval


def test_eval1():
    e = Eval()
    assert e.eval("1+1") == "2"
    assert e.eval("1+1\n") == "2"
    assert e.eval("a=1+1") == ""
    assert e.eval("a=1+1\n") == ""
    assert e.eval("a=1+1\na") == "2"
    assert e.eval("a=1+1\na\n") == "2"
    assert e.eval("a=1+1\na=3") == ""
    assert e.eval("a=1+1\na=3\n") == ""


def test_eval2():
    e = Eval()
    assert e.eval("""\
def f(x):
    return x**2
f(3)
"""\
        ) == "9"
    assert e.eval("""\
def f(x):
    return x**2
f(3)
a = 5
"""\
        ) == ""
    assert e.eval("""\
def f(x):
    return x**2
if f(3) == 9:
    a = 1
else:
    a = 0
a
"""\
        ) == "1"
    assert e.eval("""\
def f(x):
    return x**2 + 1
if f(3) == 9:
    a = 1
else:
    a = 0
a
"""\
        ) == "0"


def test_eval3():
    e = Eval()
    assert e.eval("xxxx").startswith("Traceback")
    assert e.eval("""\
def f(x):
    return x**2 + 1 + y
if f(3) == 9:
    a = 1
else:
    a = 0
a
"""\
        ).startswith("Traceback")
