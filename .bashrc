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

alias sshsirius='ssh ex1494@sirius.am.ics.keio.ac.jp'
alias vba_m='wine ~/Dropbox/GBA/VisualBoyAdvanceM1206/VisualBoyAdvance-M.exe'
alias gba='vba_m'
alias showhidden='defaults write com.apple.finder AppleShowAllFiles TRUE'
alias unshowhidden='defaults write com.apple.finder AppleShowAllFiles FALSE'
#alias logbook='~/applications/logbook/logbook.sh'
alias braban='wine C:\\Program\ Files\\YUZUSOFT\\ぶらばん！\\ぶらばん！.exe'
alias sshjikken='ssh j132441r@131.113.100.213'
