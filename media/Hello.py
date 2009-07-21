import pyjd # this is dummy in pyjs.
from pyjamas.ui.RootPanel import RootPanel
from pyjamas.ui.Button import Button
from pyjamas.ui.HTML import HTML
from pyjamas.ui.Label import Label
from pyjamas import Window

def greet(fred):
    print "greet button"
    Window.alert("Hello, AJAX!")

if __name__ == '__main__':
    pyjd.setup("../templates/Hello.html")
    b = Button("Click me", greet, StyleName='teststyle')
    h = HTML("<b>Hello World</b> (html)", StyleName='teststyle')
    l = Label("Hello World (label)", StyleName='teststyle')
    RootPanel().add(b)
    RootPanel().add(h)
    RootPanel().add(l)
    pyjd.run()
