#!/usr/bin/env python3
"""
Dotfiles Installer - Python版

安全なdotfilesインストールスクリプト（Python標準ライブラリのみ使用）
既存のinstall.shの機能をPythonで再実装
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from lib.config import Config
from lib.installer import DotfilesInstaller
from lib.logger import ColoredLogger


def create_argument_parser():
    """共通の引数パーサーを作成"""
    parser = argparse.ArgumentParser(
        description="Dotfiles installer - 安全なdotfilesインストールツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s                    # インタラクティブモードでインストール
  %(prog)s --force            # 確認なしでインストール
  %(prog)s --dry-run          # 実際の処理を行わずにプレビュー
  %(prog)s --rollback         # 最新のバックアップからロールバック
  %(prog)s --rollback /path   # 指定パスからロールバック

注意:
  - 既存ファイルは自動的にバックアップされます
  - .installignoreファイルで除外ファイルを指定可能
  - バックアップ先: ~/.dotfiles_backup_YYYYMMDD_HHMMSS/
        """
    )

    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="確認なしで実行"
    )

    parser.add_argument(
        "-d", "--dry-run",
        action="store_true",
        help="実際の処理を行わずにプレビューのみ"
    )

    parser.add_argument(
        "--rollback",
        nargs="?",
        const="",
        metavar="DIR",
        help="バックアップからロールバック（DIR省略時は最新を使用）"
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="一時ファイルをクリーンアップして終了"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="詳細なログを出力"
    )

    parser.add_argument(
        "--test-mode",
        metavar="DIR",
        help="テストモード: 指定ディレクトリをホームディレクトリとして使用"
    )

    return parser


def setup_logging(log_file: Path, verbose: bool = False) -> logging.Logger:
    """ログ設定を初期化"""
    logger = ColoredLogger("dotfiles", log_file)

    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    return logger


def parse_arguments() -> argparse.Namespace:
    """コマンドライン引数を解析"""
    parser = create_argument_parser()
    return parser.parse_args()


def parse_arguments_for_help():
    """ヘルプ表示用の引数解析"""
    parser = create_argument_parser()
    parser.print_help()


def main() -> int:
    """メイン処理"""
    try:
        # 引数なしで実行された場合はヘルプを表示
        if len(sys.argv) == 1:
            parse_arguments_for_help()
            return 0

        # 引数解析
        args = parse_arguments()

        # 設定初期化
        config = Config()

        # テストモード対応
        if args.test_mode:
            test_dir = Path(args.test_mode).resolve()
            test_dir.mkdir(parents=True, exist_ok=True)

            # TODO config に寄せたほうがいい？
            config.target_dir = test_dir
            # バックアップディレクトリも再設定
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            config.backup_dir = test_dir / f".dotfiles_backup_{timestamp}"
            print(f"🧪 テストモード: {test_dir} をインストール先として使用")

        # ログ設定
        logger = setup_logging(config.log_file, args.verbose)

        # インストーラー初期化
        installer = DotfilesInstaller(config, logger)

        # クリーンアップモード
        if args.cleanup:
            installer.cleanup()
            return 0

        # ロールバックモード
        if args.rollback is not None:
            backup_dir = args.rollback if args.rollback else None
            return installer.rollback(backup_dir)

        # ドライランモード
        if args.dry_run:
            installer.dry_run()
            return 0

        # 通常のインストール
        return installer.install(force=args.force)

    except KeyboardInterrupt:
        print("\n操作がキャンセルされました")
        return 130
    except Exception as e:
        print(f"予期しないエラー: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())