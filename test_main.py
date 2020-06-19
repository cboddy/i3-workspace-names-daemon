from i3_workspace_names_daemon import main


def test_main(argparse_fix, mocki3):  # pylint: disable=W0613
    argparse_fix({})
    main()


def test_verbose(argparse_fix, mocki3):  # pylint: disable=W0613
    argparse_fix({'verbose': True})
    main()

def test_config_validation_failed(argparse_fix, mocki3):  # pylint: disable=W0613
    pass
