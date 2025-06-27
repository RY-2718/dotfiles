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
readonly BACKUP_DIR="${HOME}/.dotfiles_backup_$(date +%Y%m%d_%H%M%S)"
readonly LOG_FILE="${SCRIPT_DIR}/install.log"
readonly IGNORE_FILE="${SCRIPT_DIR}/.installignore"

# 一時ファイル管理
readonly TEMP_DIR="${SCRIPT_DIR}/.temp"
readonly TEMP_EXCLUDE_FILE="${TEMP_DIR}/exclude_list.txt"
readonly TEMP_FILES_LOG="${TEMP_DIR}/temp_files.log"

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
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${*}" | tee -a "${LOG_FILE}"
}

info() {
    echo -e "${BLUE}ℹ${NC} ${*}" | tee -a "${LOG_FILE}"
}

success() {
    echo -e "${GREEN}✓${NC} ${*}" | tee -a "${LOG_FILE}"
}

warning() {
    echo -e "${YELLOW}⚠${NC} ${*}" | tee -a "${LOG_FILE}"
}

error() {
    echo -e "${RED}✗${NC} ${*}" | tee -a "${LOG_FILE}"
}

# ============================================================================
# ユーティリティ関数
# ============================================================================

# 一時ディレクトリの初期化
init_temp_dir() {
    if [[ ! -d "${TEMP_DIR}" ]]; then
        mkdir -p "${TEMP_DIR}"
        info "一時ディレクトリ作成: ${TEMP_DIR}"
    fi

    # 一時ファイルログを初期化
    : > "${TEMP_FILES_LOG}"
}

# 一時ファイルを登録
register_temp_file() {
    local file="${1}"
    echo "${file}" >> "${TEMP_FILES_LOG}"
}

# 一時ファイルのクリーンアップ
cleanup_temp_files() {
    if [[ -f "${TEMP_FILES_LOG}" ]]; then
        while IFS= read -r temp_file; do
            if [[ -n "${temp_file}" && -f "${temp_file}" ]]; then
                rm -f "${temp_file}"
                log "一時ファイル削除: ${temp_file}"
            fi
        done < "${TEMP_FILES_LOG}"
    fi

    # 一時ディレクトリが空になったら削除
    if [[ -d "${TEMP_DIR}" ]] && [[ -z "$(ls -A "${TEMP_DIR}")" ]]; then
        rmdir "${TEMP_DIR}"
        info "一時ディレクトリ削除: ${TEMP_DIR}"
    fi
}

# クリーンアップ専用関数（外部から呼び出し可能）
cleanup() {
    info "クリーンアップ開始"
    cleanup_temp_files
    success "クリーンアップ完了"
}

# ユーザーに Y/n の確認を求める関数
ask_user_confirmation() {
    local message="${1}"
    local default_yes="${2:-false}"

    if [[ "${default_yes}" == true ]]; then
        echo -n "${message} [Y/n]: "
    else
        echo -n "${message} [y/N]: "
    fi

    read -r response

    case "${response}" in
        [yY]|[yY][eE][sS])
            return 0  # Yes
            ;;
        [nN]|[nN][oO])
            return 1  # No
            ;;
        "")
            # デフォルト値を使用
            if [[ "${default_yes}" == true ]]; then
                return 0  # Yes
            else
                return 1  # No
            fi
            ;;
        *)
            # 無効な入力の場合は再度確認
            warning "無効な入力です。y/n で回答してください。"
            ask_user_confirmation "${message}" "${default_yes}"
            ;;
    esac
}

check_dependencies() {
    local missing_deps=()

    # 必須コマンドのリスト
    local required_commands=("ln" "cp" "mkdir" "date")

    for cmd in "${required_commands[@]}"; do
        if ! command -v "${cmd}" >/dev/null 2>&1; then
            missing_deps+=("${cmd}")
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
    if [[ ! -d "${BACKUP_DIR}" ]]; then
        mkdir -p "${BACKUP_DIR}"
        info "バックアップ作成: ${BACKUP_DIR}"
    fi
}

# 既存ファイルのバックアップ
backup_file() {
    local file="${1}"
    local target="${HOME}/${file}"

    if [[ -e "${target}" ]]; then
        cp -p "${target}" "${BACKUP_DIR}/"
        info "バックアップ: ${file}"
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
    local source="${1}"
    local relative_path="${source#${SCRIPT_DIR}/}"
    local target="${HOME}/${relative_path}"

    if [[ -L "${target}" ]]; then
        # シンボリックリンクのリンク先を取得
        local current_target="$(readlink "${target}")"

        # 既に同じリンク先を指している場合
        if [[ "${current_target}" == "${source}" ]]; then
            return 0  # スキップ
        else
            return 1  # 更新
        fi
    elif [[ -e "${target}" ]]; then
        return 2  # バックアップ
    else
        return 3  # 新規作成
    fi
}

# シンボリックリンクの作成
create_symlink() {
    local source="${1}"
    local relative_path="${source#${SCRIPT_DIR}/}"
    local target="${HOME}/${relative_path}"
    local basename_file="$(basename "${source}")"
    local force="${2:-false}"

    # ソースファイルの存在確認
    if [[ ! -e "${source}" ]]; then
        error "ソースファイルが存在しません: ${source}"
        return 1
    fi

    # 状態をチェック
    check_symlink_status "${source}"
    local status=$?

    case $status in
        0)  # スキップ
            info "スキップ: ${relative_path} (既に正しいリンクが存在)"
            return 0
            ;;
        1)  # 更新
            local current_target="$(readlink "${target}")"
            info "既存リンクの更新対象: ${relative_path} ($(basename "${current_target}") -> ${basename_file})"

            # forceオプション指定時以外は確認
            if [[ "${force}" != true ]]; then
                if ! ask_user_confirmation "既存のシンボリックリンク ${relative_path} を更新しますか？" true; then
                    info "スキップ: ${relative_path}"
                    return 0
                fi
            fi

            backup_file "${relative_path}"
            rm -f "${target}"
            ;;
        2)  # バックアップ
            info "バックアップ: ${relative_path}"

            # forceオプション指定時以外は確認
            if [[ "${force}" != true ]]; then
                if ! ask_user_confirmation "既存ファイル ${relative_path} をバックアップして置き換えますか？" true; then
                    info "スキップ: ${relative_path}"
                    return 0
                fi
            fi

            backup_file "${relative_path}"
            rm -f "${target}"
            ;;
        3)  # 新規作成
            if [[ "${force}" != true ]]; then
                info "新規作成: ${relative_path}"
                if ! ask_user_confirmation "新しいシンボリックリンク ${relative_path} を作成しますか？" true; then
                    info "スキップ: ${relative_path}"
                    return 0
                fi
            fi
            ;;
    esac

    # シンボリックリンク作成
    # 親ディレクトリが存在しない場合は作成
    local target_dir="$(dirname "${target}")"
    if [[ ! -d "${target_dir}" ]]; then
        if mkdir -p "${target_dir}"; then
            info "ディレクトリ作成: ${target_dir#${HOME}/}"
        else
            error "ディレクトリ作成失敗: ${target_dir}"
            return 1
        fi
    fi

    if ln -sf "${source}" "${target}"; then
        success "作成: ${relative_path}"
    else
        error "作成失敗: ${relative_path}"
        return 1
    fi
}

# ============================================================================
# テンプレートディレクトリ管理
# ============================================================================

# テンプレートディレクトリのコピー
copy_template_dir() {
    local dir_name="${1}"
    local source="${SCRIPT_DIR}/template/${dir_name}"
    local target="${HOME}/${dir_name}"

    if [[ ! -d "${source}" ]]; then
        warning "テンプレートディレクトリが存在しません: ${source}"
        return 1
    fi

    if [[ -e "${target}" ]]; then
        info "${target} は既に存在します（スキップ）"
        return 0
    fi

    if cp -r "${source}" "${target}"; then
        success "コピー: ${dir_name}"
    else
        error "コピー失敗: ${dir_name}"
        return 1
    fi
}

# 除外ファイルリストを読み込む
load_exclude_list() {
    local exclude_list=()

    # デフォルトの除外ファイル
    exclude_list+=(".git" ".DS_Store" ".gitignore" ".gitmodules" "install.sh")

    # 外部除外ファイルが存在する場合は読み込み
    if [[ -f "${IGNORE_FILE}" ]]; then
        while IFS= read -r line; do
            # コメント行と空行をスキップ
            [[ "${line}" =~ ^[[:space:]]*# ]] && continue
            [[ -z "${line// }" ]] && continue

            # 行頭の空白を削除
            line="${line#"${line%%[! ]*}"}"
            exclude_list+=("${line}")
        done < "${IGNORE_FILE}"
        info "除外ファイル読み込み: ${IGNORE_FILE}"
    fi

    # 一時ファイルに出力
    printf '%s\n' "${exclude_list[@]}" > "${TEMP_EXCLUDE_FILE}"
    register_temp_file "${TEMP_EXCLUDE_FILE}"

    # 一時ファイルのパスを返す
    echo "${TEMP_EXCLUDE_FILE}"
}

# ファイルが除外リストに含まれているかチェック
is_excluded() {
    local filename="${1}"
    local filepath="${2}"  # フルパスを追加
    shift 2
    local exclude_list=("${@}")

    local is_excluded=false
    local longest_match=""

    for pattern in "${exclude_list[@]}"; do
        # パターンがファイル名またはパスにマッチするかチェック
        local matches=false

        # ファイル名の完全一致
        if [[ "${filename}" == "${pattern}" ]]; then
            matches=true
        # パスの完全一致
        elif [[ "${filepath}" == "${pattern}" ]]; then
            matches=true
        # ワイルドカードパターンの処理
        elif [[ "${pattern}" == *"*"* ]]; then
            if [[ "${filename}" == ${pattern} ]] || [[ "${filepath}" == ${pattern} ]]; then
                matches=true
            fi
        # ディレクトリパターン（末尾が/の場合）
        elif [[ "${pattern}" == */ ]]; then
            local dir_pattern="${pattern%/}"
            if [[ "${filepath}" == "${dir_pattern}"/* ]] || [[ "${filepath}" == "${dir_pattern}" ]]; then
                matches=true
            fi
        fi

        if [[ "${matches}" == true ]]; then
            # longest matchをチェック
            if [[ "${#pattern}" -gt "${#longest_match}" ]]; then
                longest_match="${pattern}"
                # !で始まるパターンは除外解除、それ以外は除外
                if [[ "${pattern}" == "!"* ]]; then
                    is_excluded=false
                else
                    is_excluded=true
                fi
            fi
        fi
    done

    return $([ "${is_excluded}" == true ] && echo 0 || echo 1)
}

# ============================================================================
# メインインストール処理
# ============================================================================

# dotfilesのインストール
install_dotfiles() {
    local dotfiles=()
    local failed_files=()
    local force="${1:-false}"

    # dotfilesファイルリストを取得（除外ファイルを除く）
    local exclude_file="$(load_exclude_list)"
    local exclude_list=()
    while IFS= read -r line; do
        exclude_list+=("${line}")
    done < "${exclude_file}"

    # 再帰的にファイルを検索
    while IFS= read -r -d '' file; do
        local basename_file="$(basename "${file}")"
        local relative_path="${file#${SCRIPT_DIR}/}"

        # .temp をスキップ
        if [[ "${basename_file}" == ".temp" ]]; then
            continue
        fi

        # 除外ファイルをスキップ
        if is_excluded "${basename_file}" "${relative_path}" "${exclude_list[@]}"; then
            continue
        fi

        dotfiles+=("${file}")
    done < <(find "${SCRIPT_DIR}" -type f -name '.*' -print0)

    info "dotfilesインストール開始 (${#dotfiles[@]}個)"

    if [[ "${force}" != true ]]; then
        info "インタラクティブモード"
    fi

    # 各dotfileのシンボリックリンクを作成
    for file in "${dotfiles[@]}"; do
        if ! create_symlink "${file}" "${force}"; then
            failed_files+=("$(basename "${file}")")
        fi
    done

    if [[ ${#failed_files[@]} -gt 0 ]]; then
        error "失敗: ${failed_files[*]}"
        return 1
    fi

    success "dotfilesインストール完了"
}

# テンプレートディレクトリのインストール
install_template_dirs() {
    local template_dirs=("bin" "opt" "tools")
    local failed_dirs=()

    info "テンプレートディレクトリインストール開始"

    for dir in "${template_dirs[@]}"; do
        if ! copy_template_dir "${dir}"; then
            failed_dirs+=("${dir}")
        fi
    done

    if [[ ${#failed_dirs[@]} -gt 0 ]]; then
        warning "失敗: ${failed_dirs[*]}"
    fi

    success "テンプレートディレクトリ完了"
}

# ============================================================================
# ロールバック機能
# ============================================================================

# バックアップからの復元
rollback() {
    local specified_backup_dir="${1}"
    local target_backup_dir

    if [[ -n "${specified_backup_dir}" ]]; then
        # 指定されたバックアップディレクトリを使用
        if [[ ! -d "${specified_backup_dir}" ]]; then
            error "バックアップディレクトリが見つかりません: ${specified_backup_dir}"
            return 1
        fi
        target_backup_dir="${specified_backup_dir}"
    else
        # 最新のバックアップディレクトリを自動検索
        target_backup_dir=$(find "${HOME}" -maxdepth 1 -name ".dotfiles_backup_*" -type d | sort -r | head -1)

        if [[ -z "${target_backup_dir}" ]]; then
            error "バックアップディレクトリが見つかりません"
            info "利用可能なバックアップ:"
            find "${HOME}" -maxdepth 1 -name ".dotfiles_backup_*" -type d | sort -r || echo "なし"
            return 1
        fi

        info "最新バックアップ: $(basename "${target_backup_dir}")"
    fi

    # バックアップディレクトリの内容確認
    if [[ ! "$(ls -A "${target_backup_dir}")" ]]; then
        warning "バックアップディレクトリが空です: ${target_backup_dir}"
        return 0
    fi

    warning "ロールバック実行"
    warning "現在のdotfilesが上書きされます"
    info "復元元: ${target_backup_dir}"

    # 確認プロンプト
    echo -n "ロールバックしますか? [y/N]: "
    read -r response
    case "${response}" in
        [yY]|[yY][eE][sS])
            info "ロールバックを開始します"
            ;;
        *)
            info "ロールバックをキャンセルしました"
            return 0
            ;;
    esac

    local restored_count=0
    local failed_count=0
    local failed_files=()

    # バックアップファイルを復元
    for backup_file in "${target_backup_dir}"/*; do
        if [[ -f "${backup_file}" ]]; then
            local filename="$(basename "${backup_file}")"

            # ファイル名の検証（dotfilesのみ復元）
            if [[ ! "${filename}" =~ ^\.[a-zA-Z0-9._-]+$ ]]; then
                warning "無効なファイル名をスキップ: ${filename}"
                continue
            fi

            # 復元先の確認
            local restore_target="${HOME}/${filename}"
            if [[ -e "${restore_target}" ]] && [[ ! -L "${restore_target}" ]]; then
                warning "既存ファイルが存在します: ${filename}"
                if ! ask_user_confirmation "既存ファイル ${filename} を上書きしますか？" false; then
                    info "スキップ: ${filename}"
                    continue
                fi
            fi

            if cp "${backup_file}" "${restore_target}"; then
                info "復元: ${filename}"
                ((restored_count++))
            else
                error "復元失敗: ${filename}"
                failed_files+=("${filename}")
                ((failed_count++))
            fi
        fi
    done

    if [[ ${restored_count} -gt 0 ]]; then
        success "ロールバック完了 (${restored_count}個)"
        if [[ ${failed_count} -gt 0 ]]; then
            warning "復元失敗: ${failed_files[*]}"
        fi
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
使用方法: ${0} [オプション]

オプション:
    -h, --help          このヘルプを表示
    -f, --force         確認なしで実行
    -d, --dry-run       実際の処理を行わずにプレビューのみ
    --rollback [DIR]    バックアップからロールバック (DIR省略時は最新を使用)
    --cleanup           一時ファイルをクリーンアップして終了

説明:
    このスクリプトはdotfilesを安全にインストールします。
    既存ファイルは自動的にバックアップされます。

    注意: -f (--force) を指定しない場合、デフォルトで各ファイルの処理前に確認を求めます。

除外ファイル:
    インストール対象から除外したいファイルは .installignore に記載してください。
    コメント行（#で始まる行）と空行は無視されます。
    !で始まる行は除外解除（対象に含める）を意味します。
    パターンはlongest matchで優先されます。

バックアップ場所: ~/.dotfiles_backup_YYYYMMDD_HHMMSS/
ログファイル: ${SCRIPT_DIR}/install.log

EOF
}

# ドライラン機能
dry_run() {
    info "=== ドライランモード ==="

    local skip_count=0
    local update_count=0
    local backup_count=0
    local create_count=0
    local ignore_count=0

    # dotfilesのチェック
    local exclude_file="$(load_exclude_list)"
    local exclude_list=()
    while IFS= read -r line; do
        exclude_list+=("${line}")
    done < "${exclude_file}"

    while IFS= read -r -d '' file; do
        local basename_file="$(basename "${file}")"
        local relative_path="${file#${SCRIPT_DIR}/}"

        # 除外ファイルをスキップ
        if is_excluded "${basename_file}" "${relative_path}" "${exclude_list[@]}"; then
            echo "[IGNORE] ${relative_path} (除外対象)"
            ((ignore_count++))
            continue
        fi

        check_symlink_status "${file}"
        local status=$?

        case $status in
            0)  # スキップ
                echo "[SKIP] ${relative_path} (既に正しいリンクが存在)"
                ((skip_count++))
                ;;
            1)  # 更新
                local current_target="$(readlink "${HOME}/${relative_path}" 2>/dev/null || echo "unknown")"
                echo "[UPDATE] ${relative_path} (リンク先変更: $(basename "${current_target}") -> ${basename_file})"
                ((update_count++))
                ;;
            2)  # バックアップ
                echo "[BACKUP] ${relative_path} (既存ファイルをバックアップして置換)"
                ((backup_count++))
                ;;
            3)  # 新規作成
                echo "[CREATE] ${relative_path} (新規リンク作成)"
                ((create_count++))
                ;;
        esac
    done < <(find "${SCRIPT_DIR}" -type f -name '.*' -print0)

    # テンプレートディレクトリのチェック
    local template_dirs=("bin" "opt" "tools")
    local template_skip=0
    local template_copy=0

    for dir in "${template_dirs[@]}"; do
        if [[ -d "${SCRIPT_DIR}/template/${dir}" ]]; then
            if [[ -e "${HOME}/${dir}" ]]; then
                echo "[SKIP] ${dir} (既に存在)"
                ((template_skip++))
            else
                echo "[COPY] ${dir} (新規作成)"
                ((template_copy++))
            fi
        fi
    done

    echo
    info "=== 処理概要 ==="
    echo "dotfiles:"
    echo "  除外: ${ignore_count}個"
    echo "  スキップ: ${skip_count}個"
    echo "  更新: ${update_count}個"
    echo "  バックアップ: ${backup_count}個"
    echo "  新規作成: ${create_count}個"
    echo "テンプレートディレクトリ:"
    echo "  スキップ: ${template_skip}個"
    echo "  コピー: ${template_copy}個"

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
            --rollback)
                rollback_mode=true
                shift
                # 次の引数がバックアップディレクトリのパスかチェック
                if [[ $# -gt 0 && ! "$1" =~ ^- ]]; then
                    rollback_dir="$1"
                    shift
                fi
                ;;
            --cleanup)
                cleanup
                exit 0
                ;;
            *)
                error "不明なオプション: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # ログファイル初期化
    : > "${LOG_FILE}"

    # 一時ディレクトリ初期化
    init_temp_dir

    info "=== dotfilesインストールスクリプト開始 ==="
    log "スクリプトディレクトリ: ${SCRIPT_DIR}"
    log "ホームディレクトリ: ${HOME}"

    # ロールバックモード
    if [[ "${rollback_mode}" == true ]]; then
        rollback "${rollback_dir}"
        local exit_code=$?
        cleanup_temp_files
        exit ${exit_code}
    fi

    # 依存関係チェック
    if ! check_dependencies; then
        cleanup_temp_files
        exit 1
    fi

    # ドライランモード
    if [[ "${dry_run_mode}" == true ]]; then
        dry_run
        cleanup_temp_files
        exit 0
    fi

    # 確認プロンプト
    if [[ "${force}" != true ]]; then
        echo
        info "以下の処理を実行します:"
        echo "  1. 既存dotfilesのバックアップ"
        echo "  2. dotfilesのシンボリックリンク作成"
        echo "  3. テンプレートディレクトリのコピー"
        echo
        echo -n "続行しますか? [y/N]: "
        read -r response
        case "${response}" in
            [yY]|[yY][eE][sS])
                info "インストールを開始します"
                ;;
            *)
                info "インストールをキャンセルしました"
                cleanup_temp_files
                exit 0
                ;;
        esac
    fi

    # バックアップディレクトリ作成
    create_backup_dir

    # メイン処理実行
    local exit_code=0

    if ! install_dotfiles "${force}"; then
        error "dotfilesインストールでエラーが発生しました"
        exit_code=1
    fi

    if ! install_template_dirs; then
        warning "一部のテンプレートディレクトリでエラーが発生しました"
    fi

    if [[ ${exit_code} -eq 0 ]]; then
        success "=== インストール完了 ==="
        info "バックアップ: ${BACKUP_DIR}"
        info "ログ: ${LOG_FILE}"
        echo
        info "ロールバックするには: ${0} --rollback [バックアップディレクトリ]"
    else
        error "=== インストール失敗 ==="
        info "ロールバックするには: ${0} --rollback [バックアップディレクトリ]"
    fi

    # クリーンアップ実行
    cleanup_temp_files

    exit ${exit_code}
}

# ============================================================================
# スクリプト実行
# ============================================================================

# エラー時のトラップ処理
trap 'error "スクリプトが予期しないエラーで終了しました"; cleanup_temp_files; exit 1' ERR

# 中断時のトラップ処理
trap 'warning "スクリプトが中断されました"; cleanup_temp_files; exit 130' INT TERM

# スクリプト実行
main "$@"