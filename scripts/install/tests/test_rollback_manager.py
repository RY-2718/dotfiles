"""RollbackManager のテスト."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.install.pkg.rollback_manager import RollbackManager


class MockUI:
    """テスト用のモック UI."""

    def __init__(self, auto_confirm: bool = True):
        self.auto_confirm = auto_confirm
        self.confirmations = []

    def confirm(self, message: str, default_yes: bool = False) -> bool:
        self.confirmations.append(message)
        return self.auto_confirm


class TestRollbackManager(unittest.TestCase):
    """RollbackManager の基本動作のテスト."""

    def setUp(self):
        """各テストの前に実行される共通セットアップ."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.test_dir.name)
        self.target_root = self.tmp_path / "home"
        self.archive_root = self.tmp_path / "rollbacks"

        self.target_root.mkdir()
        self.archive_root.mkdir()

    def tearDown(self):
        """各テストの後に実行されるクリーンアップ."""
        self.test_dir.cleanup()

    def test_restore_regular_file(self):
        """通常のファイルを復元できることを確認."""
        # バックアップアーカイブを作成
        archive = self.archive_root / "20240101_120000"
        archive.mkdir()
        (archive / ".bashrc").write_text("# backup bashrc\n")

        # 現在のホームディレクトリに別の内容のファイルがある
        (self.target_root / ".bashrc").write_text("# current bashrc\n")

        # リストア実行（自動承認）
        ui = MockUI(auto_confirm=True)
        manager = RollbackManager(target_root=self.target_root, ui=ui)
        manager.restore_archive(archive, restore_all=True)

        # ファイルが復元されていることを確認
        bashrc = self.target_root / ".bashrc"
        self.assertTrue(bashrc.exists())
        self.assertEqual(bashrc.read_text(), "# backup bashrc\n")

    def test_restore_symlink(self):
        """シンボリックリンクを復元できることを確認."""
        # バックアップアーカイブを作成
        archive = self.archive_root / "20240101_120000"
        archive.mkdir()

        # .vimrc.link ファイル（リンク先情報を保存）
        link_target = "/Users/test/dotfiles/source/.vimrc"
        (archive / ".vimrc.link").write_text(link_target)

        # リストア実行
        ui = MockUI(auto_confirm=True)
        manager = RollbackManager(target_root=self.target_root, ui=ui)
        manager.restore_archive(archive, restore_all=True)

        # シンボリックリンクが作成されていることを確認
        vimrc = self.target_root / ".vimrc"
        self.assertTrue(vimrc.is_symlink())
        self.assertEqual(str(vimrc.readlink()), link_target)

    def test_restore_nested_file(self):
        """ネストしたディレクトリ内のファイルを復元できることを確認."""
        # バックアップアーカイブを作成
        archive = self.archive_root / "20240101_120000"
        archive.mkdir()
        (archive / ".config").mkdir()
        (archive / ".config" / "test.conf").write_text("test=1\n")

        # リストア実行
        ui = MockUI(auto_confirm=True)
        manager = RollbackManager(target_root=self.target_root, ui=ui)
        manager.restore_archive(archive, restore_all=True)

        # ファイルが復元されていることを確認
        config = self.target_root / ".config" / "test.conf"
        self.assertTrue(config.exists())
        self.assertEqual(config.read_text(), "test=1\n")

    def test_restore_with_confirmation(self):
        """確認モードでユーザーに確認が求められることを確認."""
        # バックアップアーカイブを作成
        archive = self.archive_root / "20240101_120000"
        archive.mkdir()
        (archive / ".bashrc").write_text("# backup bashrc\n")
        (archive / ".vimrc").write_text("# backup vimrc\n")

        # リストア実行（確認モード、自動承認）
        ui = MockUI(auto_confirm=True)
        manager = RollbackManager(target_root=self.target_root, ui=ui)
        manager.restore_archive(archive, restore_all=False)

        # 確認が求められたことを確認
        self.assertEqual(len(ui.confirmations), 2)
        self.assertIn(".bashrc", ui.confirmations[0])
        self.assertIn(".vimrc", ui.confirmations[1])

    def test_restore_with_rejection(self):
        """確認を拒否した場合にファイルが復元されないことを確認."""
        # バックアップアーカイブを作成
        archive = self.archive_root / "20240101_120000"
        archive.mkdir()
        (archive / ".bashrc").write_text("# backup bashrc\n")

        # リストア実行（確認モード、自動拒否）
        ui = MockUI(auto_confirm=False)
        manager = RollbackManager(target_root=self.target_root, ui=ui)
        manager.restore_archive(archive, restore_all=False)

        # ファイルが復元されていないことを確認
        bashrc = self.target_root / ".bashrc"
        self.assertFalse(bashrc.exists())

    def test_restore_overwrites_existing_file(self):
        """既存のファイルを上書きして復元できることを確認."""
        # バックアップアーカイブを作成
        archive = self.archive_root / "20240101_120000"
        archive.mkdir()
        (archive / ".bashrc").write_text("# backup bashrc\n")

        # 既存のファイルを作成
        (self.target_root / ".bashrc").write_text("# existing bashrc\n")

        # リストア実行
        ui = MockUI(auto_confirm=True)
        manager = RollbackManager(target_root=self.target_root, ui=ui)
        manager.restore_archive(archive, restore_all=True)

        # ファイルが上書きされていることを確認
        bashrc = self.target_root / ".bashrc"
        self.assertEqual(bashrc.read_text(), "# backup bashrc\n")

    def test_restore_overwrites_existing_symlink(self):
        """既存のシンボリックリンクを上書きして復元できることを確認."""
        # バックアップアーカイブを作成
        archive = self.archive_root / "20240101_120000"
        archive.mkdir()
        (archive / ".bashrc").write_text("# backup bashrc\n")

        # 既存のシンボリックリンクを作成
        dummy_target = self.tmp_path / "dummy.txt"
        dummy_target.write_text("dummy")
        (self.target_root / ".bashrc").symlink_to(dummy_target)

        # リストア実行
        ui = MockUI(auto_confirm=True)
        manager = RollbackManager(target_root=self.target_root, ui=ui)
        manager.restore_archive(archive, restore_all=True)

        # シンボリックリンクが通常ファイルに置き換わっていることを確認
        bashrc = self.target_root / ".bashrc"
        self.assertFalse(bashrc.is_symlink())
        self.assertEqual(bashrc.read_text(), "# backup bashrc\n")

    def test_restore_nonexistent_archive_raises_error(self):
        """存在しないアーカイブを指定した場合にエラーが発生することを確認."""
        nonexistent = self.archive_root / "nonexistent"

        ui = MockUI(auto_confirm=True)
        manager = RollbackManager(target_root=self.target_root, ui=ui)

        with self.assertRaises(FileNotFoundError):
            manager.restore_archive(nonexistent, restore_all=True)

    def test_iter_backup_entries_with_symlinks(self):
        """バックアップエントリの列挙でシンボリックリンクを正しく識別できることを確認."""
        # バックアップアーカイブを作成
        archive = self.archive_root / "20240101_120000"
        archive.mkdir()

        # 通常ファイル
        (archive / ".bashrc").write_text("# backup bashrc\n")

        # シンボリックリンク（.link ファイル）
        (archive / ".vimrc.link").write_text("/path/to/dotfiles/.vimrc")

        # ネストしたファイル
        (archive / ".config").mkdir()
        (archive / ".config" / "test.conf").write_text("test=1\n")

        ui = MockUI(auto_confirm=True)
        manager = RollbackManager(target_root=self.target_root, ui=ui)

        # エントリを列挙
        entries = list(manager._iter_backup_entries(archive))

        # 3つのエントリがあることを確認
        self.assertEqual(len(entries), 3)

        # エントリの内容を確認
        entry_dict = {str(path): info for path, info in entries}
        self.assertIn(".bashrc", entry_dict)
        self.assertEqual(entry_dict[".bashrc"], "file")
        self.assertIn(".vimrc", entry_dict)
        self.assertEqual(entry_dict[".vimrc"], "symlink")
        self.assertIn(".config/test.conf", entry_dict)
        self.assertEqual(entry_dict[".config/test.conf"], "file")

    def test_restore_replaces_symlink_with_different_target(self):
        """異なるリンク先を持つシンボリックリンクを正しく置き換えられることを確認."""
        # バックアップアーカイブを作成（古いリンク先）
        archive = self.archive_root / "20240101_120000"
        archive.mkdir()
        old_target = "/old/path/to/dotfiles/.bashrc"
        (archive / ".bashrc.link").write_text(old_target)

        # 現在のホームディレクトリに新しいリンク先のシンボリックリンクがある
        new_target = self.tmp_path / "new_dotfiles" / ".bashrc"
        new_target.parent.mkdir()
        new_target.write_text("# new bashrc\n")
        (self.target_root / ".bashrc").symlink_to(new_target)

        # リストア実行
        ui = MockUI(auto_confirm=True)
        manager = RollbackManager(target_root=self.target_root, ui=ui)
        manager.restore_archive(archive, restore_all=True)

        # シンボリックリンクが古いリンク先に戻っていることを確認
        bashrc = self.target_root / ".bashrc"
        self.assertTrue(bashrc.is_symlink())
        self.assertEqual(str(bashrc.readlink()), old_target)

    def test_multiple_files_restore_order(self):
        """複数ファイルが正しい順序で復元されることを確認."""
        # バックアップアーカイブを作成
        archive = self.archive_root / "20240101_120000"
        archive.mkdir()
        (archive / ".zshrc").write_text("# zshrc\n")
        (archive / ".bashrc").write_text("# bashrc\n")
        (archive / ".vimrc").write_text("# vimrc\n")

        # リストア実行
        ui = MockUI(auto_confirm=True)
        manager = RollbackManager(target_root=self.target_root, ui=ui)
        manager.restore_archive(archive, restore_all=True)

        # すべてのファイルが復元されていることを確認
        self.assertTrue((self.target_root / ".bashrc").exists())
        self.assertTrue((self.target_root / ".vimrc").exists())
        self.assertTrue((self.target_root / ".zshrc").exists())

        # 内容も正しいことを確認
        self.assertEqual((self.target_root / ".bashrc").read_text(), "# bashrc\n")
        self.assertEqual((self.target_root / ".vimrc").read_text(), "# vimrc\n")
        self.assertEqual((self.target_root / ".zshrc").read_text(), "# zshrc\n")


if __name__ == "__main__":
    unittest.main()
