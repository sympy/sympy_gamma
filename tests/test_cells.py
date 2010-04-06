import jsonrpclib

def test_add_cell():
    s = jsonrpclib.SimpleServerProxy("http://localhost:8080/json/")
    print s.add_cell()
    print s.add_cell(5)
