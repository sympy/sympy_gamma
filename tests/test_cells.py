import jsonrpclib

def test_add_cell():
    s = jsonrpclib.SimpleServerProxy("http://localhost:8080/test-service/")
    print s.add_cell()
    print s.add_cell(5)
