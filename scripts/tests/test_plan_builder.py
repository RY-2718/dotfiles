"""PlanBuilder のテスト."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.pkg.plan.builder import PlanBuilder
from scripts.pkg.plan.model import ActionType


class TestPlanBuilder(unittest.TestCase):
    """PlanBuilder クラスのテスト."""

    def setUp(self):
        """各テストの前に実行される共通セットアップ."""
        # 一時ディレクトリを作成
        self.test_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.test_dir.name)

        self.source = self.tmp_path / "source"
        self.dest = self.tmp_path / "dest"
        self.rollbacks = self.tmp_path / "rollbacks"

        self.source.mkdir()
        self.dest.mkdir()
        self.rollbacks.mkdir()

    def tearDown(self):
        """各テストの後に実行されるクリーンアップ."""
        self.test_dir.cleanup()

    def _setup_basic_source(self):
        """基本的なテストファイルをsource/に配置."""
        (self.source / ".bashrc").write_text("# test bashrc\n")
        (self.source / ".vimrc").write_text("# test vimrc\n")
        (self.source / ".zshrc").write_text("# test zshrc\n")

        (self.source / ".config").mkdir()
        (self.source / ".config" / "test.conf").write_text("test=1\n")
        (self.source / ".config" / "subdir").mkdir()
        (self.source / ".config" / "subdir" / "nested.conf").write_text("nested=1\n")

    def _setup_dest_with_existing_files(self):
        """ホームディレクトリに既存ファイルを配置."""
        self._setup_basic_source()
        (self.dest / ".bashrc").write_text("# existing bashrc\n")
        (self.dest / ".vimrc").symlink_to(self.source / ".vimrc")

    def test_empty_source(self):
        """空の source/ ディレクトリで Plan が空になることを確認."""
        builder = PlanBuilder(source_dir=self.source, dest_dir=self.dest)
        plan = builder.build()

        self.assertEqual(len(plan.entries), 0)
        self.assertEqual(plan.summary().total, 0)

    def test_basic_file_creation(self):
        """新規ファイルが CREATE アクションになることを確認."""
        self._setup_basic_source()

        builder = PlanBuilder(source_dir=self.source, dest_dir=self.dest)
        plan = builder.build()

        # .bashrc, .vimrc, .zshrc, test.conf, nested.conf の5ファイル
        # + .config, .config/subdir の2ディレクトリ = 計7エントリ
        self.assertEqual(len(plan.entries), 7)

        # ディレクトリエントリ
        ensure_dirs = [e for e in plan.entries if e.action == ActionType.ENSURE_DIR]
        self.assertEqual(len(ensure_dirs), 2)
        dir_paths = {str(e.spec.relative_path) for e in ensure_dirs}
        self.assertIn(".config", dir_paths)
        self.assertIn(".config/subdir", dir_paths)

        # 新規作成エントリ
        creates = [e for e in plan.entries if e.action == ActionType.CREATE]
        self.assertEqual(len(creates), 5)
        create_paths = {str(e.spec.relative_path) for e in creates}
        self.assertIn(".bashrc", create_paths)
        self.assertIn(".vimrc", create_paths)
        self.assertIn(".zshrc", create_paths)
        self.assertIn(".config/test.conf", create_paths)
        self.assertIn(".config/subdir/nested.conf", create_paths)

    def test_existing_file_update(self):
        """既存ファイルが UPDATE アクションになることを確認."""
        self._setup_dest_with_existing_files()

        builder = PlanBuilder(source_dir=self.source, dest_dir=self.dest)
        plan = builder.build()

        # .bashrc は既存ファイルなので UPDATE
        updates = [e for e in plan.entries if e.action == ActionType.UPDATE]
        self.assertEqual(len(updates), 1)
        self.assertEqual(str(updates[0].spec.relative_path), ".bashrc")
        self.assertTrue(updates[0].needs_confirmation)
        self.assertTrue(updates[0].needs_backup)

    def test_existing_correct_link_skip(self):
        """既存の正しいリンクが SKIP アクションになることを確認."""
        self._setup_dest_with_existing_files()

        builder = PlanBuilder(source_dir=self.source, dest_dir=self.dest)
        plan = builder.build()

        # .vimrc は既存の正しいリンクなので SKIP
        skips = [e for e in plan.entries if e.action == ActionType.SKIP]
        self.assertEqual(len(skips), 1)
        self.assertEqual(str(skips[0].spec.relative_path), ".vimrc")
        self.assertFalse(skips[0].needs_confirmation)
        self.assertFalse(skips[0].needs_backup)

    def test_symlink_in_source_error(self):
        """source/ 内のシンボリックリンクが ERROR アクションになることを確認."""
        # source/ 内にシンボリックリンクを作成
        dummy_file = self.source / "dummy.txt"
        dummy_file.write_text("dummy")
        (self.source / ".bashrc").symlink_to(dummy_file)

        builder = PlanBuilder(source_dir=self.source, dest_dir=self.dest)
        plan = builder.build()

        # ERROR エントリが生成される
        errors = [e for e in plan.entries if e.action == ActionType.ERROR]
        self.assertEqual(len(errors), 1)
        self.assertEqual(str(errors[0].spec.relative_path), ".bashrc")
        self.assertIn("シンボリックリンク", errors[0].message)

    def test_broken_link_in_home_update(self):
        """ホームディレクトリの壊れたリンクが UPDATE アクションになることを確認."""
        # source/ にファイルを作成
        (self.source / ".bashrc").write_text("# new bashrc\n")

        # home/ に壊れたリンクを作成
        nonexistent_file = self.dest / "nonexistent.txt"
        (self.dest / ".bashrc").symlink_to(nonexistent_file)

        builder = PlanBuilder(source_dir=self.source, dest_dir=self.dest)
        plan = builder.build()

        # 壊れたリンクは UPDATE として扱われる
        updates = [e for e in plan.entries if e.action == ActionType.UPDATE]
        self.assertEqual(len(updates), 1)
        self.assertEqual(str(updates[0].spec.relative_path), ".bashrc")

    def test_plan_summary(self):
        """Plan のサマリーが正しく生成されることを確認."""
        self._setup_dest_with_existing_files()

        builder = PlanBuilder(source_dir=self.source, dest_dir=self.dest)
        plan = builder.build()

        summary = plan.summary()
        self.assertEqual(summary.ensure_dirs, 2)
        self.assertEqual(summary.creates, 3)  # .zshrc, test.conf, nested.conf (.vimrcはSKIP)
        self.assertEqual(summary.updates, 1)  # .bashrc
        self.assertEqual(summary.skips, 1)    # .vimrc
        self.assertEqual(summary.errors, 0)
        self.assertEqual(summary.total, 7)

    def test_plan_confirmations(self):
        """確認が必要なエントリが正しく抽出されることを確認."""
        self._setup_dest_with_existing_files()

        builder = PlanBuilder(source_dir=self.source, dest_dir=self.dest)
        plan = builder.build()

        confirmations = list(plan.iter_confirmations())
        self.assertEqual(len(confirmations), 1)
        self.assertEqual(str(confirmations[0].spec.relative_path), ".bashrc")
        self.assertEqual(confirmations[0].action, ActionType.UPDATE)

    def test_skip_existing_directory(self):
        """既に存在するディレクトリに対して ENSURE_DIR が生成されないことを確認."""
        # source/ に .config/test.conf を作成
        (self.source / ".config").mkdir()
        (self.source / ".config" / "test.conf").write_text("test=1\n")

        # dest/ に既に .config ディレクトリが存在
        (self.dest / ".config").mkdir()

        builder = PlanBuilder(source_dir=self.source, dest_dir=self.dest)
        plan = builder.build()

        # ENSURE_DIR は生成されないはず
        ensure_dirs = [e for e in plan.entries if e.action == ActionType.ENSURE_DIR]
        self.assertEqual(len(ensure_dirs), 0)

        # CREATE のみ
        creates = [e for e in plan.entries if e.action == ActionType.CREATE]
        self.assertEqual(len(creates), 1)
        self.assertEqual(str(creates[0].spec.relative_path), ".config/test.conf")


if __name__ == "__main__":
    unittest.main()
