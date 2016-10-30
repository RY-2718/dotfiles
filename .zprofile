# Source Prezto.
if [[ -s "${ZDOTDIR:-$HOME}/.zprezto/runcoms/zprofile" ]]; then
    source "${ZDOTDIR:-$HOME}/.zprezto/runcoms/zprofile"
fi

# Source local file.
if [[ -s "$HOME/.zprofile.local" ]]; then
    source "$HOME/.zprofile.local"
fi

echo "~/.zprofile"
