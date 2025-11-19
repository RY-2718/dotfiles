"""PlanExecutor のテスト."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.pkg.backup_store import BackupManager
from scripts.pkg.logger import ColoredLogger
from scripts.pkg.plan.builder import PlanBuilder
from scripts.pkg.plan.executor import PlanExecutor
from scripts.pkg.ui import UserInterface


class TestPlanExecutorDryRun(unittest.TestCase):
    """PlanExecutor のドライランモードのテスト."""

    def setUp(self):
        """各テストの前に実行される共通セットアップ."""
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

    def _setup_dest_with_existing_files(self):
        """ホームディレクトリに既存ファイルを配置."""
        (self.source / ".bashrc").write_text("# test bashrc\n")
        (self.source / ".vimrc").write_text("# test vimrc\n")
        (self.source / ".zshrc").write_text("# test zshrc\n")

        (self.source / ".config").mkdir()
        (self.source / ".config" / "test.conf").write_text("test=1\n")
        (self.source / ".config" / "subdir").mkdir()
        (self.source / ".config" / "subdir" / "nested.conf").write_text("nested=1\n")

        (self.dest / ".bashrc").write_text("# existing bashrc\n")
        (self.dest / ".vimrc").symlink_to(self.source / ".vimrc")

    def test_dry_run_no_changes(self):
        """ドライランモードで実際にファイルが変更されないことを確認."""
        self._setup_dest_with_existing_files()

        builder = PlanBuilder(source_dir=self.source, dest_dir=self.dest)
        plan = builder.build()

        logger = ColoredLogger(name="test")
        ui = UserInterface()
        backup_manager = BackupManager(rollbacks_root=self.rollbacks)
        executor = PlanExecutor(ui=ui, logger=logger, backup_manager=backup_manager)

        report = executor.execute(plan, dry_run=True)

        self.assertEqual(report.applied, 0)
        self.assertEqual(report.errors, 0)

        bashrc = self.dest / ".bashrc"
        self.assertTrue(bashrc.exists())
        self.assertFalse(bashrc.is_symlink())
        self.assertEqual(bashrc.read_text(), "# existing bashrc\n")

        backup_dirs = list(self.rollbacks.glob("*"))
        self.assertEqual(len(backup_dirs), 0)


class TestPlanExecutorExecution(unittest.TestCase):
    """PlanExecutor の実行モードのテスト."""

    def setUp(self):
        """各テストの前に実行される共通セットアップ."""
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

    def test_create_new_links(self):
        """新規ファイルがリンクとして作成されることを確認."""
        self._setup_basic_source()

        builder = PlanBuilder(source_dir=self.source, dest_dir=self.dest)
        plan = builder.build()

        logger = ColoredLogger(name="test")
        ui = UserInterface()
        ui.confirm = lambda msg, default_yes=True: True
        backup_manager = BackupManager(rollbacks_root=self.rollbacks)
        executor = PlanExecutor(ui=ui, logger=logger, backup_manager=backup_manager)

        report = executor.execute(plan, dry_run=False)

        self.assertGreater(report.applied, 0)
        self.assertEqual(report.errors, 0)

        bashrc = self.dest / ".bashrc"
        self.assertTrue(bashrc.is_symlink())
        self.assertEqual(bashrc.resolve(), (self.source / ".bashrc").resolve())

        vimrc = self.dest / ".vimrc"
        self.assertTrue(vimrc.is_symlink())
        self.assertEqual(vimrc.resolve(), (self.source / ".vimrc").resolve())

        zshrc = self.dest / ".zshrc"
        self.assertTrue(zshrc.is_symlink())
        self.assertEqual(zshrc.resolve(), (self.source / ".zshrc").resolve())

    def test_create_nested_links(self):
        """ネストしたディレクトリ内のファイルがリンクとして作成されることを確認."""
        self._setup_basic_source()

        builder = PlanBuilder(source_dir=self.source, dest_dir=self.dest)
        plan = builder.build()

        logger = ColoredLogger(name="test")
        ui = UserInterface()
        ui.confirm = lambda msg, default_yes=True: True
        backup_manager = BackupManager(rollbacks_root=self.rollbacks)
        executor = PlanExecutor(ui=ui, logger=logger, backup_manager=backup_manager)

        executor.execute(plan, dry_run=False)

        config = self.dest / ".config"
        self.assertTrue(config.is_dir())
        self.assertFalse(config.is_symlink())

        subdir = self.dest / ".config" / "subdir"
        self.assertTrue(subdir.is_dir())
        self.assertFalse(subdir.is_symlink())

        test_conf = self.dest / ".config" / "test.conf"
        self.assertTrue(test_conf.is_symlink())
        self.assertEqual(test_conf.resolve(), (self.source / ".config" / "test.conf").resolve())

        nested = self.dest / ".config" / "subdir" / "nested.conf"
        self.assertTrue(nested.is_symlink())
        self.assertEqual(nested.resolve(), (self.source / ".config" / "subdir" / "nested.conf").resolve())

    def test_update_existing_file_with_backup(self):
        """既存ファイルをバックアップして上書きすることを確認."""
        self._setup_dest_with_existing_files()

        builder = PlanBuilder(source_dir=self.source, dest_dir=self.dest)
        plan = builder.build()

        logger = ColoredLogger(name="test")
        ui = UserInterface()
        ui.confirm = lambda msg, default_yes=True: True
        backup_manager = BackupManager(rollbacks_root=self.rollbacks)
        executor = PlanExecutor(ui=ui, logger=logger, backup_manager=backup_manager)

        executor.execute(plan, dry_run=False)

        bashrc = self.dest / ".bashrc"
        self.assertTrue(bashrc.is_symlink())
        self.assertEqual(bashrc.resolve(), (self.source / ".bashrc").resolve())

        backup_dirs = list(self.rollbacks.glob("*"))
        self.assertEqual(len(backup_dirs), 1)

        backup_dir = backup_dirs[0]
        backup_bashrc = backup_dir / ".bashrc"
        self.assertTrue(backup_bashrc.exists())
        self.assertEqual(backup_bashrc.read_text(), "# existing bashrc\n")

    def test_skip_existing_correct_link(self):
        """既存の正しいリンクがスキップされることを確認."""
        self._setup_dest_with_existing_files()

        builder = PlanBuilder(source_dir=self.source, dest_dir=self.dest)
        plan = builder.build()

        logger = ColoredLogger(name="test")
        ui = UserInterface()
        ui.confirm = lambda msg, default_yes=True: True
        backup_manager = BackupManager(rollbacks_root=self.rollbacks)
        executor = PlanExecutor(ui=ui, logger=logger, backup_manager=backup_manager)

        vimrc = self.dest / ".vimrc"
        original_link_dest = vimrc.resolve()

        report = executor.execute(plan, dry_run=False)

        self.assertGreater(report.skipped, 0)

        self.assertTrue(vimrc.is_symlink())
        self.assertEqual(vimrc.resolve(), original_link_dest)

    def test_confirmation_required(self):
        """確認が必要なエントリでユーザー確認が求められることを確認."""
        self._setup_dest_with_existing_files()

        builder = PlanBuilder(source_dir=self.source, dest_dir=self.dest)
        plan = builder.build()

        logger = ColoredLogger(name="test")
        ui = UserInterface()
        ui.confirm = lambda msg, default_yes=True: False
        backup_manager = BackupManager(rollbacks_root=self.rollbacks)
        executor = PlanExecutor(ui=ui, logger=logger, backup_manager=backup_manager)

        executor.execute(plan, dry_run=False)

        bashrc = self.dest / ".bashrc"
        self.assertFalse(bashrc.is_symlink())
        self.assertEqual(bashrc.read_text(), "# existing bashrc\n")

        backup_dirs = list(self.rollbacks.glob("*"))
        self.assertEqual(len(backup_dirs), 0)


class TestPlanExecutorEdgeCases(unittest.TestCase):
    """PlanExecutor のエッジケースのテスト."""

    def setUp(self):
        """各テストの前に実行される共通セットアップ."""
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

    def test_broken_link_replacement(self):
        """壊れたリンクが正しく置き換えられることを確認."""
        (self.source / ".bashrc").write_text("# new bashrc\n")

        nonexistent_file = self.dest / "nonexistent.txt"
        (self.dest / ".bashrc").symlink_to(nonexistent_file)

        builder = PlanBuilder(source_dir=self.source, dest_dir=self.dest)
        plan = builder.build()

        logger = ColoredLogger(name="test")
        ui = UserInterface()
        ui.confirm = lambda msg, default_yes=True: True
        backup_manager = BackupManager(rollbacks_root=self.rollbacks)
        executor = PlanExecutor(ui=ui, logger=logger, backup_manager=backup_manager)

        executor.execute(plan, dry_run=False)

        bashrc = self.dest / ".bashrc"
        self.assertTrue(bashrc.is_symlink())
        self.assertEqual(bashrc.resolve(), (self.source / ".bashrc").resolve())
        self.assertTrue(bashrc.exists())

    def test_no_backup_for_create_action(self):
        """CREATE アクションではバックアップが作成されないことを確認."""
        (self.source / ".bashrc").write_text("# test bashrc\n")
        (self.source / ".vimrc").write_text("# test vimrc\n")
        (self.source / ".zshrc").write_text("# test zshrc\n")

        (self.source / ".config").mkdir()
        (self.source / ".config" / "test.conf").write_text("test=1\n")
        (self.source / ".config" / "subdir").mkdir()
        (self.source / ".config" / "subdir" / "nested.conf").write_text("nested=1\n")

        builder = PlanBuilder(source_dir=self.source, dest_dir=self.dest)
        plan = builder.build()

        logger = ColoredLogger(name="test")
        ui = UserInterface()
        ui.confirm = lambda msg, default_yes=True: True
        backup_manager = BackupManager(rollbacks_root=self.rollbacks)
        executor = PlanExecutor(ui=ui, logger=logger, backup_manager=backup_manager)

        executor.execute(plan, dry_run=False)

        backup_dirs = list(self.rollbacks.glob("*"))
        self.assertEqual(len(backup_dirs), 0)


if __name__ == "__main__":
    unittest.main()
    """PlanExecutor のドライランモードのテスト."""

    def test_dry_run_no_changes(self, home_with_existing_files):
        """ドライランモードで実際にファイルが変更されないことを確認."""
        source, home, rollbacks = home_with_existing_files

        # Plan 生成
        builder = PlanBuilder(source_dir=source, dest_dir=home)
        plan = builder.build()

        # Executor 作成
        logger = ColoredLogger(name="test")
        ui = UserInterface()
        backup_manager = BackupManager(rollbacks_root=rollbacks)
        executor = PlanExecutor(ui=ui, logger=logger, backup_manager=backup_manager)

        # ドライラン実行
        report = executor.execute(plan, dry_run=True)

        # 統計確認（dry_runなので全てスキップ扱い）
        assert report.applied == 0
        assert report.errors == 0

        # ファイルが変更されていないことを確認
        bashrc = home / ".bashrc"
        assert bashrc.exists()
        assert not bashrc.is_symlink()
        assert bashrc.read_text() == "# existing bashrc\n"

        # バックアップディレクトリが作成されていないことを確認
        backup_dirs = list(rollbacks.glob("*"))
        assert len(backup_dirs) == 0


class TestPlanExecutorExecution:
    """PlanExecutor の実行モードのテスト."""

    def test_create_new_links(self, basic_source):
        """新規ファイルがリンクとして作成されることを確認."""
        source, home, rollbacks = basic_source

        # Plan 生成
        builder = PlanBuilder(source_dir=source, dest_dir=home)
        plan = builder.build()

        # Executor 作成（確認を自動でYes）
        logger = ColoredLogger(name="test")
        ui = UserInterface()
        ui.confirm = lambda msg, default_yes=True: True
        backup_manager = BackupManager(rollbacks_root=rollbacks)
        executor = PlanExecutor(ui=ui, logger=logger, backup_manager=backup_manager)

        # 実行
        report = executor.execute(plan, dry_run=False)

        # 統計確認
        assert report.applied > 0
        assert report.errors == 0

        # リンクが作成されていることを確認
        bashrc = home / ".bashrc"
        assert bashrc.is_symlink()
        assert bashrc.resolve() == (source / ".bashrc").resolve()

        vimrc = home / ".vimrc"
        assert vimrc.is_symlink()
        assert vimrc.resolve() == (source / ".vimrc").resolve()

        zshrc = home / ".zshrc"
        assert zshrc.is_symlink()
        assert zshrc.resolve() == (source / ".zshrc").resolve()

    def test_create_nested_links(self, basic_source):
        """ネストしたディレクトリ内のファイルがリンクとして作成されることを確認."""
        source, home, rollbacks = basic_source

        # Plan 生成
        builder = PlanBuilder(source_dir=source, dest_dir=home)
        plan = builder.build()

        # Executor 作成
        logger = ColoredLogger(name="test")
        ui = UserInterface()
        ui.confirm = lambda msg, default_yes=True: True
        backup_manager = BackupManager(rollbacks_root=rollbacks)
        executor = PlanExecutor(ui=ui, logger=logger, backup_manager=backup_manager)

        # 実行
        executor.execute(plan, dry_run=False)

        # ディレクトリが作成されていることを確認
        config = home / ".config"
        assert config.is_dir()
        assert not config.is_symlink()  # ディレクトリはリンクではない

        subdir = home / ".config" / "subdir"
        assert subdir.is_dir()
        assert not subdir.is_symlink()

        # ファイルがリンクになっていることを確認
        test_conf = home / ".config" / "test.conf"
        assert test_conf.is_symlink()
        assert test_conf.resolve() == (source / ".config" / "test.conf").resolve()

        nested = home / ".config" / "subdir" / "nested.conf"
        assert nested.is_symlink()
        assert nested.resolve() == (source / ".config" / "subdir" / "nested.conf").resolve()

    def test_update_existing_file_with_backup(self, home_with_existing_files):
        """既存ファイルをバックアップして上書きすることを確認."""
        source, home, rollbacks = home_with_existing_files

        # Plan 生成
        builder = PlanBuilder(source_dir=source, dest_dir=home)
        plan = builder.build()

        # Executor 作成
        logger = ColoredLogger(name="test")
        ui = UserInterface()
        ui.confirm = lambda msg, default_yes=True: True
        backup_manager = BackupManager(rollbacks_root=rollbacks)
        executor = PlanExecutor(ui=ui, logger=logger, backup_manager=backup_manager)

        # 実行
        executor.execute(plan, dry_run=False)

        # .bashrc がリンクになっていることを確認
        bashrc = home / ".bashrc"
        assert bashrc.is_symlink()
        assert bashrc.resolve() == (source / ".bashrc").resolve()

        # バックアップが作成されていることを確認
        backup_dirs = list(rollbacks.glob("*"))
        assert len(backup_dirs) == 1

        backup_dir = backup_dirs[0]
        backup_bashrc = backup_dir / ".bashrc"
        assert backup_bashrc.exists()
        assert backup_bashrc.read_text() == "# existing bashrc\n"

    def test_skip_existing_correct_link(self, home_with_existing_files):
        """既存の正しいリンクがスキップされることを確認."""
        source, home, rollbacks = home_with_existing_files

        # Plan 生成
        builder = PlanBuilder(source_dir=source, dest_dir=home)
        plan = builder.build()

        # Executor 作成
        logger = ColoredLogger(name="test")
        ui = UserInterface()
        ui.confirm = lambda msg, default_yes=True: True
        backup_manager = BackupManager(rollbacks_root=rollbacks)
        executor = PlanExecutor(ui=ui, logger=logger, backup_manager=backup_manager)

        # 実行前のリンク先を記録
        vimrc = home / ".vimrc"
        original_link_dest = vimrc.resolve()

        # 実行
        report = executor.execute(plan, dry_run=False)

        # スキップがカウントされていることを確認
        assert report.skipped > 0

        # .vimrc がそのまま残っていることを確認
        assert vimrc.is_symlink()
        assert vimrc.resolve() == original_link_dest

    def test_confirmation_required(self, home_with_existing_files):
        """確認が必要なエントリでユーザー確認が求められることを確認."""
        source, home, rollbacks = home_with_existing_files

        # Plan 生成
        builder = PlanBuilder(source_dir=source, dest_dir=home)
        plan = builder.build()

        # Executor 作成（確認を自動でNo）
        logger = ColoredLogger(name="test")
        ui = UserInterface()
        ui.confirm = lambda msg, default_yes=True: False  # 常に No
        backup_manager = BackupManager(rollbacks_root=rollbacks)
        executor = PlanExecutor(ui=ui, logger=logger, backup_manager=backup_manager)

        # 実行
        executor.execute(plan, dry_run=False)

        # .bashrc は確認でNoを選んだのでスキップされる
        bashrc = home / ".bashrc"
        assert not bashrc.is_symlink()
        assert bashrc.read_text() == "# existing bashrc\n"

        # バックアップは作成されない（何も変更していないため）
        backup_dirs = list(rollbacks.glob("*"))
        assert len(backup_dirs) == 0


class TestPlanExecutorEdgeCases:
    """PlanExecutor のエッジケースのテスト."""

    def test_broken_link_replacement(self, tmp_dotfiles_env):
        """壊れたリンクが正しく置き換えられることを確認."""
        source, home, rollbacks = tmp_dotfiles_env

        # source/ にファイルを作成
        (source / ".bashrc").write_text("# new bashrc\n")

        # home/ に壊れたリンクを作成
        nonexistent_file = home / "nonexistent.txt"
        (home / ".bashrc").symlink_to(nonexistent_file)

        # Plan 生成
        builder = PlanBuilder(source_dir=source, dest_dir=home)
        plan = builder.build()

        # Executor 作成
        logger = ColoredLogger(name="test")
        ui = UserInterface()
        ui.confirm = lambda msg, default_yes=True: True
        backup_manager = BackupManager(rollbacks_root=rollbacks)
        executor = PlanExecutor(ui=ui, logger=logger, backup_manager=backup_manager)

        # 実行
        executor.execute(plan, dry_run=False)

        # 壊れたリンクが正しいリンクに置き換わっていることを確認
        bashrc = home / ".bashrc"
        assert bashrc.is_symlink()
        assert bashrc.resolve() == (source / ".bashrc").resolve()
        assert bashrc.exists()  # リンク先が存在する

    def test_no_backup_for_create_action(self, basic_source):
        """CREATE アクションではバックアップが作成されないことを確認."""
        source, home, rollbacks = basic_source

        # Plan 生成
        builder = PlanBuilder(source_dir=source, dest_dir=home)
        plan = builder.build()

        # Executor 作成
        logger = ColoredLogger(name="test")
        ui = UserInterface()
        ui.confirm = lambda msg, default_yes=True: True
        backup_manager = BackupManager(rollbacks_root=rollbacks)
        executor = PlanExecutor(ui=ui, logger=logger, backup_manager=backup_manager)

        # 実行
        executor.execute(plan, dry_run=False)

        # バックアップディレクトリが作成されていないことを確認
        # （全て新規作成なのでバックアップ不要）
        backup_dirs = list(rollbacks.glob("*"))
        assert len(backup_dirs) == 0
