import jsonrpclib

def test_add_cell():
    s = jsonrpclib.SimpleServerProxy("http://localhost:8080/json/")
    token = s.create_worksheet()
    s.add_cell(token)
    assert s.get_cell_ids(token) == [1]
    s.add_cell(token)
    assert s.get_cell_ids(token) == [1, 2]
    s.add_cell(token)
    assert s.get_cell_ids(token) == [1, 2, 3]

    s.add_cell(token, 2)
    # not implemented yet:
    #assert s.get_cell_ids(token) == [1, 4, 2, 3]
