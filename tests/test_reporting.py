"""Verify report output when the system defaults to a legacy Windows encoding."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.reporting import save_summary


class ReportingTests(unittest.TestCase):
    def test_summary_preserves_lithuanian_text_with_cp1251_default(self):
        original_open = Path.open

        def windows_open(path, mode='r', buffering=-1, encoding=None,
                         errors=None, newline=None):
            # Simulate a Windows locale only when no explicit encoding is used.
            if encoding in (None, 'locale'):
                encoding = 'cp1251'
            return original_open(path, mode, buffering, encoding, errors, newline)

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch.object(Path, 'open', windows_open):
                save_summary([], 0.0075, (-0.01, 0.02), 0.0, output)
            text = (output / 'RESULTS.md').read_bytes().decode('utf-8')
            self.assertIn('Hipotezė AP skirtumas ≥ 0,02', text)
            self.assertIn('Automatiškai sukurta', text)
            self.assertIn('nepasitvirtino šiame teste', text)


if __name__ == '__main__':
    unittest.main()
