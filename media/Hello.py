import pyjd # this is dummy in pyjs.
from pyjamas.ui.RootPanel import RootPanel
from pyjamas.ui.Button import Button
from pyjamas.ui.HTML import HTML
from pyjamas.ui.Label import Label
from pyjamas import Window
from pyjamas.ui.TextArea import TextArea

def greet(fred):
    print "greet button"
    Window.alert("Hello, AJAX!")

class InputArea(TextArea):

    def __init__(self, echo):
        TextArea.__init__(self)
        self.echo = echo
        self.addKeyboardListener(self)
        self.addClickListener(self)
        self.setVisibleLines(4)
        self.setCharacterWidth(80)

    def onClick(self, sender):
        print "on_click"

    def rows(self):
        return self.getVisibleLines()

    def cols(self):
        return self.getCharacterWidth()

    def cursor_coordinates(self):
        text = self.getText()
        lines = text.split("\n")
        pos = self.getCursorPos()
        i = 0
        cursor_row = -1
        cursor_col = -1
        #print "--------" + "start"
        for row, line in enumerate(lines):
            i += len(line) + 1  # we need to include "\n"
        #    print len(line), i, pos, line
            if pos < i:
                cursor_row = row
                cursor_col = pos - i + len(line) + 1
                break
        #print "--------"
        return (cursor_row, cursor_col)

    def onKeyUp(self, sender, keyCode, modifiers):
        #print "on_key_up"
        s = "row/col: (%s, %s), cursor pos: %s" % \
                (self.rows(), self.cols(), self.cursor_coordinates())
        self.echo.setHTML("Info:" + s)

    def onKeyDown(self, sender, keyCode, modifiers):
        #print "on_key_down"
        pass

    def onKeyPress(self, sender, keyCode, modifiers):
        #print "on_key_press"
        pass


if __name__ == '__main__':
    pyjd.setup("../templates/Hello.html")
    b = Button("Click me", greet, StyleName='teststyle')
    h = HTML("<b>Hello World</b> (html)", StyleName='teststyle')
    l = Label("Hello World (label)", StyleName='teststyle')
    echo = HTML()
    t = InputArea(echo)
    RootPanel().add(b)
    RootPanel().add(h)
    RootPanel().add(l)
    RootPanel().add(t)
    RootPanel().add(echo)
    pyjd.run()
