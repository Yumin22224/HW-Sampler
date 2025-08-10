#!/usr/bin/env bash
set -euo pipefail

export XDG_RUNTIME_DIR=/run/user/$(id -u)

# wayland 소켓 자동 감지 (wayland-0, wayland-1 등)
if compgen -G "$XDG_RUNTIME_DIR/wayland-*" > /dev/null; then
  export WAYLAND_DISPLAY=$(basename "$(ls "$XDG_RUNTIME_DIR"/wayland-* | head -n1)")
else
  echo "No wayland-* socket under $XDG_RUNTIME_DIR. Is weston running on tty1?"
  exit 1
fi

export SDL_VIDEODRIVER=wayland
exec python src/main.py
