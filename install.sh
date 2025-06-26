#!/bin/bash

# ============================================================================
# 安全なdotfilesインストールスクリプト
# ============================================================================

set -euo pipefail  # エラー時即座に終了、未定義変数使用禁止、パイプエラー検出

# ============================================================================
# 設定と定数
# ============================================================================

# スクリプトの基本設定
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly BACKUP_DIR="$HOME/.dotfiles_backup_$(date +%Y%m%d_%H%M%S)"
readonly LOG_FILE="$SCRIPT_DIR/install.log"

# 色付きメッセージ用の定数
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# ============================================================================
# ログ・メッセージ関数
# ============================================================================

# 基本ログ関数（タイムスタンプ付き）
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
}

# ============================================================================
# ユーティリティ関数
# ============================================================================

# ユーザーに Y/n の確認を求める関数
ask_user_confirmation() {
    local message="$1"
    local default_yes="${2:-false}"

    if [[ "$default_yes" == true ]]; then
        echo -n "$message [Y/n]: "
    else
        echo -n "$message [y/N]: "
    fi

    read -r response

    case "$response" in
        [yY]|[yY][eE][sS])
            return 0  # Yes
            ;;
        [nN]|[nN][oO])
            return 1  # No
            ;;
        "")
            # デフォルト値を使用
            if [[ "$default_yes" == true ]]; then
                return 0  # Yes
            else
                return 1  # No
            fi
            ;;
        *)
            # 無効な入力の場合は再度確認
            warning "無効な入力です。y/n または Y/N で回答してください。"
            ask_user_confirmation "$message" "$default_yes"
            ;;
    esac
}

check_dependencies() {
    local missing_deps=()

    # 必須コマンドのリスト
    local required_commands=("ln" "cp" "mkdir" "date")

    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_deps+=("$cmd")
        fi
    done

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        error "必須コマンドが不足しています: ${missing_deps[*]}"
        return 1
    fi

    success "依存関係チェック完了"
}

# バックアップディレクトリの作成
create_backup_dir() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        mkdir -p "$BACKUP_DIR"
        info "バックアップディレクトリ作成: $BACKUP_DIR"
    fi
}

# 既存ファイルのバックアップ
backup_file() {
    local file="$1"
    local target="$HOME/$file"

    if [[ -e "$target" ]]; then
        cp -p "$target" "$BACKUP_DIR/"
        info "バックアップ: $file"
        return 0
    fi
    return 1
}

# ============================================================================
# シンボリックリンク管理
# ============================================================================

# シンボリックリンクの状態を判定
#
# 引数:
#   $1 - ソースファイルのパス
#
# 戻り値:
#   0: 既に正しいリンクが存在 (スキップ)
#   1: 既存のシンボリックリンクを置換 (更新)
#   2: 通常ファイル/ディレクトリを置換 (バックアップ)
#   3: ファイルが存在しない (新規作成)
check_symlink_status() {
    local source="$1"
    local target="$HOME/$(basename "$source")"

    if [[ -L "$target" ]]; then
        # シンボリックリンクのリンク先を取得
        local current_target="$(readlink "$target")"

        # 既に同じリンク先を指している場合
        if [[ "$current_target" == "$source" ]]; then
            return 0  # スキップ
        else
            return 1  # 更新
        fi
    elif [[ -e "$target" ]]; then
        return 2  # バックアップ
    else
        return 3  # 新規作成
    fi
}

# シンボリックリンクの作成
create_symlink() {
    local source="$1"
    local target="$HOME/$(basename "$source")"
    local basename_file="$(basename "$source")"
    local interactive="${2:-false}"

    # ソースファイルの存在確認
    if [[ ! -e "$source" ]]; then
        error "ソースファイルが存在しません: $source"
        return 1
    fi

    # 状態をチェック
    check_symlink_status "$source"
    local status=$?

    case $status in
        0)  # スキップ
            info "スキップ: $basename_file (既に正しいリンクが存在)"
            return 0
            ;;
        1)  # 更新
            local current_target="$(readlink "$target")"
            info "既存リンクの更新対象: $basename_file ($(basename "$current_target") -> $basename_file)"

            # インタラクティブモードの場合は確認
            if [[ "$interactive" == true ]]; then
                if ! ask_user_confirmation "既存のシンボリックリンク $basename_file を更新しますか？" true; then
                    info "スキップ: $basename_file (ユーザーが拒否)"
                    return 0
                fi
            fi

            backup_file "$basename_file"
            rm -f "$target"
            ;;
        2)  # バックアップ
            info "既存ファイルのバックアップ対象: $basename_file"

            # インタラクティブモードの場合は確認
            if [[ "$interactive" == true ]]; then
                if ! ask_user_confirmation "既存ファイル $basename_file をバックアップして置き換えますか？" true; then
                    info "スキップ: $basename_file (ユーザーが拒否)"
                    return 0
                fi
            fi

            backup_file "$basename_file"
            rm -f "$target"
            ;;
        3)  # 新規作成
            if [[ "$interactive" == true ]]; then
                info "新規作成対象: $basename_file"
                if ! ask_user_confirmation "新しいシンボリックリンク $basename_file を作成しますか？" true; then
                    info "スキップ: $basename_file (ユーザーが拒否)"
                    return 0
                fi
            fi
            ;;
    esac

    # シンボリックリンク作成
    if ln -sf "$source" "$target"; then
        success "リンク作成: $basename_file"
    else
        error "リンク作成失敗: $basename_file"
        return 1
    fi
}

# ============================================================================
# テンプレートディレクトリ管理
# ============================================================================

# テンプレートディレクトリのコピー
copy_template_dir() {
    local dir_name="$1"
    local source="$SCRIPT_DIR/template/$dir_name"
    local target="$HOME/$dir_name"

    if [[ ! -d "$source" ]]; then
        warning "テンプレートディレクトリが存在しません: $source"
        return 1
    fi

    if [[ -e "$target" ]]; then
        info "$target は既に存在します（スキップ）"
        return 0
    fi

    if cp -r "$source" "$target"; then
        success "ディレクトリコピー: $dir_name"
    else
        error "ディレクトリコピー失敗: $dir_name"
        return 1
    fi
}

# ============================================================================
# メインインストール処理
# ============================================================================

# dotfilesのインストール
install_dotfiles() {
    local dotfiles=()
    local failed_files=()
    local interactive="${1:-false}"

    # dotfilesファイルリストを取得（除外ファイルを除く）
    while IFS= read -r -d '' file; do
        local basename_file="$(basename "$file")"

        # 除外ファイルをスキップ
        case "$basename_file" in
            ".git"|".DS_Store"|".gitignore"|".gitmodules"|"install.sh")
                continue
                ;;
            "CLAUDE.md")
                # リポジトリルートの CLAUDE.md は除外、.claude/CLAUDE.md は対象
                if [[ "$file" == "$SCRIPT_DIR/CLAUDE.md" ]]; then
                    continue
                else
                    dotfiles+=("$file")
                fi
                ;;
            *)
                dotfiles+=("$file")
                ;;
        esac
    done < <(find "$SCRIPT_DIR" -maxdepth 1 -name '.*' -type f -print0)

    info "dotfilesインストール開始 (${#dotfiles[@]}個のファイル)"

    if [[ "$interactive" == true ]]; then
        info "インタラクティブモード: ファイルごとに確認します"
    fi

    # 各dotfileのシンボリックリンクを作成
    for file in "${dotfiles[@]}"; do
        if ! create_symlink "$file" "$interactive"; then
            failed_files+=("$(basename "$file")")
        fi
    done

    if [[ ${#failed_files[@]} -gt 0 ]]; then
        error "失敗したファイル: ${failed_files[*]}"
        return 1
    fi

    success "全dotfilesのインストール完了"
}

# テンプレートディレクトリのインストール
install_template_dirs() {
    local template_dirs=("bin" "opt" "tools")
    local failed_dirs=()

    info "テンプレートディレクトリインストール開始"

    for dir in "${template_dirs[@]}"; do
        if ! copy_template_dir "$dir"; then
            failed_dirs+=("$dir")
        fi
    done

    if [[ ${#failed_dirs[@]} -gt 0 ]]; then
        warning "失敗したディレクトリ: ${failed_dirs[*]}"
    fi

    success "テンプレートディレクトリインストール完了"
}

# ============================================================================
# ロールバック機能
# ============================================================================

# バックアップからの復元
rollback() {
    local specified_backup_dir="$1"
    local target_backup_dir

    if [[ -n "$specified_backup_dir" ]]; then
        # 指定されたバックアップディレクトリを使用
        if [[ ! -d "$specified_backup_dir" ]]; then
            error "指定されたバックアップディレクトリが見つかりません: $specified_backup_dir"
            return 1
        fi
        target_backup_dir="$specified_backup_dir"
    else
        # 最新のバックアップディレクトリを自動検索
        target_backup_dir=$(find "$HOME" -maxdepth 1 -name ".dotfiles_backup_*" -type d | sort -r | head -1)

        if [[ -z "$target_backup_dir" ]]; then
            error "バックアップディレクトリが見つかりません"
            info "利用可能なバックアップディレクトリ:"
            find "$HOME" -maxdepth 1 -name ".dotfiles_backup_*" -type d | sort -r || echo "なし"
            return 1
        fi

        info "最新のバックアップを使用: $(basename "$target_backup_dir")"
    fi

    warning "ロールバックを実行します..."
    warning "この操作により現在のdotfilesが上書きされます"
    info "復元元: $target_backup_dir"

    # 確認プロンプト
    echo -n "本当にロールバックしますか? [y/N]: "
    read -r response
    case "$response" in
        [yY]|[yY][eE][sS])
            info "ロールバックを開始します"
            ;;
        *)
            info "ロールバックをキャンセルしました"
            return 0
            ;;
    esac

    local restored_count=0

    # バックアップファイルを復元
    for backup_file in "$target_backup_dir"/*; do
        if [[ -f "$backup_file" ]]; then
            local filename="$(basename "$backup_file")"
            if cp "$backup_file" "$HOME/$filename"; then
                info "復元: $filename"
                ((restored_count++))
            else
                error "復元失敗: $filename"
            fi
        fi
    done

    if [[ $restored_count -gt 0 ]]; then
        success "ロールバック完了 ($restored_count個のファイルを復元)"
    else
        warning "復元されたファイルがありません"
    fi
}

# ============================================================================
# ヘルプ・ユーティリティ
# ============================================================================

# 使用方法表示
show_help() {
    cat << EOF
使用方法: $0 [オプション]

オプション:
    -h, --help          このヘルプを表示
    -f, --force         確認なしで実行
    -i, --interactive   ファイルごとに個別に確認
    -d, --dry-run       実際の処理を行わずにプレビューのみ
    --rollback [DIR]    バックアップからロールバック (DIR省略時は最新を使用)

説明:
    このスクリプトはdotfilesを安全にインストールします。
    既存ファイルは自動的にバックアップされます。
    
    注意: -f (--force) を指定しない場合、デフォルトで各ファイルの処理前に確認を求めます。

バックアップ場所: ~/.dotfiles_backup_YYYYMMDD_HHMMSS/
ログファイル: $SCRIPT_DIR/install.log

EOF
}

# ドライラン機能
dry_run() {
    info "=== ドライランモード ==="

    local skip_count=0
    local update_count=0
    local backup_count=0
    local create_count=0

    # dotfilesのチェック
    while IFS= read -r -d '' file; do
        local basename_file="$(basename "$file")"

        case "$basename_file" in
            ".git"|".DS_Store"|".gitignore"|".gitmodules"|"install.sh")
                continue
                ;;
            "CLAUDE.md")
                # リポジトリルートの CLAUDE.md は除外、.claude/CLAUDE.md は対象
                if [[ "$file" == "$SCRIPT_DIR/CLAUDE.md" ]]; then
                    continue
                fi
                # .claude/CLAUDE.md の場合は通常処理に進む

                check_symlink_status "$file"
                local status=$?

                case $status in
                    0)  # スキップ
                        echo "[SKIP] $basename_file (既に正しいリンクが存在)"
                        ((skip_count++))
                        ;;
                    1)  # 更新
                        local current_target="$(readlink "$HOME/$basename_file")"
                        echo "[UPDATE] $basename_file (リンク先変更: $(basename "$current_target") -> $basename_file)"
                        ((update_count++))
                        ;;
                    2)  # バックアップ
                        echo "[BACKUP] $basename_file (既存ファイルをバックアップして置換)"
                        ((backup_count++))
                        ;;
                    3)  # 新規作成
                        echo "[CREATE] $basename_file (新規リンク作成)"
                        ((create_count++))
                        ;;
                esac
                ;;
            *)
                # 同じ判定ロジックを使用
                check_symlink_status "$file"
                local status=$?

                case $status in
                    0)  # スキップ
                        echo "[SKIP] $basename_file (既に正しいリンクが存在)"
                        ((skip_count++))
                        ;;
                    1)  # 更新
                        local current_target="$(readlink "$HOME/$basename_file")"
                        echo "[UPDATE] $basename_file (リンク先変更: $(basename "$current_target") -> $basename_file)"
                        ((update_count++))
                        ;;
                    2)  # バックアップ
                        echo "[BACKUP] $basename_file (既存ファイルをバックアップして置換)"
                        ((backup_count++))
                        ;;
                    3)  # 新規作成
                        echo "[CREATE] $basename_file (新規リンク作成)"
                        ((create_count++))
                        ;;
                esac
                ;;
        esac
    done < <(find "$SCRIPT_DIR" -maxdepth 1 -name '.*' -type f -print0)

    # テンプレートディレクトリのチェック
    local template_dirs=("bin" "opt" "tools")
    local template_skip=0
    local template_copy=0

    for dir in "${template_dirs[@]}"; do
        if [[ -d "$SCRIPT_DIR/template/$dir" ]]; then
            if [[ -e "$HOME/$dir" ]]; then
                echo "[SKIP] $dir (既に存在)"
                ((template_skip++))
            else
                echo "[COPY] $dir (新規作成)"
                ((template_copy++))
            fi
        fi
    done

    echo
    info "=== 処理概要 ==="
    echo "dotfiles:"
    echo "  スキップ: $skip_count個"
    echo "  更新: $update_count個"
    echo "  バックアップ: $backup_count個"
    echo "  新規作成: $create_count個"
    echo "テンプレートディレクトリ:"
    echo "  スキップ: $template_skip個"
    echo "  コピー: $template_copy個"

    info "=== ドライラン完了 ==="
}

# ============================================================================
# メイン処理
# ============================================================================

# メイン関数
main() {
    local force=false
    local dry_run_mode=false
    local rollback_mode=false
    local interactive=false
    local rollback_dir=""

    # 引数解析
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -f|--force)
                force=true
                shift
                ;;
            -d|--dry-run)
                dry_run_mode=true
                shift
                ;;
            -i|--interactive)
                interactive=true
                shift
                ;;
            --rollback)
                rollback_mode=true
                shift
                # 次の引数がバックアップディレクトリのパスかチェック
                if [[ $# -gt 0 && ! "$1" =~ ^- ]]; then
                    rollback_dir="$1"
                    shift
                fi
                ;;
            *)
                error "不明なオプション: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # ログファイル初期化
    : > "$LOG_FILE"

    info "=== dotfilesインストールスクリプト開始 ==="
    log "スクリプトディレクトリ: $SCRIPT_DIR"
    log "ホームディレクトリ: $HOME"

    # ロールバックモード
    if [[ "$rollback_mode" == true ]]; then
        rollback "$rollback_dir"
        exit $?
    fi

    # 依存関係チェック
    if ! check_dependencies; then
        exit 1
    fi

    # ドライランモード
    if [[ "$dry_run_mode" == true ]]; then
        dry_run
        exit 0
    fi

    # 確認プロンプト
    if [[ "$force" != true ]]; then
        echo
        info "以下の処理を実行します:"
        echo "  1. 既存dotfilesのバックアップ"
        echo "  2. dotfilesのシンボリックリンク作成"
        echo "  3. テンプレートディレクトリのコピー"
        echo
        echo -n "続行しますか? [y/N]: "
        read -r response
        case "$response" in
            [yY]|[yY][eE][sS])
                info "インストールを開始します"
                ;;
            *)
                info "インストールをキャンセルしました"
                exit 0
                ;;
        esac
    fi

    # バックアップディレクトリ作成
    create_backup_dir

    # インタラクティブモードの決定（forceが指定されていない場合はinteractiveをデフォルトに）
    if [[ "$force" != true && "$interactive" != true ]]; then
        interactive=true
    fi

    # メイン処理実行
    local exit_code=0

    if ! install_dotfiles "$interactive"; then
        error "dotfilesインストールでエラーが発生しました"
        exit_code=1
    fi

    if ! install_template_dirs; then
        warning "一部のテンプレートディレクトリでエラーが発生しました"
    fi

    if [[ $exit_code -eq 0 ]]; then
        success "=== インストール完了 ==="
        info "バックアップ: $BACKUP_DIR"
        info "ログファイル: $LOG_FILE"
        echo
        info "ロールバックするには: $0 --rollback [バックアップディレクトリ]"
    else
        error "=== インストール失敗 ==="
        info "ロールバックするには: $0 --rollback [バックアップディレクトリ]"
    fi

    exit $exit_code
}

# ============================================================================
# スクリプト実行
# ============================================================================

# エラー時のトラップ処理
trap 'error "スクリプトが予期しないエラーで終了しました"; exit 1' ERR

# スクリプト実行
main "$@"