import unittest

from i3_workspace_names_daemon import _validate_config, DEFAULT_APP_ICON_CONFIG

class TestValidateConfig(unittest.TestCase):

    def test_empty(self):
        config = {}
        err = _validate_config(config)
        self.assertFalse(err)

    def test_default(self):
        err = _validate_config(DEFAULT_APP_ICON_CONFIG)
        self.assertFalse(err)

    def test_invalid_icon_name(self):
        config = {
            'app1': 'does-not-exist'
        }
        err = _validate_config(config)
        self.assertTrue(err)

    def test_custom_pango_markup(self):
        config = {
            'emacs': u'<span font_desc="file-icons">\ue926</span>'
        }
        err = _validate_config(config)
        self.assertFalse(err)

    def test_empty_mapping(self):
        # this is equal to no entry in the dict
        config = {
            'app2': {}
        }
        err = _validate_config(config)
        self.assertFalse(err)

    def test_icon_mapping_explicit(self):
        config = {
            'app2': {
                'icon': 'edit'
            }
        }
        err = _validate_config(config)
        self.assertFalse(err)

    def test_icon_mapping_explicit_invalid(self):
        config = {
            'app2': {
                'icon': 'does-not-exist'
            }
        }
        err = _validate_config(config)
        self.assertTrue(err)

    def test_mapping_ignore_extra_attributes(self):
        config = {
            'app2': {
                'icon': 'edit',
                'abc': 'def',
                '123': '098'
            }
        }
        err = _validate_config(config)
        self.assertFalse(err)

    def test_mapping_transform_title(self):
        config = {
            'appbla': {
                'transform_title': {
                    'from': ':(.*)',
                    'to': r'pj: \1',
                }
            }
        }
        err = _validate_config(config)
        self.assertFalse(err)

    def test_mapping_transform_title_missing_from(self):
        config = {
            'appbla': {
                'transform_title': {
                    'to': r'pj: \1',
                }
            }
        }
        err = _validate_config(config)
        self.assertTrue(err)

    def test_mapping_transform_title_missing_to(self):
        config = {
            'appbla': {
                'transform_title': {
                    'from': ':(.*)',
                }
            }
        }
        err = _validate_config(config)
        self.assertTrue(err)

    def test_mapping_transform_title_invalid_re(self):
        config = {
            'appbla': {
                'transform_title': {
                    'from': ':(.*(',
                    'to': r'zyx',
                }
            }
        }
        err = _validate_config(config)
        self.assertTrue(err)

if __name__ == '__main__':
    # disable stdout
    unittest.main(buffer=True)
