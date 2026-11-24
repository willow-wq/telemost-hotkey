import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from telemost_hotkey import configured_key, is_mic_label


class MatchingTests(unittest.TestCase):
    def test_key_config_and_cli_precedence(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            self.assertEqual(configured_key(None, path), 'Shift_R')
            path.write_text('{"hotkey":"F8"}', encoding='utf-8')
            self.assertEqual(configured_key(None, path), 'F8')
            self.assertEqual(configured_key('F9', path), 'F9')
            path.write_text('{"hotkey":12}', encoding='utf-8')
            with self.assertRaises(ValueError):
                configured_key(None, path)

    def test_explicit_labels(self):
        for label in ('Выключить микрофон', ' Включить   микрофон ', 'Unmute microphone'):
            self.assertTrue(is_mic_label(label))

    def test_unrelated_controls(self):
        for label in ('Микрофон', 'Microphone settings', 'Выключить камеру', ''):
            self.assertFalse(is_mic_label(label))

if __name__ == '__main__':
    unittest.main()
