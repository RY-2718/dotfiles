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

# 一時作業用コマンド http://bit.ly/22GF66y
tmpspace() {
    (
    d=$(mktemp -d "${TMPDIR:-/tmp}/${1:-tmpspace}.XXXXXXXXXX") && cd "$d" || exit 1
    "$SHELL"
    s=$?
    if [[ $s == 0 ]]; then
        rm -rf "$d"
    else
        echo "Directory '$d' still exists." >&2
    fi
    exit $s
    )
}

# typoで補完が出てこないのもストレスなのでaliasも作っておくことにした
alias tempspace=tmpspace
