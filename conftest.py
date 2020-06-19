from i3_workspace_names_daemon import DEFAULT_ARGS
import argparse
import i3ipc
import pytest


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
    def __init__(self, args):
        self.num = args[0]
        self.leaves_ = args[1:]
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
        self.workspaces = [MockWorkspace(w) for w in workspaces]
        self.tree = MockTree(self)

    @staticmethod
    def main():
        pass

    @staticmethod
    def on(event, callback):
        pass

    def get_tree(self):
        return self.tree

    def get_workspaces(self):
        return self.workspaces

    def command(self, cmd):
        self.cmd = cmd


@pytest.fixture
def mocki3(monkeypatch):
    def _mocki3(*workspaces):
        i3 = MockI3(*workspaces)
        return i3
    monkeypatch.setattr(i3ipc, 'Connection', _mocki3)
    return _mocki3


@pytest.fixture
def argparse_fix(monkeypatch):
    def _argparse_fix(args):
        def argparse_gen(args):
            class ArgumentParser:
                def __init__(self, doc):
                    pass

                def add_argument(self, *_, **__):
                    pass

                def parse_args(self):
                    return AttrDict(args)

            return ArgumentParser

        args = DEFAULT_ARGS.copy()
        args.update({'config_path': ''})
        monkeypatch.setattr(argparse, 'ArgumentParser', argparse_gen(args))
    return _argparse_fix
