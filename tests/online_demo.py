import jsonrpclib

#base_address = "http://localhost:8080"
base_address = "http://2.latest.sympy-gamma.appspot.com"

s = jsonrpclib.SimpleServerProxy(base_address + "/test-service/")
print s.add(2, 3)
print s.add("2", "3")
print s.eval_cell("2+3")
print s.eval_cell("""\
from sympy import sin, integrate, var
var("x")
integrate(sin(x), x)
""")
assert s.add(2, 3) == 5
assert s.add("2", "3") == "23"

