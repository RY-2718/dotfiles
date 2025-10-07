import unittest
import shutil
import os
from pathlib import Path
import subprocess

TEST_HOME = Path("test_env/home")
DOTFILES_DIR = Path("test_env/dotfiles")
INSTALL_SCRIPT = Path("../install.py")

class DotfilesInstallerTest(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(TEST_HOME, ignore_errors=True)
        shutil.rmtree(DOTFILES_DIR, ignore_errors=True)
        TEST_HOME.mkdir(parents=True, exist_ok=True)
        DOTFILES_DIR.mkdir(parents=True, exist_ok=True)
        (DOTFILES_DIR / ".vimrc").write_text("set number\n")
        (DOTFILES_DIR / ".bashrc").write_text("export TEST=1\n")
        (TEST_HOME / ".vimrc").write_text("old config\n")
        (DOTFILES_DIR / ".installignore").write_text(".bashrc\n")

    def test_backup_and_symlink(self):
        result = subprocess.run(
            ["python3", str(INSTALL_SCRIPT), "--force", "--test-mode", str(TEST_HOME)],
            capture_output=True, text=True
        )
        self.assertIn("バックアップ", result.stdout)
        backups = list(TEST_HOME.glob(".dotfiles_backup_*"))
        self.assertTrue(backups)
        backup_vimrc = list(backups[0].glob(".vimrc*"))
        self.assertTrue(backup_vimrc)
        self.assertTrue((TEST_HOME / ".vimrc").is_symlink())
        self.assertFalse((TEST_HOME / ".bashrc").exists())

    def test_dry_run(self):
        before = (TEST_HOME / ".vimrc").read_text()
        result = subprocess.run(
            ["python3", str(INSTALL_SCRIPT), "--dry-run", "--test-mode", str(TEST_HOME)],
            capture_output=True, text=True
        )
        after = (TEST_HOME / ".vimrc").read_text()
        self.assertEqual(before, after)
        self.assertIn("プレビュー", result.stdout)

    # def test_rollback(self):
    #     subprocess.run(
    #         ["python3", str(INSTALL_SCRIPT), "--force", "--test-mode", str(TEST_HOME)],
    #         capture_output=True, text=True
    #     )
    #     backup_dir = list(TEST_HOME.glob(".dotfiles_backup_*"))[0]
    #     subprocess.run(
    #         ["python3", str(INSTALL_SCRIPT), "--force", "--rollback", str(backup_dir), "--test-mode", str(TEST_HOME)],
    #         capture_output=True, text=True
    #     )
    #     content = (TEST_HOME / ".vimrc").read_text()
    #     self.assertEqual(content, "old config\n")

if __name__ == "__main__":
    unittest.main()
