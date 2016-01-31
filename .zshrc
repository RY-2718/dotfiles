#
# Executes commands at the start of an interactive session.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

# Source Prezto.
if [[ -s "${ZDOTDIR:-$HOME}/.zprezto/init.zsh" ]]; then
  source "${ZDOTDIR:-$HOME}/.zprezto/init.zsh"
fi

# Customize to your needs...

# fundamental alias
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'
alias ll='ls -l'
alias la='ls -al'

# History
export HISTFILE=${HOME}/.zsh_history
export HISTSIZE=1000
export SAVEHIST=100000
setopt hist_ignore_all_dups
setopt share_history
setopt EXTENDED_HISTORY
bindkey "^R" history-incremental-search-backward
bindkey "^S" history-incremental-search-forward

# peco
function peco-history-selection() {
    BUFFER=`history -n 1 | tail -r  | awk '!a[$0]++' | peco`
    CURSOR=$#BUFFER
    zle reset-prompt
}

zle -N peco-history-selection
bindkey '^R' peco-history-selection

# additional setting
setopt no_beep
setopt nonomatch

#vim
#alias vi=vim
alias vim='env_LANG=ja_JP.UTF-8 /Applications/MacVim.app/Contents/MacOS/Vim'
#alias vim='mvim -v'

#personal
alias sshua='ssh ua332994@logex02.educ.cc.keio.ac.jp'
alias sshsirius='ssh ex1494@sirius.am.ics.keio.ac.jp'
alias vba_m='wine ~/Dropbox/GBA/VisualBoyAdvanceM1206/VisualBoyAdvance-M.exe'
alias gba='vba_m'
alias showhidden='defaults write com.apple.finder AppleShowAllFiles TRUE'
alias unshowhidden='defaults write com.apple.finder AppleShowAllFiles FALSE'
#alias logbook='~/applications/logbook/logbook.sh'
alias braban='wine C:\\Program\ Files\\YUZUSOFT\\ぶらばん！\\ぶらばん！.exe'
alias sshjikken='ssh j132441r@131.113.100.213'
echo -ne "\033]0;$(pwd | rev | awk -F \/ '{print "/"$1"/"$2}'| rev)\007"
function chpwd() { echo -ne "\033]0;$(pwd | rev | awk -F \/ '{print "/"$1"/"$2}'| rev)\007"}
