import pytest

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

    def __repr__(self):  # pragma: no cover
        # for proper output if test fail
        return f'<Leaf {self.__dict__}>'


class MockWorkspace:
    def __init__(self, num, *leaves):
        self.num = num
        self.leaves_ = leaves
        self.visible = True
        self.focused = True
        self.name = ""

    def leaves(self):
        return self.leaves_

    def __repr__(self):  # pragma: no cover
        # for proper output if test fail
        return f'<MockWorkspace {self.leaves_}>'


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
    return AttrDict({
        "delimiter": "|",
        "max_title_length": 12,
        "uniq": False,
        "ignore_unknown": False,
        "no_match_not_show_name": False,
        "verbose": False,
    })


def base_mappings():
    return {
        "chromium-browser": "chrome",
        "firefox": "firefox",
        'pango_emacs': '<span font_desc="file-icons">\ue926</span>',
    }


def get_names(cmd):
    commands = cmd.split(";")
    return [x[len('rename workspace "" to "') : -1] for x in commands]


@pytest.mark.parametrize('workspaces,mappings,args,expected', (
    ((), {}, {}, [""]),  # no windows in any workspace
    ((  # two workspaces
        MockWorkspace(1, MockLeaf("firefox")),
        MockWorkspace(2, MockLeaf("chromium-browser")),
    ), {}, {}, ['1: \uf269', '2: \uf268']),
    ((  # two apps in one workspace
        MockWorkspace(1, MockLeaf("firefox"), MockLeaf("chromium-browser")),
    ), {}, {}, ['1: \uf269|\uf268']),
    ((  # two apps in one workspace, with space delimiter
        MockWorkspace(1, MockLeaf("firefox"), MockLeaf("chromium-browser")),
    ), {}, {'delimiter': ' '}, ['1: \uf269 \uf268']),
    ((  # twice same app in a workspace
        MockWorkspace(1, MockLeaf("firefox"), MockLeaf("firefox")),
    ), {}, {}, ['1: \uf269|\uf269']),
    ((  # twice same app in a workspace, with uniq
        MockWorkspace(1, MockLeaf("firefox"), MockLeaf("firefox")),
    ), {}, {'uniq': True}, ['1: \uf269']),
    ((  # unknown name
        MockWorkspace(1, MockLeaf("giregox")),
    ), {}, {}, ['1: giregox']),
    ((  # unknown name that is long gets truncated with ellipsis
        MockWorkspace(1, MockLeaf('giregox-giregox-giregox')),
    ), {}, {}, ['1: giregox-gire…']),
    ((  # unknown name and no window class, expected plain "?"
        # TODO: it this correct? should we expect "giregox" instead of "?"
        MockWorkspace(1, MockLeaf('giregox', '', '', '')),
    ), {}, {}, ['1: ?']),
    ((  # unknown name, with _no_match icon
        MockWorkspace(1, MockLeaf('giregox')),
    ), {'_no_match': 'question'}, {}, ['1: \uf128giregox']),
    ((  # unknown name, with _no_match icon but long so ellipsis
        MockWorkspace(1, MockLeaf('giregox-giregox')),
    ), {'_no_match': 'question'}, {}, ['1: \uf128giregox-gire…']),
    ((  # unknown name, no CLASS and no_match icon
        # TODO: as the above TODO is this correct?
        MockWorkspace(1, MockLeaf('giregox', '', '', '')),
    ), {'_no_match': 'question'}, {}, ['1: \uf128']),
    ((  # ignore unknown option
        # TODO: is "1: " right? should it be just "1"?
        MockWorkspace(1, MockLeaf('giregox')),
    ), {}, {'ignore_unknown': True}, ['1: ']),
    ((  # ignore unknown option, with long name
        # TODO: is "1: " right? should it be just "1"?
        MockWorkspace(1, MockLeaf('giregox-giregox-giregox')),
    ), {}, {'ignore_unknown': True}, ['1: ']),
    ((  # ignore unknown option, no class
        # TODO: is "1: " right? should it be just "1"?
        MockWorkspace(1, MockLeaf('giregox', '', '', '')),
    ), {}, {'ignore_unknown': True}, ['1: ']),
    # TEXT TRANSFORMATIONS
    (
        (  # just transform title through regex replace
            MockWorkspace(1, MockLeaf('emacs', 'foo [bar] baz')),
        ), {'emacs': {
            "transform_title": {"from": r".*\[(.+?)\].*", "to": r"\1"},
        }}, {}, ['1: bar']
    ),
    (
        (  # just transform title through regex replace, adding icon
            MockWorkspace(1, MockLeaf('emacs', 'foo [bar] baz')),
        ), {'emacs': {
            "transform_title": {"from": r".*\[(.+?)\].*", "to": r"\1"},
            "icon": 'play',
        }}, {}, ['1: \uf04bbar']
    ),
    (
        (  # just replaces the title, this test doesn't test anything new, can be removed
            MockWorkspace(1, MockLeaf('emacs', 'foo [bar] baz')),
        ), {'emacs': {
            "transform_title": {"from": r".*\[(.+?)\].*", "to": r"replaced"},
            "icon": 'play',
        }}, {}, ['1: \uf04breplaced']
    ),
    (
        (  # just transform title through regex replace, COMPRESS
            MockWorkspace(1, MockLeaf('emacs', 'project [a very-too_long+window title]')),
        ), {'emacs': {
            "transform_title": {"from": r".*\[(.+?)\].*", "to": r"\1", 'compress': True},
        }}, {}, ['1: a ver-too_lo…']
    ),
    (
        (  # just transform title through regex replace, no compress but long
            MockWorkspace(1, MockLeaf('emacs', 'project [a very-too_long+window title]')),
        ), {'emacs': {
            "transform_title": {"from": r".*\[(.+?)\].*", "to": r"\1", 'compress': False},
        }}, {}, ['1: a very-too_l…']
    ),
    ((  # pango markup
        MockWorkspace(1, MockLeaf('pango_emacs')),
    ), {}, {}, ['1: <span font_desc=\\"file-icons\\">\ue926</span>']),
    ((  # icon defined but not found, maybe mispelled
        MockWorkspace(1, MockLeaf('emacs')),
    ), {'emacs': 'not_there'}, {}, ['1: emacs']),
    (
        (  # test icon inside dict without transform_title
            MockWorkspace(1, MockLeaf('emacs')),
        ), {'emacs': {
            'icon': '<span font_desc=\"file-icons\">\ue926</span>',
        }},{}, ['1: <span font_desc=\\"file-icons\\">\ue926</span>']
    ),
))
def test_rename(workspaces, mappings, args, expected):
    _mappings = base_mappings()
    _mappings.update(mappings)
    _args = base_config()
    _args.update(args)
    mock_i3 = MockI3(*workspaces)
    rename = build_rename(mock_i3, _mappings, _args)
    rename(mock_i3, None)
    assert expected == get_names(mock_i3.cmd)
