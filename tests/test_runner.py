"""Check portable command construction without requiring a dataset or shell."""
import unittest
from pathlib import Path
import sys
from run import phase_command


class RunnerTests(unittest.TestCase):
    def test_dataset_path_with_spaces_is_one_argument(self):
        data = str(Path('CT scans with spaces').resolve())
        command = phase_command('audit', data=data)
        self.assertEqual(command[:3], [sys.executable, '-m', 'src.io_chaos'])
        self.assertEqual(command[-2:], ['--data', data])

    def test_visualization_archive_is_explicit(self):
        self.assertIn('--no-archive', phase_command('visualization'))
        self.assertNotIn('--no-archive', phase_command('visualization', archive=True))
