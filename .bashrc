export PS1="\! [\u@\h \w]\\$ "

function cdls() {
    \cd $1;
    ls;
}

# Source local file.
if [[ -s "$HOME/.bashrc_local" ]]; then
    source "$HOME/.bashrc_local"
fi

# Source aliases file
if [[ -s "$HOME/.aliases" ]]; then
    source "$HOME/.aliases"
fi
