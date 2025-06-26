# ============================================================================
# Zsh Configuration File
# ============================================================================
#
# 概要: 対話セッション開始時に実行される設定
#
# 主な機能:
#   - 高度な履歴管理 (50,000エントリ、重複除去、タイムスタンプ)
#   - fzf統合 (履歴・ファイル・ディレクトリ検索)
#   - 強化された補完システム (メニュー選択、色付き表示)
#   - zplugによるプラグイン管理
#
# インストール要件:
#   - fzf
#   - zplug: 自動インストールプロンプトあり
#
# キーバインド:
#   Ctrl+R: 履歴検索 (fzf)
#   Ctrl+T: ファイル検索 (fzf)
#   Ctrl+F: ディレクトリ検索 + 移動 (fzf)
#   ↑/↓:   部分一致履歴検索 (zsh-history-substring-search)
#   →:     自動提案受け入れ (zsh-autosuggestions)
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com> (original template)
# ============================================================================

# History Configuration
export HISTFILE=${HOME}/.zsh_history
export HISTSIZE=50000
export SAVEHIST=50000
setopt hist_ignore_all_dups    # 重複するコマンドを無視
setopt share_history           # セッション間でhistoryを共有
setopt EXTENDED_HISTORY        # タイムスタンプも記録
setopt hist_ignore_space       # スペースで始まるコマンドは記録しない
setopt hist_reduce_blanks      # 余分な空白を削除
setopt hist_no_store           # historyコマンド自体は記録しない
setopt inc_append_history      # コマンド実行後すぐに追記

# ============================================================================
# fzf - Fuzzy Finder Integration
# ============================================================================
#
# 機能:
#   Ctrl+R: 履歴をfuzzy検索 (プレビュー付き、リアルタイム絞り込み)
#   Ctrl+T: ファイルをfuzzy検索 (ファイル内容のプレビュー付き)
#   Ctrl+F: ディレクトリをfuzzy検索してcd移動
#
if type fzf > /dev/null 2>&1; then
    # 履歴検索 (Ctrl+R)
    # 使い方: Ctrl+Rを押して文字を入力、↑↓で選択、Enterで実行
    function fzf-history-search() {
        local selected
        selected=$(history -rn 1 | fzf --query="$LBUFFER" --height=40% --reverse --border)
        if [[ -n "$selected" ]]; then
            BUFFER="$selected"
            CURSOR=$#BUFFER
        fi
        zle clear-screen
    }

    zle -N fzf-history-search
    bindkey '^R' fzf-history-search

    # ファイル検索 (Ctrl+T)
    # 使い方: Ctrl+Tでファイル選択、選択したファイルパスがコマンドラインに挿入
    # 例: vim <Ctrl+T> → vim ./path/to/selected/file.txt
    function fzf-file-widget() {
        local selected
        selected=$(find . -type f 2>/dev/null | fzf --height=40% --reverse --border --preview='head -100 {}')
        if [[ -n "$selected" ]]; then
            LBUFFER="${LBUFFER}${selected}"
        fi
        zle clear-screen
    }

    zle -N fzf-file-widget
    bindkey '^T' fzf-file-widget

    # ディレクトリ検索 + 移動 (Ctrl+F)
    # 使い方: Ctrl+Fでディレクトリ選択、選択したディレクトリに自動でcd
    function fzf-cd-widget() {
        local selected
        selected=$(find . -type d 2>/dev/null | fzf --height=40% --reverse --border)
        if [[ -n "$selected" ]]; then
            cd "$selected"
            zle reset-prompt
        fi
        zle clear-screen
    }

    zle -N fzf-cd-widget
    bindkey '^F' fzf-cd-widget

else
    echo "🚨 fzfがインストールされていません。高機能な検索のためにインストールを推奨します。"
    echo "インストールコマンド: brew install fzf"
    echo ""
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

# ============================================================================
# 補完システム設定
# ============================================================================
#
# 機能:
#   - メニュー選択補完 (Tab/矢印キーで候補選択)
#   - 大文字小文字を区別しない補完
#   - 色付き補完表示 (ファイルタイプに応じた色分け)
#   - 補完キャッシュによる高速化
#   - プロセス名補完の改善
#
# 使い方:
#   - Tab: 補完開始/次の候補
#   - Shift+Tab: 前の候補
#   - ↑↓←→: 補完メニュー内での移動
#   - Enter: 選択確定
#   - Ctrl+G: 補完キャンセル
#
autoload -Uz compinit
compinit -u  # セキュリティチェックをスキップして高速化

# 基本的な補完設定
zstyle ':completion:*' menu select                    # 補完候補をメニューで選択
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'   # 大文字小文字を区別しない
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS} # ファイル補完に色を付ける
zstyle ':completion:*' group-name ''                  # グループ名を表示しない
zstyle ':completion:*' verbose yes                    # 詳細な補完情報を表示
zstyle ':completion:*:descriptions' format '%B%d%b'   # 説明をボールドで表示
zstyle ':completion:*:warnings' format 'No matches for: %d' # マッチしない場合
zstyle ':completion:*' squeeze-slashes true           # 連続するスラッシュを1つに

# パフォーマンス向上のための補完キャッシュ
zstyle ':completion:*' use-cache yes
zstyle ':completion:*' cache-path ~/.zsh/cache

# プロセス名補完の改善 (kill コマンドなどで便利)
zstyle ':completion:*:processes' command 'ps -eo pid,user,comm'
zstyle ':completion:*:*:kill:*' menu yes select
zstyle ':completion:*:kill:*' force-list always

# ============================================================================
# zplug - プラグイン管理
# ============================================================================
#
# 導入されるプラグイン:
#   - zsh-autosuggestions: 履歴に基づくコマンド自動提案 (→キーで補完)
#   - zsh-syntax-highlighting: コマンドラインのシンタックスハイライト
#   - zsh-completions: 追加の補完定義
#   - zsh-history-substring-search: 部分文字列での履歴検索 (↑↓キー)
#   - pure: ミニマルなプロンプトテーマ
#
# インストール:
#   curl -sL --proto-redir -all,https https://raw.githubusercontent.com/zplug/installer/master/installer.zsh | zsh
#
# 使い方:
#   - →キー: 自動提案を受け入れ
#   - ↑↓キー: 入力中の文字列で履歴を部分検索
#   - コマンド入力中: リアルタイムでシンタックスハイライト
#
if type zplug > /dev/null 2>&1; then
    zplug "zsh-users/zsh-autosuggestions"              # コマンド自動提案
    zplug "mafredri/zsh-async", from:github            # 非同期処理用
    zplug "sindresorhus/pure", use:pure.zsh, from:github, as:theme  # ミニマルテーマ
    zplug "zsh-users/zsh-syntax-highlighting"          # シンタックスハイライト
    zplug "zsh-users/zsh-completions"                  # 追加補完定義
    zplug "zsh-users/zsh-history-substring-search"    # 履歴のsubstring検索

    # 未インストールプラグインの自動インストール
    if ! zplug check --verbose; then
        printf "Install missing plugins? [y/N]: "
        if read -q; then
            echo; zplug install
        fi
    fi

    # プラグイン読み込み
    zplug load

    # zsh-history-substring-search のキーバインド設定
    # ↑↓キーで入力中の文字列に基づく履歴検索
    if zplug check "zsh-users/zsh-history-substring-search"; then
        bindkey '^[[A' history-substring-search-up    # ↑キー
        bindkey '^[[B' history-substring-search-down  # ↓キー
    fi

    # zsh-autosuggestions の見た目設定
    if zplug check "zsh-users/zsh-autosuggestions"; then
        ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=240'              # 薄いグレーで表示
        ZSH_AUTOSUGGEST_STRATEGY=(history completion)        # 履歴と補完から提案
    fi
else
    echo "zplugがインストールされていません。高機能なzsh環境のために導入を推奨します。"
    echo "インストールコマンド:"
    echo "curl -sL --proto-redir -all,https https://raw.githubusercontent.com/zplug/installer/master/installer.zsh | zsh"
fi

