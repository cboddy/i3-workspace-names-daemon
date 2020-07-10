import pytest
from conftest import AttrDict, MockWorkspace, MockLeaf

from i3_workspace_names_daemon import build_rename, DEFAULT_ARGS


def base_config():
    return AttrDict(DEFAULT_ARGS)


def base_mappings():
    return {
        "chromium-browser": "chrome",
        "firefox": "firefox",
        'pango_emacs': '<span font_desc="file-icons">\ue926</span>',
        'emacs_unicode': '\ue926',
    }


def get_names(cmd):
    commands = cmd.split(";")
    return [x[len('rename workspace "" to "'): -1] for x in commands]


@pytest.mark.parametrize('workspaces,mappings,args,expected', (
    ((), {}, {}, [""]),  # no windows in any workspace
    ((  # two workspaces
        (1, MockLeaf("firefox")),
        (2, MockLeaf("chromium-browser")),
    ), {}, {}, ['1: \uf269', '2: \uf268']),
    ((  # two apps in one workspace
        (1, MockLeaf("firefox"), MockLeaf("chromium-browser")),
    ), {}, {}, ['1: \uf269|\uf268']),
    ((  # two apps in one workspace, verbose
        (1, MockLeaf("firefox"), MockLeaf("chromium-browser")),
    ), {}, {'verbose': True}, ['1: \uf269|\uf268']),
    ((  # two apps in one workspace, with space delimiter
        (1, MockLeaf("firefox"), MockLeaf("chromium-browser")),
    ), {}, {'delimiter': ' '}, ['1: \uf269 \uf268']),
    ((  # twice same app in a workspace
        (1, MockLeaf("firefox"), MockLeaf("firefox")),
    ), {}, {}, ['1: \uf269|\uf269']),
    ((  # twice same app in a workspace, with uniq
        (1, MockLeaf("firefox"), MockLeaf("firefox")),
    ), {}, {'uniq': True}, ['1: \uf269']),
    ((  # unknown name
        (1, MockLeaf("giregox")),
    ), {}, {}, ['1: giregox']),
    ((  # unknown name that is long gets truncated with ellipsis
        (1, MockLeaf('giregox-giregox-giregox')),
    ), {}, {}, ['1: giregox-gire…']),
    ((  # unknown name and no window class, expected truncated window name
        (1, MockLeaf('giregox', '', '', '')),
    ), {}, {}, ['1: giregox']),
    ((  # unknown name, with _no_match icon
        (1, MockLeaf('giregox')),
    ), {'_no_match': 'question'}, {}, ['1: \uf128giregox']),
    ((  # unknown name, with _no_match icon but long so ellipsis
        (1, MockLeaf('giregox-giregox')),
    ), {'_no_match': 'question'}, {}, ['1: \uf128giregox-gire…']),
    ((  # unknown name, no CLASS and no_match icon
        (1, MockLeaf('giregox', '', '', '')),
    ), {'_no_match': 'question'}, {}, ['1: \uf128giregox']),
    ((  # ignore unknown option
        (1, MockLeaf('giregox')),
    ), {}, {'ignore_unknown': True}, ['1']),
    ((  # ignore unknown option, with long name
        (1, MockLeaf('giregox-giregox-giregox')),
    ), {}, {'ignore_unknown': True}, ['1']),
    ((  # ignore unknown option, no class
        (1, MockLeaf('giregox', '', '', '')),
    ), {}, {'ignore_unknown': True}, ['1']),
    # TEXT TRANSFORMATIONS
    (
        (  # just transform title through regex replace
            (1, MockLeaf('emacs', 'foo [bar] baz')),
        ), {'emacs': {
            "transform_title": {"from": r".*\[(.+?)\].*", "to": r"\1"},
        }}, {}, ['1: bar']
    ),
    (
        (  # just transform title through regex replace, adding icon
            (1, MockLeaf('emacs', 'foo [bar] baz')),
        ), {'emacs': {
            "transform_title": {"from": r".*\[(.+?)\].*", "to": r"\1"},
            "icon": 'play',
        }}, {}, ['1: \uf04bbar']
    ),
    (
        (  # just replaces the title, this test doesn't test anything new, can be removed
            (1, MockLeaf('emacs', 'foo [bar] baz')),
        ), {'emacs': {
            "transform_title": {"from": r".*\[(.+?)\].*", "to": r"replaced"},
            "icon": 'play',
        }}, {}, ['1: \uf04breplaced']
    ),
    (
        (  # just transform title through regex replace, COMPRESS
            (1, MockLeaf('emacs', 'project [a very-too_long+window title]')),
        ), {'emacs': {
            "transform_title": {"from": r".*\[(.+?)\].*", "to": r"\1", 'compress': True},
        }}, {}, ['1: a ver-too_lo…']
    ),
    (
        (  # just transform title through regex replace, no compress but long
            (1, MockLeaf('emacs', 'project [a very-too_long+window title]')),
        ), {'emacs': {
            "transform_title": {"from": r".*\[(.+?)\].*", "to": r"\1", 'compress': False},
        }}, {}, ['1: a very-too_l…']
    ),
    ((  # pango markup
        (1, MockLeaf('pango_emacs')),
    ), {}, {}, ['1: <span font_desc=\\"file-icons\\">\ue926</span>']),
    ((  # unicode directely
        (1, MockLeaf('emacs_unicode')),
    ), {}, {}, ['1: \ue926']),
    ((  # icon defined but not found, maybe mispelled
        (1, MockLeaf('emacs')),
    ), {'emacs': 'not_there'}, {}, ['1: emacs']),
    (
        (  # test icon inside dict without transform_title
            (1, MockLeaf('emacs')),
        ), {'emacs': {
            'icon': '<span font_desc=\"file-icons\">\ue926</span>',
        }}, {}, ['1: <span font_desc=\\"file-icons\\">\ue926</span>']
    ),
    ((  # none in every window prop
        (1, MockLeaf(None, None, None, None)),
    ), {}, {}, ['1: ?']),
    ((  # empty string in every window prop
        (1, MockLeaf('')),
    ), {}, {}, ['1: ?']),
    ((  # workspace number -1  (means named workspace)
        # leave it untouched
        (-1, MockLeaf('firefox')),
    ), {}, {}, ['']),  # in order to assert expected workspace name a separate test would be needed
))
def test_rename(workspaces, mappings, args, expected, mocki3):
    _mappings = base_mappings()
    _mappings.update(mappings)
    _args = base_config()
    _args.update(args)
    mock_i3 = mocki3(*workspaces)
    rename = build_rename(mock_i3, _mappings, _args)
    rename(mock_i3, None)
    assert expected == get_names(mock_i3.cmd)
