# Source Prezto.
if [[ -s "${ZDOTDIR:-$HOME}/.zprezto/runcoms/zprofile" ]]; then
    source "${ZDOTDIR:-$HOME}/.zprezto/runcoms/zprofile"
fi

# private
eval "$(rbenv init -)"
export PATH="/usr/local/sbin:/Applications/Macvim.app/Contents/MacOS:$PATH"
