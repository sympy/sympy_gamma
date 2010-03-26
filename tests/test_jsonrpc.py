import jsonrpclib

def test_jsonrpc1():
    s = jsonrpclib.SimpleServerProxy("http://localhost:8080/test-service/")
    assert s.echo("Foo bar") == "Foo bar"
    assert s.echo(1) == 1
    assert s.echo(2) + 3 == 5
    assert s.echo(1) != "1"
    assert s.reverse("Foo bar") == "rab ooF"
    assert s.uppercase("Foo bar") == "FOO BAR"
    assert s.lowercase("Foo bar") == "foo bar"

def test_jsonrpc2():
    s = jsonrpclib.SimpleServerProxy("http://localhost:8080/test-service/")
    assert s.add(2, 3) == 5
    assert s.add(2, 3) != "5"

    assert s.add("2", "3") == "23"
    assert s.add("2", "3") != 23
    assert s.add("2", "3") != 5

def test_eval_cell1():
    s = jsonrpclib.SimpleServerProxy("http://localhost:8080/test-service/")
    assert s.eval_cell("2 + 3") == "5"
    code = """\
from sympy import sin, integrate, var
var("x")
integrate(sin(x), x)
"""
    assert s.eval_cell(code) == "-cos(x)"
    assert s.eval_cell(code) != "cos(x)"

def test_eval_cell2():
    s = jsonrpclib.SimpleServerProxy("http://localhost:8080/test-service/")
    assert s.eval_cell("a = 2") == ""
    assert s.eval_cell("a + 3") == "5"
