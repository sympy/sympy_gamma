import pyjd # this is dummy in pyjs.
from pyjamas.ui.RootPanel import RootPanel
from pyjamas.ui.Button import Button
from pyjamas.ui.HTML import HTML
from pyjamas.ui.Label import Label
from pyjamas.ui.TextArea import TextArea
from pyjamas.ui import KeyboardListener, Event
from pyjamas.HTTPRequest import HTTPRequest
from pyjamas import DOM
from pyjamas import Window

from pyjamas.JSONParser import JSONParser

def greet(fred):
    print "greet button"
    Window.alert("Hello, AJAX!")

class InputArea(TextArea):

    def __init__(self, worksheet, cell_id, **kwargs):
        TextArea.__init__(self, **kwargs)
        self._worksheet = worksheet
        self._cell_id = cell_id
        self.addKeyboardListener(self)
        #self.addClickListener(self)
        self.addFocusListener(self)
        self.set_rows(1)
        self.setCharacterWidth(80)

    #def onClick(self, sender):
    #    pass

    def onFocus(self, sender):
        #print "focus", self._cell_id
        self._worksheet.set_active_cell(self._cell_id)

    def onLostFocus(self, sender):
        #print "lost-focus", self._cell_id
        pass

    def rows(self):
        return self.getVisibleLines()

    def set_rows(self, rows):
        if rows == 0:
            rows = 1
        self.setVisibleLines(rows)

    def cols(self):
        return self.getCharacterWidth()

    def occupied_rows(self):
        text = self.getText()
        lines = text.split("\n")
        return len(lines)

    def cursor_coordinates(self):
        """
        Returns the cursor coordinates as a tuple (x, y).

        Example:

        >>> self.cursor_coordinates()
        (2, 3)
        """
        text = self.getText()
        lines = text.split("\n")
        pos = self.getCursorPos()
        if pos == 0:
            return (0, 0)
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
        return (cursor_col, cursor_row)

    def insert_at_cursor(self, inserted_text):
        pos = self.getCursorPos()
        text = self.getText()
        text = text[:pos] + inserted_text + text[pos:]
        self.setText(text)

    def onKeyUp(self, sender, keyCode, modifiers):
        #print "on_key_up"
        x, y = self.cursor_coordinates()
        rows = self.occupied_rows()
        s = "row/col: (%s, %s), cursor pos: %d, %d, real_rows: %d" % \
                (self.rows(), self.cols(), x, y, rows)
        self.set_rows(rows)
        self._worksheet.print_info(s)

    def onKeyDown(self, sender, key_code, modifiers):
        if key_code == KeyboardListener.KEY_TAB:
            self.insert_at_cursor("    ")
            event = DOM.eventGetCurrentEvent()
            event.preventDefault()
        elif key_code == KeyboardListener.KEY_BACKSPACE:
            x, y = self.cursor_coordinates()
            if (x == 0) and (y == 0):
                return
            lines = self.getText().split("\n")
            line = lines[y]
            if line.strip() == "" and len(line) > 0:
                old_len = len(line)
                new_len = int(old_len / 4) * 4
                if old_len == new_len:
                    new_len = new_len - 4
                lines[y] = line[:new_len]
                self.setText("\n".join(lines))
                event = DOM.eventGetCurrentEvent()
                event.preventDefault()
        elif key_code == KeyboardListener.KEY_ENTER and \
                modifiers == KeyboardListener.MODIFIER_SHIFT:
            event = DOM.eventGetCurrentEvent()
            event.preventDefault()
            print "sending"
            payload = {"code": self.getText(), "time": "ok"}
            payload = JSONParser().encode(payload)
            print "payload: %s" % payload
            data = urlencode({"payload": payload})
            HTTPRequest().asyncPost("/eval_cell/", data, Loader(self))
            if self._cell_id == self._worksheet.num_cells():
                self._worksheet.add_cell()
            self._worksheet.move_to_next_cell()
        elif key_code == KeyboardListener.KEY_UP:
            x, y = self.cursor_coordinates()
            if y == 0:
                event = DOM.eventGetCurrentEvent()
                event.preventDefault()
                self._worksheet.move_to_prev_cell()
        elif key_code == KeyboardListener.KEY_DOWN:
            x, y = self.cursor_coordinates()
            if y + 1 == self.rows():
                event = DOM.eventGetCurrentEvent()
                event.preventDefault()
                self._worksheet.move_to_next_cell()

    def onKeyPress(self, sender, keyCode, modifiers):
        #print "on_key_press"
        pass

    def handle_eval_data(self, text):
        self._worksheet.show_output(self._cell_id, text)

class Loader:

    def __init__(self, cell):
        self._cell = cell

    def onCompletion(self, text):
        print "completed", text
        data = JSONParser().decode(text)
        self._cell.handle_eval_data(data["result"])
        print "ok"

    def onError(self, text, code):
        print "error", text, code

    def onTimeout(self, text):
        print "timeout", text

class InsertListener:

    def __init__(self, worksheet, id):
        self._worksheet = worksheet
        self._id = id

    def onClick(self, event):
        self._worksheet.insert_cell(self._id)

class Worksheet:

    def __init__(self):
        self._echo = HTML()
        RootPanel().add(self._echo)
        self._i = 0
        self._active_cell = -1
        self._cell_list = []
        self._other = []
        self.print_info("")

    def print_info(self, text):
        self._echo.setHTML("INFO: cells: %d, active cell: %d, " % \
                (self._i, self._active_cell) + text)

    def num_cells(self):
        return self._i

    def add_cell(self, insert_before=None):
        self._i += 1
        insert_new_cell = HTML('<div class="insert_new_cell"></div>')
        listener = InsertListener(self, self._i)
        insert_new_cell.addClickListener(listener)
        input_prompt = HTML('<span class="input_prompt">In [%d]:</span>' % \
                self._i)
        cell_input = InputArea(self, self._i, StyleName='cell_input')
        output_delimiter = HTML('<div class="output_delimiter"></div>')
        output_prompt = HTML('<span class="output_prompt">Out[%d]:</span>' % \
                self._i)
        cell_output = HTML('<span class="cell_output"></span>')
        output_prompt.setVisible(False)
        RootPanel_insert_before(insert_new_cell, insert_before)
        RootPanel_insert_before(insert_new_cell, insert_before)
        RootPanel_insert_before(input_prompt, insert_before)
        RootPanel_insert_before(cell_input, insert_before)
        RootPanel_insert_before(output_delimiter, insert_before)
        RootPanel_insert_before(output_prompt, insert_before)
        RootPanel_insert_before(cell_output, insert_before)
        self._cell_list.append(cell_input)
        self._other.append((output_prompt, cell_output))
        self.print_info("")

    def set_active_cell(self, cell_id):
        self._active_cell = cell_id
        self.print_info("")

    def move_to_prev_cell(self):
        if self._active_cell > 1:
            self._cell_list[self._active_cell-2].setFocus(True)

    def move_to_next_cell(self):
        if self._active_cell < self._i:
            self._cell_list[self._active_cell].setFocus(True)

    def insert_cell(self, id):
        cell = self._cell_list[id-1].getElement()
        first_elem = getPrevSibling(getPrevSibling(cell))
        self.add_cell(first_elem)

    def show_output(self, id, text):
        print id
        #print text
        #self.print_info(text)
        cell = self._cell_list[id-1].getElement()
        output = HTML(text)
        RootPanel_insert_before(output, cell)
        prompt, cell = self._other[id-1]
        print prompt, cell
        prompt.setVisible(True)
        cell.setHTML('<span class="cell_output">' + text + '</span>')

def getPrevSibling(elem):
    parent = DOM.getParent(elem)
    elem_index = DOM.getChildIndex(parent, elem)
    children = list(DOM.iterChildren(parent))
    return children[elem_index - 1]

def insertChildBefore(new_elem, elem):
    """
    Inserts an element "new_elem" before the element "elem".
    """
    parent = DOM.getParent(elem)
    id = DOM.getChildIndex(parent, elem)
    DOM.insertChild(parent, new_elem, id)

def RootPanel_insert_before(new_elem, elem):
    if elem is None:
        RootPanel().add(new_elem)
    else:
        parent = RootPanel()
        new_elem.setParent(parent)
        insertChildBefore(new_elem.getElement(), elem)

def urlencode(d):
    return "%s=%s" % ("payload", encodeURIComponent(d["payload"]))

if __name__ == '__main__':
    pyjd.setup("templates/Hello.html")
    w = Worksheet()
    w.add_cell()
    w.move_to_next_cell()
    pyjd.run()
