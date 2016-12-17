export PS1="\! [\u@\h \w]\\$ "

alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'
alias ll='ls -l'
alias la='ls -al'

function cdls() {
    \cd $1;
    ls;
}

alias showhidden='defaults write com.apple.finder AppleShowAllFiles TRUE'
alias unshowhidden='defaults write com.apple.finder AppleShowAllFiles FALSE'

# Source local file.
if [[ -s "$HOME/.bashrc.local" ]]; then
    source "$HOME/.bashrc.local"
fi
