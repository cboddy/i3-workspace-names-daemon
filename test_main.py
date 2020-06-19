from pytest import raises
from conftest import MockLeaf
import i3_workspace_names_daemon
from i3_workspace_names_daemon import main
import os


def test_main(argparse_fix, mocki3):
    argparse_fix({})
    mocki3()
    main()


def test_verbose(argparse_fix, mocki3, capsys):
    argparse_fix({'verbose': True})
    mocki3(
        (1, MockLeaf('firefox')),
    )
    main()
    out, err = capsys.readouterr()
    # assert 'WORKSPACE:' in out
    # FIXME: does not work for me, out and err are always empty strings


def test_config_validation_failed(monkeypatch, argparse_fix, mocki3):
    argparse_fix({})
    mocki3()
    monkeypatch.setattr(i3_workspace_names_daemon, '_get_mapping', lambda cp: {'firefox': []})
    main()
    # Errors in configuration found!


def test_config_path_not_existing(argparse_fix, mocki3):
    argparse_fix({'config_path': 'not_existing'})
    mocki3()
    with raises(SystemExit):
        main()

def test_config_path_is_not_a_file(monkeypatch, argparse_fix, mocki3):
    argparse_fix({})
    mocki3()
    monkeypatch.setattr(os.path, 'isfile', lambda p: False)
    main()
    # "Using default app-icon config {}".format(DEFAULT_APP_ICON_CONFIG)

def test_i3_config_directory_doesnt_exist(monkeypatch, argparse_fix, mocki3):
    argparse_fix({})
    mocki3()
    monkeypatch.setattr(os.path, 'isdir', lambda p: False)
    with raises(SystemExit):
        main()
    # Could not find i3 config directory! Expected one of
