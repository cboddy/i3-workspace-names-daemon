import unittest

from i3_workspace_names_daemon import build_rename


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class MockLeaf:
    def __init__(self, name, title=None, instance=None, wc=None):
        self.name = name
        if title is not None:
            self.window_title = title
        else:
            self.window_title = name
        if instance is not None:
            self.window_instance = instance
        else:
            self.window_instance = name
        if wc is not None:
            self.window_class = wc
        else:
            self.window_class = name


class MockWorkspace:
    def __init__(self, num, *leaves):
        self.num = num
        self.leaves_ = leaves
        self.visible = True
        self.focused = True
        self.name = ""

    def leaves(self):
        return self.leaves_


class MockTree:
    def __init__(self, mi3):
        self.mi3 = mi3

    def workspaces(self):
        return self.mi3.workspaces


class MockI3:
    def __init__(self, *workspaces):
        self.workspaces = workspaces

    def get_tree(self):
        return MockTree(self)

    def get_workspaces(self):
        return self.workspaces

    def command(self, cmd):
        self.cmd = cmd


def base_config():
    return {
        "delimiter": "|",
        "max_title_length": 12,
        "uniq": False,
        "ignore_unknown": False,
        "no_unknown_name": False,
        "verbose": False,
    }


def base_mappings():
    return {
        "chromium-browser": "chrome",
        "firefox": "firefox",
    }


def get_names(cmd):
    commands = cmd.split(";")
    return [x[len('rename workspace "" to "') : -1] for x in commands]


class TestRename(unittest.TestCase):
    def test_simple(self):
        mappings = base_mappings()
        args = AttrDict(base_config())

        mi3 = MockI3(
            MockWorkspace(1, MockLeaf("firefox")),
            MockWorkspace(2, MockLeaf("chromium-browser")),
        )

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: \uf269", "2: \uf268"]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_two_apps_one_ws(self):
        mappings = base_mappings()
        args = AttrDict(base_config())

        mi3 = MockI3(
            MockWorkspace(1, MockLeaf("firefox"), MockLeaf("chromium-browser"))
        )

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: \uf269|\uf268"]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_two_apps_one_ws_delim(self):
        mappings = base_mappings()
        args = AttrDict(base_config())
        args.delimiter = " "

        mi3 = MockI3(
            MockWorkspace(1, MockLeaf("firefox"), MockLeaf("chromium-browser"))
        )

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: \uf269 \uf268"]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_two_apps_same(self):
        mappings = base_mappings()
        args = AttrDict(base_config())

        mi3 = MockI3(MockWorkspace(1, MockLeaf("firefox"), MockLeaf("firefox")))

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: \uf269|\uf269"]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_two_apps_same_uniq(self):
        mappings = base_mappings()
        args = AttrDict(base_config())
        args.uniq = True

        mi3 = MockI3(MockWorkspace(1, MockLeaf("firefox"), MockLeaf("firefox")))

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: \uf269"]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_two_apps_same_uniq(self):
        mappings = base_mappings()
        args = AttrDict(base_config())
        args.uniq = True

        mi3 = MockI3(MockWorkspace(1, MockLeaf("firefox"), MockLeaf("firefox")))

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: \uf269"]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_unknown_name(self):
        mappings = base_mappings()
        args = AttrDict(base_config())

        mi3 = MockI3(MockWorkspace(1, MockLeaf("giregox")))

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: giregox"]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_long_unknown_name(self):
        mappings = base_mappings()
        args = AttrDict(base_config())

        mi3 = MockI3(MockWorkspace(1, MockLeaf("giregox-giregox-giregox")))

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: giregox-gire…"]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_unknown_name_no_window_class(self):
        mappings = base_mappings()
        args = AttrDict(base_config())

        mi3 = MockI3(MockWorkspace(1, MockLeaf("giregox", "", "", "")))

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: ?"]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_unknown_name_no_match_icon(self):
        mappings = base_mappings()
        mappings["_no_match"] = "question"
        args = AttrDict(base_config())

        mi3 = MockI3(MockWorkspace(1, MockLeaf("giregox")))

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: \uf128giregox"]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_long_unknown_name_no_match_icon(self):
        mappings = base_mappings()
        mappings["_no_match"] = "question"
        args = AttrDict(base_config())

        mi3 = MockI3(MockWorkspace(1, MockLeaf("giregox-giregox-giregox")))

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: \uf128giregox-gire…"]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_unknown_name_no_window_class_no_match_icon(self):
        mappings = base_mappings()
        mappings["_no_match"] = "question"
        args = AttrDict(base_config())

        mi3 = MockI3(MockWorkspace(1, MockLeaf("giregox", "", "", "")))

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: \uf128"]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_unknown_name_ignore(self):
        mappings = base_mappings()
        args = AttrDict(base_config())
        args.ignore_unknown = True

        mi3 = MockI3(MockWorkspace(1, MockLeaf("giregox")))

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: "]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_long_unknown_name_ignore(self):
        mappings = base_mappings()
        args = AttrDict(base_config())
        args.ignore_unknown = True

        mi3 = MockI3(MockWorkspace(1, MockLeaf("giregox-giregox-giregox")))

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: "]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_unknown_name_no_window_class_ignore(self):
        mappings = base_mappings()
        args = AttrDict(base_config())
        args.ignore_unknown = True

        mi3 = MockI3(MockWorkspace(1, MockLeaf("giregox", "", "", "")))

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: "]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_transform_title(self):
        mappings = base_mappings()
        mappings["emacs"] = {
            "transform_title": {"from": r".*\[(.+?)\].*", "to": r"\1",}
        }

        args = AttrDict(base_config())

        mi3 = MockI3(MockWorkspace(1, MockLeaf("emacs", "foo [bar] baz")))

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: bar"]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_transform_title_icon(self):
        mappings = base_mappings()
        mappings["emacs"] = {
            "transform_title": {"from": r".*\[(.+?)\].*", "to": r"\1",},
            "icon": "play",
        }

        args = AttrDict(base_config())

        mi3 = MockI3(MockWorkspace(1, MockLeaf("emacs", "foo [bar] baz")))

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: \uf04bbar"]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_transform_title_replace_all(self):
        mappings = base_mappings()
        mappings["emacs"] = {
            "transform_title": {"from": r"(.*)", "to": r"replaced",},
        }

        args = AttrDict(base_config())

        mi3 = MockI3(MockWorkspace(1, MockLeaf("emacs", "foo [bar] baz")))

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: replaced"]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_transform_title_replace_all_with_icon(self):
        mappings = base_mappings()
        mappings["emacs"] = {
            "transform_title": {"from": r"(.*)", "to": r"replaced",},
            "icon": "play",
        }

        args = AttrDict(base_config())

        mi3 = MockI3(MockWorkspace(1, MockLeaf("emacs", "foo [bar] baz")))

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: \uf04breplaced"]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_transform_title_compress(self):
        mappings = base_mappings()
        mappings["emacs"] = {
            "transform_title": {"from": r".*\[(.+?)\].*", "to": r"\1", "compress": True}
        }

        args = AttrDict(base_config())

        mi3 = MockI3(
            MockWorkspace(
                1, MockLeaf("emacs", "project [a very-too_long+window title]")
            )
        )

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ["1: a ver-too_lo…"]
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)

    def test_pango(self):
        mappings = base_mappings()
        mappings["emacs"] = '<span font_desc="file-icons">\ue926</span>'

        args = AttrDict(base_config())

        mi3 = MockI3(MockWorkspace(1, MockLeaf("emacs")),)

        rename = build_rename(mi3, mappings, args)
        rename(mi3, None)

        expected = ['1: <span font_desc=\\"file-icons\\">\ue926</span>']
        actual = get_names(mi3.cmd)
        self.assertListEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
