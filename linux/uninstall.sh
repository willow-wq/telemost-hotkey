#!/bin/sh
set -eu
autostart=${XDG_CONFIG_HOME:-"$HOME/.config"}/autostart
rm -f -- "$autostart/telemost-right-shift.desktop"
echo 'Autostart removed. To stop a terminal instance, press Ctrl+C; otherwise log out. Files were kept.'
