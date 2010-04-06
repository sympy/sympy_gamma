import jsonrpclib

def test_add_cell():
    s = jsonrpclib.SimpleServerProxy("http://localhost:8080/json/")
    token = s.create_worksheet()
    s.add_cell(token)
    print s.print_worksheet(token)
    s.add_cell(token, 5)
    print s.print_worksheet(token)
