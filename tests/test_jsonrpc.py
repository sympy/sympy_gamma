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
