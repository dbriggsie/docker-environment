from asyncio import Future

from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.layout.containers import (
    HSplit,
)
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import (
    Button,
    Dialog,
    Label,
)


class MessageDialog:
    def __init__(self, title, text, kb=KeyBindings()):
        self.future = Future()

        @kb.add('escape')
        def set_done(event=''):
            self.future.set_result(None)

        ok_button = Button(text="OK", handler=(lambda: set_done()))

        self.dialog = Dialog(
            title=title,
            body=HSplit([Label(text=text),]),
            buttons=[ok_button],
            width=D(preferred=80),
            modal=True,
        )

    def __pt_container__(self):
        return self.dialog
