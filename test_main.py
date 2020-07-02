from pytest import raises
from conftest import MockLeaf
import i3_workspace_names_daemon
from i3_workspace_names_daemon import main
import os


def test_main(argparse_fix, mocki3):
    argparse_fix({})
    mocki3()
    main()


def test_verbose_startup(argparse_fix, mocki3, caplog):
    argparse_fix({'verbose': True})
    mocki3(
        (1, MockLeaf('firefox')),
    )
    main()
    assert 'WORKSPACE: ""' in caplog.text
    assert '===> leave: 0' in caplog.text
    assert '-> name: firefox' in caplog.text
    assert '-> window_title: firefox' in caplog.text
    assert '-> window_instance: firefox' in caplog.text
    assert '-> window_class: firefox' in caplog.text


def test_config_validation_failed(monkeypatch, argparse_fix, mocki3, caplog):
    argparse_fix({})
    mocki3()
    monkeypatch.setattr(i3_workspace_names_daemon, '_get_mapping', lambda cp: {'firefox': []})
    main()
    assert 'Errors in configuration found!' in caplog.text


def test_config_path_not_existing(argparse_fix, mocki3):
    argparse_fix({'config_path': 'not_existing'})
    mocki3()
    with raises(SystemExit):
        main()

def test_config_path_is_not_a_file(monkeypatch, argparse_fix, mocki3, caplog):
    argparse_fix({})
    mocki3()
    monkeypatch.setattr(os.path, 'isfile', lambda p: False)
    main()
    assert "Using default app-icon config" in caplog.text

def test_i3_config_directory_doesnt_exist(monkeypatch, argparse_fix, mocki3):
    argparse_fix({})
    mocki3()
    monkeypatch.setattr(os.path, 'isdir', lambda p: False)
    with raises(SystemExit) as ex:
        main()
    assert 'Could not find i3 config directory! Expected one of' in str(ex)
