export PS1="\! [\u@\h \w]\\$ "

function cdls() {
    \cd $1;
    ls;
}

# Source local file.
if [[ -s "$HOME/.bashrc.local" ]]; then
    source "$HOME/.bashrc.local"
fi

# Source aliases file
if [[ -s "$HOME/.aliases" ]]; then
    source "$HOME/.aliases"
fi
