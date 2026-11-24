"""Exercise hotkey decisions without installing a Windows keyboard hook."""
import ast
import ctypes as c
from ctypes import wintypes as w
from pathlib import Path
import unittest
from unittest.mock import Mock


def load_functions(user):
    tree = ast.parse(Path(__file__).with_name('telemost_hotkey.pyw').read_text(encoding='utf-8'))
    nodes = [node for node in tree.body
             if isinstance(node, (ast.ClassDef, ast.FunctionDef))
             and node.name in ('KBD', 'call_usable', 'hook')]
    for node in nodes:
        if isinstance(node, ast.FunctionDef):
            node.decorator_list = []
    namespace = dict(c=c, w=w, u=user, logging=Mock(), pressed=False,
                     bound_window=None, cached_call=123, thread_id=7)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<hotkey tests>', 'exec'), namespace)
    return namespace


class HotkeyTests(unittest.TestCase):
    def setUp(self):
        self.user = Mock()
        self.user.GetAsyncKeyState.return_value = 0
        self.user.CallNextHookEx.return_value = 42
        self.user.PostThreadMessageW.return_value = True
        self.ns = load_functions(self.user)

    def key(self, message, vk=0xA1):
        event = self.ns['KBD']()
        event.vkCode = vk
        return self.ns['hook'](0, message, c.addressof(event))

    def test_press_repeat_release(self):
        self.assertEqual(self.key(0x100), 1)
        self.assertEqual(self.key(0x100), 1)
        self.user.PostThreadMessageW.assert_called_once_with(7, 0x8001, 123, 0)
        self.assertEqual(self.key(0x101), 1)
        self.assertFalse(self.ns['pressed'])
        self.assertIsNone(self.ns['bound_window'])

    def test_no_call_passes_shift_through(self):
        self.ns['cached_call'] = None
        self.assertEqual(self.key(0x100), 42)
        self.assertEqual(self.key(0x101), 42)
        self.user.PostThreadMessageW.assert_not_called()

    def test_modifier_and_other_keys_pass_through(self):
        self.user.GetAsyncKeyState.return_value = 0x8000
        self.assertEqual(self.key(0x100), 42)
        self.assertEqual(self.key(0x101), 42)
        self.assertEqual(self.key(0x100, 0x41), 42)
        self.user.PostThreadMessageW.assert_not_called()

    def test_queue_failure_does_not_swallow_shift(self):
        self.user.PostThreadMessageW.return_value = False
        self.assertEqual(self.key(0x100), 42)
        self.assertEqual(self.key(0x101), 42)

    def test_geometry_and_dpi_gate(self):
        def rect(width, height):
            def get_rect(hwnd, pointer):
                value = c.cast(pointer, c.POINTER(w.RECT)).contents
                value.right, value.bottom = width, height
                return True
            self.user.GetClientRect.side_effect = get_rect
        self.user.GetDpiForWindow.return_value = 96
        rect(800, 450)
        self.assertTrue(self.ns['call_usable'](123))
        rect(799, 450)
        self.assertFalse(self.ns['call_usable'](123))
        rect(800, 449)
        self.assertFalse(self.ns['call_usable'](123))
        rect(1000, 700)
        self.user.GetDpiForWindow.return_value = 144
        self.assertFalse(self.ns['call_usable'](123))
        self.user.GetDpiForWindow.return_value = 96
        self.user.GetClientRect.side_effect = None
        self.user.GetClientRect.return_value = False
        self.assertFalse(self.ns['call_usable'](123))


if __name__ == '__main__':
    unittest.main()
