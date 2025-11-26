#!/usr/bin/env python3
"""Dotfiles Installer - source/ ベースの新しい実装.

Plan/Executor パターンを使用した安全なdotfilesインストーラー
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.pkg.backup_store import BackupManager
from scripts.pkg.logger import ColoredLogger
from scripts.pkg.plan.builder import PlanBuilder
from scripts.pkg.plan.executor import PlanExecutor
from scripts.pkg.rollback_manager import RollbackManager
from scripts.pkg.ui import UserInterface


def create_argument_parser() -> argparse.ArgumentParser:
    """コマンドライン引数パーサーを作成."""
    parser = argparse.ArgumentParser(
        description="Dotfiles installer - source/ ディレクトリを使った安全なインストーラー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s                    # インタラクティブモードでインストール
  %(prog)s --dry-run          # 実際の処理を行わずにプレビュー
  %(prog)s --force            # 確認なしでインストール
  %(prog)s --rollback         # 最新のバックアップからロールバック

注意:
  - source/ ディレクトリのファイルをホームディレクトリにシンボリックリンク
  - 既存ファイルは自動的にバックアップされます
  - バックアップ先: rollbacks/<timestamp>/
        """,
    )

    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="実際の処理を行わずにプレビューのみ",
    )

    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="確認なしで実行",
    )

    parser.add_argument(
        "--rollback",
        nargs="?",
        const="latest",
        metavar="TIMESTAMP",
        help="バックアップからロールバック（省略時は最新）",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="詳細なログを出力",
    )

    parser.add_argument(
        "--source-dir",
        type=Path,
        metavar="DIR",
        help="source/ ディレクトリのパス（デフォルト: ./source）",
    )

    parser.add_argument(
        "--dest-dir",
        type=Path,
        metavar="DIR",
        help="インストール先ディレクトリ（デフォルト: $HOME）",
    )

    return parser


def main() -> int:
    """メイン処理."""
    try:
        # 引数解析
        parser = create_argument_parser()
        args = parser.parse_args()

        # ディレクトリ設定
        repo_root = Path(__file__).resolve().parent
        source_dir = args.source_dir if args.source_dir else repo_root / "source"
        dest_dir = args.dest_dir if args.dest_dir else Path.home()
        rollbacks_dir = repo_root / "rollbacks"

        # source/ が存在しない場合はエラー
        if not source_dir.exists():
            print(f"エラー: source/ ディレクトリが見つかりません: {source_dir}")
            print(
                "\nsource/ ディレクトリを作成して、インストールしたいファイルを配置してください。"
            )
            return 1

        # UI・ログ設定
        ui = UserInterface()
        logger = ColoredLogger(name="dotfiles_installer")
        if args.verbose:
            import logging

            logger.set_level(logging.DEBUG)

        # ロールバックモード
        if args.rollback is not None:
            if args.rollback == "latest":
                # 利用可能なバックアップを一覧表示
                archives = sorted(rollbacks_dir.glob("*"), reverse=True)
                if not archives:
                    print("エラー: 利用可能なバックアップが見つかりません")
                    return 1

                if len(archives) == 1:
                    archive_path = archives[0]
                    print(f"最新のバックアップからロールバック: {archive_path.name}")
                else:
                    # 複数ある場合は選択肢を表示
                    print("\n利用可能なバックアップ:")
                    for i, archive in enumerate(archives, 1):
                        print(f"  {i}. {archive.name}")
                    print()

                    if args.force:
                        # --force の場合は最新を自動選択
                        archive_path = archives[0]
                        print(f"最新のバックアップを選択: {archive_path.name}")
                    else:
                        # ユーザーに選択させる
                        while True:
                            try:
                                choice = input(
                                    f"ロールバックするバックアップを選択 (1-{len(archives)}, Enter=1): "
                                ).strip()
                                if not choice:
                                    choice = "1"
                                idx = int(choice) - 1
                                if 0 <= idx < len(archives):
                                    archive_path = archives[idx]
                                    break
                                print(f"1から{len(archives)}の数字を入力してください")
                            except ValueError:
                                print("数字を入力してください")
                            except (KeyboardInterrupt, EOFError):
                                print("\nキャンセルされました")
                                return 0
            else:
                archive_path = rollbacks_dir / args.rollback
                if not archive_path.exists():
                    print(f"エラー: 指定されたバックアップが見つかりません: {archive_path}")
                    return 1

            # dry-run モード
            if args.dry_run:
                print(f"\n[DRY-RUN] {archive_path.name} から復元される予定のファイル:")
                rollback_manager = RollbackManager(target_root=dest_dir, ui=ui)
                for entry, info in rollback_manager._iter_backup_entries(archive_path):
                    file_type = "symlink" if info == "symlink" else "file"
                    current_file = dest_dir / entry

                    # 現在の状態を表示
                    if current_file.is_symlink():
                        current_target = current_file.readlink()
                        if info == "symlink":
                            # バックアップのリンク先を取得
                            link_file = archive_path / f"{entry}.link"
                            backup_target = Path(link_file.read_text().strip())
                            print(f"  - {entry}: {current_target} → {backup_target}")
                        else:
                            print(f"  - {entry}: symlink → file")
                    elif current_file.exists():
                        print(f"  - {entry}: file → {file_type}")
                    else:
                        print(f"  - {entry}: (新規作成) ← {file_type}")

                print("\n[DRY-RUN] 実際の処理は行われません")
                return 0

            if not args.force and not ui.confirm(
                f"{archive_path.name} からロールバックしますか？", default_yes=False
            ):
                print("キャンセルされました")
                return 0

            rollback_manager = RollbackManager(target_root=dest_dir, ui=ui)
            rollback_manager.restore_archive(archive_path, restore_all=args.force)
            logger.success("ロールバック完了")
            return 0

        # Plan 生成
        logger.info("インストール計画を生成中...")
        builder = PlanBuilder(source_dir=source_dir, dest_dir=dest_dir)
        plan = builder.build()

        # サマリー表示
        print()
        print("=" * 60)
        print("インストール計画")
        print("=" * 60)
        summary = plan.summary()
        for line in summary.format_lines():
            print(line)
        print()

        # 確認が必要なエントリを表示
        confirmations = list(plan.iter_confirmations())
        if confirmations:
            print("⚠️  以下のファイルは確認が必要です:")
            for entry in confirmations:
                print(f"  - {entry.spec.relative_path}: {entry.message}")
            print()

        if summary.total == 0:
            logger.success("処理が必要なファイルはありません")
            return 0

        # ドライランモード
        if args.dry_run:
            logger.info("[DRY-RUN] 実際の処理は行われません")
            return 0

        # 実行確認
        if not args.force and not ui.confirm(
            f"{summary.total}個のファイルをインストールしますか？", default_yes=True
        ):
            print("キャンセルされました")
            return 0

        # 実行
        backup_manager = BackupManager(rollbacks_root=rollbacks_dir)
        executor = PlanExecutor(ui=ui, logger=logger, backup_manager=backup_manager)

        print()
        print("=" * 60)
        print("インストール実行中...")
        print("=" * 60)
        report = executor.execute(plan, dry_run=False)

        print()
        print("=" * 60)
        print("インストール完了")
        print("=" * 60)
        print(f"適用: {report.applied}件")
        print(f"スキップ: {report.skipped}件")
        if report.errors > 0:
            print(f"エラー: {report.errors}件")
            return 1

        logger.success("✨ インストールが完了しました")
        return 0

    except KeyboardInterrupt:
        print("\n\n操作がキャンセルされました")
        return 130
    except Exception as e:
        print(f"\n予期しないエラー: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
