#!/bin/sh
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
helper=$script_dir/telemost_hotkey.py
test -f "$helper"
/usr/bin/python3 -c 'import sys, Xlib, pyatspi; sys.exit("Unsupported characters in project path." if any(chr(c) in sys.argv[1] for c in (10,13,34,36,92,96)) else 0)' "$helper"
autostart=${XDG_CONFIG_HOME:-"$HOME/.config"}/autostart
mkdir -p "$autostart"
# Escape percent field codes in desktop Exec values.
desktop_helper=$(printf '%s' "$helper" | sed 's/%/%%/g')
cat > "$autostart/telemost-right-shift.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Telemost Right Shift (experimental X11)
Exec=/usr/bin/python3 "$desktop_helper"
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
echo 'Autostart installed for this user. Log in again or run: /usr/bin/python3 telemost_hotkey.py'
