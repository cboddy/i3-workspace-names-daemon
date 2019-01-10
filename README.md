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

If you use the ``$mod+1`` etc. shortcuts to switch workspaces then update the following so that the *switch to workspace* and *move focussed window to workspace* **shortcuts still work**. 


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
    "signal": "comment"
}
```

where the key is the name of the i3-window (ie. what is shown in the i3-bar when it is not configured yet) and  the value is the font-awesome icon name you want to show instead, see [picking icons](#picking-icons).

Note: the hard-coded list above is used if you don't add this icon-config file.

### picking icons 

The easiest way to pick an icon is to search for one in the [gallery](https://origin.fontawesome.com/icons?d=gallery). **NB: the "pro" icons are not available in the debian package.**

##### FAQ
https://pypi.org/project/i3-workspace-names-daemon/
