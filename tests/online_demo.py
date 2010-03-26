import jsonrpclib

#base_address = "http://localhost:8080"
base_address = "http://2.latest.sympy-gamma.appspot.com"

s = jsonrpclib.ServerProxy(base_address + "/test-service/")
print s.add(2, 3)
print s.add("2", "3")
assert s.add(2, 3)["result"] == 5
assert s.add("2", "3")["result"] == "23"

