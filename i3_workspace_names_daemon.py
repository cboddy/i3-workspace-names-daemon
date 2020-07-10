#!/usr/bin/env python3
"""Dynamically update i3wm workspace names based on running applications in each and optionally define an icon to show instead."""

import json
import os.path
import argparse
import logging
import re
import i3ipc
from pprint import pformat
from fa_icons import icons as fa_icons


log = logging.getLogger()  # I mean... it's ok to use root logger...

I3_CONFIG_PATHS = tuple(
    os.path.expanduser(path)
    for path in ("~/.i3", "~/.config/i3", "~/.config/i3-regolith")
)

DEFAULT_APP_ICON_CONFIG = {
    "chromium-browser": "chrome",
    "firefox": "firefox",
    "x-terminal-emulator": "terminal",
    "thunderbird": "envelope",
    "jetbrains-idea-ce": "edit",
    "nautilus": "folder-open",
    "clementine": "music",
    "vlc": "play",
    "signal": "comment",
}


DEFAULT_ARGS = {
    'config_path': None,
    'delimiter': '|',
    'max_title_length': 12,
    'verbose': False,
    'no_match_not_show_name': False,
    'ignore_unknown': False,
    'uniq': False,
    'log_path': None,
}

def truncate(text, length, ellipsis="…"):
    if len(text) <= length:
        return text
    return text[:length] + ellipsis


def compress(text, length=3):
    ret = ""
    matches = re.finditer(r"[a-zA-Z0-9]+", text)
    for match in matches:
        ret += match[0][:length]
        if match.end() < (len(text) - 1):
            ret += text[match.end()]

    return ret


def build_rename(i3, mappings, args):
    """Build rename callback function to pass to i3ipc.

    Parameters
    ----------
    i3: `i3ipc.i3ipc.Connection`
    mappings: `dict[str, Union[dict, str]]`
        Index of application-name regex (from i3) to icon-name (in font-awesome gallery).
    args: `object`
        Arguments parameters usually from argparse

    Returns
    -------
    func
        The rename callback.
    """
    delim = args.delimiter
    length = args.max_title_length
    uniq = args.uniq
    ignore_unknown = args.ignore_unknown
    no_unknown_name = args.no_match_not_show_name
    verbose = args.verbose

    def get_icon(icon_name):
        # is pango markup?
        if icon_name.startswith("<"):
            return icon_name  # you can also use colored text and so on
        try:
            # is fontawesome icon name?
            icon_name.encode('ascii')
            if icon_name in fa_icons:
                return fa_icons[icon_name]
        except UnicodeEncodeError as ex:
            # is unicode icon, this is reached when you specified another font
            # in i3 bar config, so you put /ucode directely (instead of from fa_icons)
            # otherwise... if fontawesome gets updated and we don't still provide the new icon mapping.
            return icon_name
        return None

    def transform_title(target_mapping, window_title):
        tt = target_mapping["transform_title"]
        transform_from = "^" + tt["from"] + "$"
        transform_to = tt["to"]
        result, nr_subs = re.subn(transform_from, transform_to, window_title)

        # shorten name
        if tt.get("compress", False):
            result = compress(result)
        result = truncate(result, length)

        # try to get the icon, otherwise leave blank string
        icon = ""
        if target_mapping.get("icon", None):
            i = get_icon(target_mapping["icon"])
            if i:
                icon = i

        # did the title regex match?
        if nr_subs > 0:
            return "{}{}".format(icon, result)

    def resolve_icon_or_mapping(name, leaf):
        for name_re in mappings.keys():
            if re.match(name_re, name, re.IGNORECASE):
                # the key of the json configuration matches, we can
                # apply the mapping now
                target_mapping = mappings[name_re]

                if type(target_mapping) == str:
                    return get_icon(target_mapping)

                # is mapped to a title transformation?
                if type(target_mapping) == dict:
                    # it could be a dict, have the icon but not transform_title
                    if target_mapping.get("transform_title"):
                        window_title = getattr(
                            leaf,
                            target_mapping['transform_title'].get('on', "window_title"),
                            ""
                        )
                        return transform_title(target_mapping, window_title)
                    return get_icon(target_mapping.get('icon', ''))


    def get_app_identifiers(leaf):
        identifiers = {}
        for identifier in ("name", "window_title", "window_instance", "window_class"):
            name = getattr(leaf, identifier, None)
            identifiers[identifier] = name if name is not None else ''  # cannot use just '' in getattr
        return identifiers

    def get_app_label(leaf, length):
        for name in get_app_identifiers(leaf).values():
            mapping = resolve_icon_or_mapping(name, leaf)
            if mapping:
                return mapping

        log.warning('no match found for:\n%s', pformat(
            get_app_identifiers(leaf),
            indent=4,
        ))
        # no mapping was found
        if ignore_unknown:
            return None

        no_match_fallback = "_no_match" in mappings and mappings["_no_match"] in fa_icons
        for name in get_app_identifiers(leaf).values():
            # window class exists, no match was found
            if not name:
                continue
            if no_match_fallback:
                return fa_icons[mappings["_no_match"]] + (
                    "" if no_unknown_name else truncate(name, length)
                )
            return truncate(name, length)
        log.error('no identifiable information about this window')
        return "?"

    def rename(i3, _):
        workspaces = i3.get_tree().workspaces()
        # need to use get_workspaces since the i3 con object doesn't have the visible property for some reason
        workdicts = i3.get_workspaces()
        visible = [workdict.name for workdict in workdicts if workdict.visible]
        visworkspaces = []
        focus = (
            [workdict.name for workdict in workdicts if workdict.focused] or [None]
        )[0]
        focusname = None

        commands = []
        for workspace in workspaces:
            names = [get_app_label(leaf, length) for leaf in workspace.leaves()]
            if uniq:
                seen = set()
                names = [x for x in names if x not in seen and not seen.add(x)]
            # filter empty names
            names = [x for x in names if x]
            names = delim.join(names)
            if int(workspace.num) >= 0:
                if len(names) != 0:
                    newname = u"{}: {}".format(workspace.num, names)
                else:
                    newname = str(workspace.num)
            else:  # pragma: no cover (due to https://github.com/nedbat/coveragepy/issues/198 )
                # named workspaces have -1 as number
                # continue here means the name will stay untouched
                # go into your i3 config if you want to customize it,
                # but it will always be static
                continue

            if workspace.name in visible:
                visworkspaces.append(newname)
            if workspace.name == focus:
                focusname = newname

            if workspace.name != newname:
                commands.append(
                    'rename workspace "{}" to "{}"'.format(
                        # escape any double quotes in old or new name.
                        workspace.name.replace('"', '\\"'),
                        newname.replace('"', '\\"'),
                    )
                )
                if verbose:
                    log.debug(commands[-1])

        # we have to join all the activate workspaces commands into one or the order
        # might get scrambled by multiple i3-msg instances running asyncronously
        # causing the wrong workspace to be activated last, which changes the focus.
        i3.command(u";".join(commands))

    return rename


def _get_i3_dir():
    # standard i3-config directories
    for path in I3_CONFIG_PATHS:
        if os.path.isdir(path):
            return path
    raise SystemExit(
        "Could not find i3 config directory! Expected one of {} to be present".format(
            I3_CONFIG_PATHS
        )
    )


def _get_mapping(config_path=None):
    """Get app-icon mapping from config file or use defaults.

    Parameters
    ----------
    config_path: `str|None`
        Path to app-icon config file.

    Returns
    -------
    dict[str, Union[dict, str]]
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
            raise SystemExit(
                "Specified app-icon config path '{}' does not exist".format(config_path)
            )
    else:
        config_path = os.path.join(_get_i3_dir(), "app-icons.json")

    if os.path.isfile(config_path):
        with open(config_path) as f:
            mappings = json.load(f)
        # normalise app-names to lower
        return {k.lower(): v for k, v in mappings.items()}
    log.warning("Using default app-icon config %s", DEFAULT_APP_ICON_CONFIG)
    return dict(DEFAULT_APP_ICON_CONFIG)


def _verbose_startup(i3):
    for w in i3.get_tree().workspaces():
        log.debug('WORKSPACE: "{}"'.format(w.name))
        for i, l in enumerate(w.leaves()):
            log.debug(
                """===> leave: {}
-> name: {}
-> window_title: {}
-> window_instance: {}
-> window_class: {}""".format(
                    i, l.name, l.window_title, l.window_instance, l.window_class
                )
            )


def _is_valid_re(regex):
    try:
        re.compile(regex)
        return True
    except:
        return False


def _validate_dict_mapping(app, mapping):
    err = False
    if mapping.get("transform_title", None):
        # a title transformation exists
        tt = mapping["transform_title"]

        if tt.get("from", None):
            if not _is_valid_re(tt["from"]):
                err = True
                log.error(
                    "Title transform mapping for app '{}' contains invalid regular expression in 'from' attribute!".format(
                        app
                    )
                )
        else:
            err = True
            log.error(
                "Title transform mapping for app '{}' requires a 'from' key!".format(
                    app
                )
            )

        if not tt.get("to", None):
            err = True
            log.error(
                "Title transform mapping for app '{}' requires a 'to' key!".format(app)
            )

    return err


def _validate_config(config):
    """returns True when THERE IS something wrong"""
    # check for missing icons and wrong configurations
    for app, value in config.items():
        icon_name = None
        if type(value) == str:
            icon_name = value
        else:
            # icon is optional when using a transform mapping
            if type(value) != dict:
                log.error("Specified mapping for app '{}' is not a dict!".format(app))
                return True
            icon_name = value.get("icon", None)
            if _validate_dict_mapping(app, value):
                return True

        # make exceptions for custom-defined pango fonts
        if (
            icon_name is not None
            and not icon_name.startswith("<")
            and not icon_name in fa_icons
        ):
            log.error(
                "Specified icon '{}' for app '{}' does not exist!".format(
                    icon_name, app
                )
            )
            return True



def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument(
        "-config-path",
        help="Path to file that maps applications to icons in json format. Defaults to ~/.i3/app-icons.json or ~/.config/i3/app-icons.json or hard-coded list if they are not available.",
        required=False,
    )
    parser.add_argument(
        "-d",
        "--delimiter",
        help="The delimiter used to separate multiple window names in the same workspace.",
        required=False,
        default=DEFAULT_ARGS['delimiter'],
    )
    parser.add_argument(
        "-l",
        "--max-title-length",
        help="Truncate title to specified length.",
        required=False,
        default=DEFAULT_ARGS['max_title_length'],
        type=int,
    )
    parser.add_argument(
        "-u",
        "--uniq",
        help="Remove duplicate icons.",
        action="store_true",
        required=False,
        default=DEFAULT_ARGS['uniq'],
    )
    parser.add_argument(
        "-i",
        "--ignore-unknown",
        help="Ignore apps without a icon definitions.",
        action="store_true",
        required=False,
        default=DEFAULT_ARGS['ignore_unknown'],
    )
    parser.add_argument(
        "-n",
        "--no-match-not-show-name",
        help="Don't display the name of unknown apps besides the fallback icon '_no_match'.",
        action="store_true",
        required=False,
        default=DEFAULT_ARGS['no_match_not_show_name'],
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Verbose logging that will help you to find the right match name for applications.",
        action="store_true",
        required=False,
        default=DEFAULT_ARGS['verbose'],
    )
    parser.add_argument(
        '--log-path',
        help="path of the log to be generated, it will be overwriten every time this script starts. by default console will be used instead of a file",
        required=False,
        default=DEFAULT_ARGS['log_path'],
    )
    args = parser.parse_args()

    logging.basicConfig(
        filename=args.log_path,
        filemode='w',
        level=logging.WARNING
    )
    if args.verbose:
        log.setLevel(level=logging.DEBUG)

    mappings = _get_mapping(args.config_path)

    if _validate_config(mappings):
        log.error("Errors in configuration found!")

    # build i3-connection
    i3 = i3ipc.Connection()
    if args.verbose:
        _verbose_startup(i3)

    rename = build_rename(i3, mappings, args)
    for case in ["window::move", "window::new", "window::title", "window::close"]:
        i3.on(case, rename)
    i3.main()


if __name__ == "__main__":  # pragma: no cover
    main()
