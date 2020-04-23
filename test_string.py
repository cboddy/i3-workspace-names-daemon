import unittest

from i3_workspace_names_daemon import truncate, compress

class TestString(unittest.TestCase):

    def test_compress_dash(self):
        original = 'i3-workspace-names-daemon'
        expected = 'i3-wor-nam-dae'
        actual = compress(original)
        self.assertEqual(expected, actual)

    def test_compress_unserscore(self):
        original = 'i3_workspace_names_daemon'
        expected = 'i3_wor_nam_dae'
        actual = compress(original)
        self.assertEqual(expected, actual)

    def test_compress_mixed(self):
        original = 'i3-workspace_names_daemon'
        expected = 'i3-wor_nam_dae'
        actual = compress(original)
        self.assertEqual(expected, actual)

    def test_compress_trailing(self):
        original = 'i3-workspace-names-daemon_'
        expected = 'i3-wor-nam-dae'
        actual = compress(original)
        self.assertEqual(expected, actual)

    def test_compress_trailing_double(self):
        original = 'i3-workspace-names-daemon__'
        expected = 'i3-wor-nam-dae_'
        actual = compress(original)
        self.assertEqual(expected, actual)

    def test_compress_leading(self):
        original = '_i3-workspace-names-daemon'
        expected = 'i3-wor-nam-dae'
        actual = compress(original)
        self.assertEqual(expected, actual)

    def test_compress_short(self):
        original = 'a-b-c-d'
        expected = 'a-b-c-d'
        actual = compress(original)
        self.assertEqual(expected, actual)

    def test_compress_dash_double(self):
        original = 'i3-workspace--names-daemon'
        expected = 'i3-wor-nam-dae'
        actual = compress(original)
        self.assertEqual(expected, actual)

if __name__ == '__main__':
    unittest.main()
