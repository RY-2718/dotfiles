#!/bin/bash

if [ -z "$TMUX" ]; then
    echo "tmux session required" >&2
    exit 1
fi

user="$1"
shift

case "$user" in
    dev) color='#1a1e26' ;;
    *)   color='#261a1c' ;;
esac

if [ -n "$TMUX" ]; then
    tmux select-pane -P "bg=$color"
fi

sudo -u "$user" -i "$@"

if [ -n "$TMUX" ]; then
    tmux select-pane -P 'bg=default'
fi
