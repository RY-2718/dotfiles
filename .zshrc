#
# Executes commands at the start of an interactive session.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

# Customize to your needs...

# History
export HISTFILE=${HOME}/.zsh_history
export HISTSIZE=100000000
export SAVEHIST=100000000
setopt hist_ignore_all_dups
setopt share_history
setopt EXTENDED_HISTORY
bindkey "^R" history-incremental-search-backward
bindkey "^S" history-incremental-search-forward

# peco
function peco-history-selection() {
    local tac
    if which tac > /dev/null; then
        tac="tac"
    else
        tac="tail -r"
    fi

    BUFFER=$(\history -n 1 | \
        eval $tac | \
        peco --query "$LBUFFER")
    CURSOR=$#BUFFER
    zle clear-screen
}

zle -N peco-history-selection

if type peco 2>&1 > /dev/null; then
    bindkey '^R' peco-history-selection
fi

# additional setting
setopt no_beep
setopt nonomatch

# personal
echo -ne "\033]0;$(pwd | rev | awk -F \/ '{print "/"$1"/"$2}'| rev)\007"
function chpwd() { echo -ne "\033]0;$(pwd | rev | awk -F \/ '{print "/"$1"/"$2}'| rev)\007"}

# grep color
export GREP_COLOR="34;47"
export GREP_COLORS="mt=34;47"

# PATH settings
if [ -d $HOME/bin ]; then
    export PATH=$HOME/bin:$PATH
fi

# Source local file.
if [[ -s "$HOME/.zshrc_local" ]]; then
    source "$HOME/.zshrc_local"
fi

# Source aliases file
if [[ -s "$HOME/.aliases" ]]; then
    source "$HOME/.aliases"
fi

# 一時作業用コマンド http://bit.ly/22GF66y
tmpspace() {
    (
    d=$(mktemp -d "${TMPDIR:-/tmp}/${1:-tmpspace}.XXXXXXXXXX") && cd "$d" || exit 1
    "$SHELL"
    s=$?
    if [[ $s == 0 ]]; then
        \rm -rf "$d"
    else
        echo "Directory '$d' still exists." >&2
    fi
    exit $s
    )
}

# typoで補完が出てこないのもストレスなのでaliasも作っておくことにした
alias tempspace=tmpspace

# zplugがインストールされていない場合はインストールを促す
if type zplug 2>&1 > /dev/null; then
    zplug "zsh-users/zsh-autosuggestions"
    zplug "mafredri/zsh-async", from:github
    zplug "sindresorhus/pure", use:pure.zsh, from:github, as:theme
    zplug "zsh-users/zsh-syntax-highlighting"
	if ! zplug check --verbose; then
	    printf "Install? [y/N]: "
	    if read -q; then
	        echo; zplug install
	    fi
	fi
	zplug load --verbose
else
    echo "Please install zplug!"
fi

