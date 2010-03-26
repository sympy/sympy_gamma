import jsonrpclib

def test_jsonrpc1():
    s = jsonrpclib.ServerProxy("http://localhost:8080/test-service/")
    assert s.echo("Foo bar")["result"] == "Foo bar"
    assert s.echo(1)["result"] == 1
    assert s.echo(2)["result"]+3 == 5
    assert s.echo(1)["result"] != "1"
    assert s.reverse("Foo bar")["result"] == "rab ooF"
    assert s.uppercase("Foo bar")["result"] == "FOO BAR"
    assert s.lowercase("Foo bar")["result"] == "foo bar"

def test_jsonrpc2():
    s = jsonrpclib.ServerProxy("http://localhost:8080/test-service/")
    assert s.add(2, 3)["result"] == 5
    assert s.add(2, 3)["result"] != "5"

    assert s.add("2", "3")["result"] == "23"
    assert s.add("2", "3")["result"] != 23
    assert s.add("2", "3")["result"] != 5

def test_eval_cell1():
    s = jsonrpclib.ServerProxy("http://localhost:8080/test-service/")
    assert s.eval_cell("2 + 3")["result"] == "5"
    code = """\
from sympy import sin, integrate, var
var("x")
integrate(sin(x), x)
"""
    assert s.eval_cell(code)["result"] == "-cos(x)"
    assert s.eval_cell(code)["result"] != "cos(x)"

def test_eval_cell2():
    s = jsonrpclib.ServerProxy("http://localhost:8080/test-service/")
    assert s.eval_cell("a = 2")["result"] == ""
    assert s.eval_cell("a + 3")["result"] == "5"
