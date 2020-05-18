# i3-workspace-names-daemon

This script dynamically updates [i3wm](https://i3wm.org/) workspace names based on the names of the windows therein. 

It also allows users to define an icon to show for a named window from the [Font Awesome](https://origin.fontawesome.com/icons?d=gallery) icon list.

### tl;dr 
update i3-bar workspace names to look something like this

<img src="https://raw.githubusercontent.com/cboddy/_vim_gifs/master/i3-bar-with-icons.png"></img>

### install

Install the [package](https://pypi.org/project/i3-workspace-names-daemon/) from pypi with [pip](https://pypi.org/project/pip/).

```
sudo pip3 install i3-workspace-names-daemon
```

**NB. if you don't have sudo privileges instead do**

```
pip3 install --user i3-workspace-names-daemon
```
##### font 

Install the [Font Awesome](https://origin.fontawesome.com/icons?d=gallery) font via your favourite package manager. This is necessary if you want to show an icon instead of a window's name in the i3 status bar. 

You can use all icon fonts available on your system thanks to pango. [More here](#more-icons-with-pango).
 

For Debian/Ubuntu et al. 

```
sudo apt install fonts-font-awesome
```

**NB: if the glyphs are not rendering make sure the font is installed.**


### i3 config

Add the following line to your ``~/.i3/config``.

```
exec_always --no-startup-id exec i3-workspace-names-daemon
```

If you use the ``$mod+1`` etc. shortcuts to switch workspaces then update the following so that the *switch to workspace* and *move focused window to workspace* **shortcuts still work**. 


from 

```
bindsym $mod+1 workspace 1
bindsym $mod+Shift+1 move container to workspace 1
# etc
```

to

```
bindsym $mod+1 workspace number 1
bindsym $mod+Shift+1 move container to workspace number 1
# etc
```


### icons config
Configure what icons to show for what application-windows in the file  ``~/.i3/app-icons.json`` or ``~/.config/i3/app-icons.json`` (in JSON format). For example:

```
chris@vulcan: ~$ cat ~/.i3/app-icons.json
{
    "firefox": "firefox",
    "chromium-browser": "chrome",
    "chrome": "chrome",
    "google-chrome": "chrome",
    "x-terminal-emulator": "terminal",
    "thunderbird": "envelope",
    "jetbrains-idea-ce": "edit",
    "nautilus": "folder-open",
    "clementine": "music",
    "vlc": "play",
    "signal": "comment",
    "_no_match": "question",
}
```

where the key is the name of the i3-window (ie. what is shown in the i3-bar when it is not configured yet) and  the value is the font-awesome icon name you want to show instead, see [picking icons](#picking-icons).

Note: the hard-coded list above is used if you don't add this icon-config file.

### matching windows

You can debug windows names with `xprop`

Windows names are detected by inspecting in the following priority
- name
- title
- instance
- class

If there is no window name available a question mark is shown instead.

Another (simpler) way for debugging window names is running this script with `-v` or `--verbose` flag, it is suggested to use a terminal emulator that supports unicode (eg. kitty or urxvt)

### unrecognised windows

If a window is not in the icon config then by default the window title will be displayed instead.

The maximum length of the displayed window title can be set with the command line argument `--max_title_length` or `-l`.

To show a specific icon in place of unrecognised windows, specify an icon for window `_no_match` in the icon config.
If you want to show only that icon (hiding the name) then use the `--no-match-not-show-name` or `-n` option.

To hide all unknown applications, use the `--ignore-unknown` or `-i` option.

### picking icons 

The easiest way to pick an icon is to search for one in the [gallery](https://origin.fontawesome.com/icons?d=gallery). **NB: the "pro" icons are not available in the debian package.**

### windows delimiter

The window delimiter can be specified with `-d` or `--delimiter` parameter by default it is `|`.

### more icons with pango

As the i3bar supports [pango markup](https://developer.gnome.org/pygtk/stable/pango-markup-language.html), you can use almost all (icon-)fonts available on your system.
Custom text can be used instead of icons too.
All icon definitions starting with the `<` character will be interpreted as pango markup.

To check which fonts are available for use in pango, run the command
```
pango-list
```

To test if you properly installed all required fonts and the markup is valid, you can use the following command:
```bash
echo -e '<span font_desc="file-icons">\ue926</span>' | pango-view --markup /dev/stdin
```

It should render the markup correctly. If not, you need to check your font installation.

#### example: firefox & emacs

<img src="https://user-images.githubusercontent.com/1242917/80286549-5b66dc80-872c-11ea-8d3a-db1488ff299c.png"></img>

The following example displays an emacs icon for all instances of emacs and the text "FF" in red for every firefox instance.
The emacs icon requires the `file-icons` font to be installed.

```json
{
    "firefox": "<span foreground=\"red\">FF</span>",
    "emacs": "<span font_desc=\"file-icons\">\ue926</span>"
}
```

### dynamic icon titles with `transform_title`

Some applications display the title of the current project in the window title to differentiate between multiple instances.
This information can be displayed in the i3bar by using the `transform_title` directive.

Instead of a single string for the icon definition, use a json object as the property. 
For the title transformation the property `transform_title` is required.

#### `from`

The `from` property defines a regex which must match the title of the window.
If the window title is not matched, no output will be shown.
To match any window title, use `.*` as the value.
Use capturing groups (`()`) to capture strings, which you can use in the transformation (as `\1`, `\2`, `\3`, …).
Remember to escape backslashes with another backslash.

#### `to`

The string that will be displayed.
You can use strings that were matched by capturing groups in the `from` regex.

#### `compress`

Enables shortening the resulting displayed strings in a more recognizable name.
The name is split into groups of alphanumeric strings, which are all cut to a length of 3 and joined together using the adjacent separator in the original string.
Example: `i3-workspace_names+daemon` → `i3-wor_nam+dae`

#### example: emacs project title

<img src="https://user-images.githubusercontent.com/1242917/80287066-91f22680-872f-11ea-93ec-ddaab989cfab.png"></img>

Emacs displays the current project in brackets (`[<project name>]: <file name>`).
The project name can be matched by the capturing group in this regex: `".*\\[(.+?)\\].*"`.
Only the project name is shown as a result of the `to` property.

```json
"emacs": {
  "transform_title": {
    "from": ".*\\[(.+?)\\].*",
    "to": "\\1",
    "compress": true
  },
  "icon": "<span font_desc=\"file-icons\">\ue926</span>"
}
```
