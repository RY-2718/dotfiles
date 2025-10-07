#!/bin/bash
# dotfiles installer テストスクリプト

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="${SCRIPT_DIR}/test_env"

echo "🧪 dotfiles installer テスト環境セットアップ"

# テストディレクトリをクリーンアップ
if [[ -d "${TEST_DIR}" ]]; then
    echo "既存のテスト環境をクリーンアップ中..."
    rm -rf "${TEST_DIR}"
fi

# テストディレクトリ作成
mkdir -p "${TEST_DIR}"

# 既存ファイルを模擬作成（テスト用）
echo "既存ファイルを模擬作成中..."
echo "# existing .gitconfig" > "${TEST_DIR}/.gitconfig"
echo "# existing .bashrc" > "${TEST_DIR}/.bashrc"

echo "✅ テスト環境準備完了: ${TEST_DIR}"
echo ""
echo "📋 利用可能なテストコマンド:"
echo "  # ドライラン（安全確認）"
echo "  ./install.py --dry-run"
echo ""
echo "  # テスト環境でのドライラン"
echo "  ./install.py --test-mode ${TEST_DIR} --dry-run"
echo ""
echo "  # テスト環境での実際のインストール"
echo "  ./install.py --test-mode ${TEST_DIR}"
echo ""
echo "  # テスト環境での強制インストール"
echo "  ./install.py --test-mode ${TEST_DIR} --force"
echo ""
echo "⚠️  実際のホームディレクトリでテストする場合は:"
echo "  ./install.py --dry-run  # まず必ずdry-runで確認"