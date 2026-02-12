#!/bin/bash

if [ -z "$TMUX" ]; then
    echo "tmux session required" >&2
    exit 1
fi

dry_run=0
sudo_args=()
for arg in "$@"; do
    case "$arg" in
        -n|--dry-run) dry_run=1 ;;
        *) sudo_args+=("$arg") ;;
    esac
done

# Pick a user interactively.
USERS=(
    dev
    ops
    admin
)
user=$(printf '%s\n' "${USERS[@]}" | fzf --prompt='user> ')
if [ -z "$user" ]; then
    echo "user not selected" >&2
    exit 1
fi

case "$user" in
    dev) color='#25333a' ;;
    *)   color='#261a1c' ;;
esac

if [ -n "$TMUX" ]; then
    tmux select-pane -P "bg=$color"
fi

if [ "$dry_run" -eq 1 ]; then
    echo "dry-run: user=$user"
    echo "dry-run: pane bg=$color"
    echo "dry-run: sudo -u \"$user\" -i ${sudo_args[*]}"
    sleep 1
else
    sudo -u "$user" -i "${sudo_args[@]}"
fi

if [ -n "$TMUX" ]; then
    tmux select-pane -P 'bg=default'
fi
