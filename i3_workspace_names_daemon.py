#!/usr/bin/env python3
"""Dynamically update i3wm workspace names based on running applications in each and optionally define an icon to show instead."""

import json
import os.path
import argparse
import re
import i3ipc
from fa_icons import icons

I3_CONFIG_PATHS = tuple(os.path.expanduser(path) for path in ("~/.i3", "~/.config/i3", "~/.config/i3-regolith"))

DEFAULT_APP_ICON_CONFIG = {
    "chromium-browser": "chrome",
    "firefox": "firefox",
    "x-terminal-emulator": "terminal",
    "thunderbird": "envelope",
    "jetbrains-idea-ce": "edit",
    "nautilus": "folder-open",
    "clementine": "music",
    "vlc": "play",
    "signal": "comment"
}


def build_rename(i3, app_icons, args):
    """Build rename callback function to pass to i3ipc.

    Parameters
    ----------
    i3: `i3ipc.i3ipc.Connection`
    app_icons: `dict[str, str]`
        Index of application-name regex (from i3) to icon-name (in font-awesome gallery).
    delim: `str`
        Delimiter to use when build workspace name from app names/icons.

    Returns
    -------
    func
        The rename callback.
    """
    form = args.format
    delim = args.delimiter
    length = args.max_title_length
    uniq = args.uniq
    no_match_show_name = not args.no_match_not_show_name
    verbose = args.verbose

    def get_icon_or_name(leaf, length):
        for identifier in ('name', 'window_title', 'window_instance', 'window_class'):
            name = getattr(leaf, identifier, None)
            if name is None:
                continue
            for name_re in app_icons.keys():
                if re.match(name_re, name, re.IGNORECASE) \
                   and app_icons[name_re] in icons:
                    return icons[app_icons[name_re]]
        if name:
            if "_no_match" in app_icons and app_icons["_no_match"] in icons:
                return icons[app_icons["_no_match"]] + ('{}'.format(name) if no_match_show_name else '')
            return name[:length]
        else:
            # no identifiable information about this window
            return '?'

    def rename(i3, e):
        workspaces = i3.get_tree().workspaces()
        # need to use get_workspaces since the i3 con object doesn't have the visible property for some reason
        workdicts = i3.get_workspaces()
        visible = [workdict.name for workdict in workdicts if workdict.visible]
        visworkspaces = []
        focus = ([workdict.name for workdict in workdicts if workdict.focused] or [None])[0]
        focusname = None

        commands = []
        for workspace in workspaces:
            names = [get_icon_or_name(leaf, length)
                     for leaf in workspace.leaves()]
            if uniq:
                seen = set()
                names = [x for x in names if x not in seen and not seen.add(x)]
            names = delim.join(names)
            if int(workspace.num) >= 0:
                newname = form.format(workspace.num, names)
            else:
                newname = names

            if workspace.name in visible:
                visworkspaces.append(newname)
            if workspace.name == focus:
                focusname = newname

            if workspace.name != newname:
                commands.append('rename workspace "{}" to "{}"'.format(
                    # escape any double quotes in old or new name.
                    workspace.name.replace('"', '\\"'), newname.replace('"', '\\"')))
                if verbose:
                    print(commands[-1])

        # we have to join all the activate workspaces commands into one or the order
        # might get scrambled by multiple i3-msg instances running asyncronously
        # causing the wrong workspace to be activated last, which changes the focus.
        i3.command(u';'.join(commands))
    return rename


def _get_i3_dir():
    # standard i3-config directories
    for path in I3_CONFIG_PATHS:
        if os.path.isdir(path):
            return path
    raise SystemExit("Could not find i3 config directory! Expected one of {} to be present".format(I3_CONFIG_PATHS))


def _get_app_icons(config_path=None):
    """Get app-icon mapping from config file or use defaults.

    Parameters
    ----------
    config_path: `str|None`
        Path to app-icon config file.

    Returns
    -------
    dict[str,str]
        Index of application-name (from i3) to icon-name (in font-awesome gallery).

    Raises
    ------
    json.decoder.JSONDecodeError
        When app-icon config file is not in JSON format.

    SystemExit
        When `config_path is not None` and there is not a file available at tht path.
        When ~/.i3 or ~/.config/i3 is not a directory (ie. i3 is not installed).

    Notes
    -----
    If config_path is None then the locations ~/.i3/app-icons.json and ~/.config/i3/app-icons.json will also be used if available. If they are also not available then `DEFAULT_APP_ICON_CONFIG` will be used.
    """

    if config_path:
        if not os.path.isfile(config_path):
            raise SystemExit("Specified app-icon config path '{}' does not exist".format(config_path))
    else:
        config_path = os.path.join(_get_i3_dir(), "app-icons.json")

    if os.path.isfile(config_path):
        with open(config_path) as f:
            app_icons = json.load(f)
        # normalise app-names to lower
        return {k.lower(): v for k, v in app_icons.items()}
    else:
        print('Using default app-icon config {}'.format(DEFAULT_APP_ICON_CONFIG))
        return dict(DEFAULT_APP_ICON_CONFIG)


def _verbose_startup(i3):
    for w in i3.get_tree().workspaces():
        print('WORKSPACE: "{}"'.format(w.name))
        for i, l in enumerate(w.leaves()):
            print('''===> leave: {}
-> name: {}
-> window_title: {}
-> window_instance: {}
-> window_class: {}'''.format(i, l.name, l.window_title, l.window_instance, l.window_class))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("-config-path",
                        help="Path to file that maps applications to icons in json format. Defaults to ~/.i3/app-icons.json or ~/.config/i3/app-icons.json or hard-coded list if they are not available.",
                        required=False)
    parser.add_argument("-f", "--format",
            help='Format of the workspace number + names/icons.\nThe first "{}" represents the workspace number space and the second represents the names/icons space.\nEx: - "{}: {}" (Default)\n - "{} - {}"\n - "{} ( {} )"',
                        required=False,
                        default="{}: {}")
    parser.add_argument("-d", "--delimiter",
                        help="The delimiter used to separate multiple window names in the same workspace.",
                        required=False,
                        default="|")
    parser.add_argument("-l", "--max_title_length", help="Truncate title to specified length.",
                        required=False,
                        default=12,
                        type=int)
    parser.add_argument("-u", "--uniq", help="Remove duplicate icons in case the same application ",
                        action="store_true",
                        required=False,
                        default=False)
    parser.add_argument('-n', "--no-match-not-show-name",
                        help="when you set '_no_match' in your app icons, if you don't want the application name set this option",
                        action="store_true", required=False, default=False)
    parser.add_argument("-v", "--verbose", help="verbose startup that will help you to find the right name of the window",
                        action="store_true",
                        required=False,
                        default=False)
    args = parser.parse_args()

    app_icons = _get_app_icons(args.config_path)

    # check for missing icons
    for app, icon_name in app_icons.items():
        if not icon_name in icons:
            print("Specified icon '{}' for app '{}' does not exist!".format(icon_name, app))

    # build i3-connection
    i3 = i3ipc.Connection()
    if args.verbose:
        _verbose_startup(i3)

    rename = build_rename(i3, app_icons, args)
    for case in ['window::move', 'window::new', 'window::title', 'window::close']:
        i3.on(case, rename)
    i3.main()


if __name__ == '__main__':
    main()
