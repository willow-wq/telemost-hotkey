import json
from pathlib import Path
import tempfile
import unittest

from hotkey_settings import KEYS, load_key, save_key


class SettingsTests(unittest.TestCase):
    def test_missing_invalid_and_corrupt_settings_use_default(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            self.assertEqual(load_key(path), 'RightShift')
            for contents in ('{', '[]', '{"hotkey": []}', '{"hotkey": "Unknown"}'):
                path.write_text(contents, encoding='utf-8')
                self.assertEqual(load_key(path), 'RightShift')

    def test_save_load_and_replace_existing_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings' / 'config.json'
            save_key(path, 'F8')
            self.assertEqual(load_key(path), 'F8')
            self.assertEqual(KEYS[load_key(path)], 0x77)
            save_key(path, 'RightShift')
            self.assertEqual(json.loads(path.read_text())['hotkey'], 'RightShift')
            self.assertFalse(path.with_suffix('.tmp').exists())
            with self.assertRaises(ValueError):
                save_key(path, 'Unknown')


if __name__ == '__main__':
    unittest.main()
