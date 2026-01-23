"""
ユーザーインターフェースモジュール

ユーザーとの対話機能を提供
"""

import sys


class UserInterface:
    """ユーザーインターフェースクラス"""

    def __init__(self, force_mode: bool = False):
        self.force_mode = force_mode

    def confirm(self, message: str, default_yes: bool = True) -> bool:
        """
        ユーザーに確認を求める

        Args:
            message: 確認メッセージ
            default_yes: デフォルトで Yes にするか

        Returns:
            True: Yes, False: No
        """
        if self.force_mode:
            return True

        if default_yes:
            prompt = f"{message} [Y/n]: "
        else:
            prompt = f"{message} [y/N]: "

        while True:
            try:
                response = input(prompt).strip().lower()

                if response in ("y", "yes"):
                    return True
                elif response in ("n", "no"):
                    return False
                elif response == "":
                    return default_yes
                else:
                    print("無効な入力です。y/n で回答してください。")

            except KeyboardInterrupt:
                print("\n操作がキャンセルされました")
                sys.exit(130)
            except EOFError:
                print("\n入力が終了しました")
                return False

    def select_from_list(self, items: list, message: str) -> str | None:
        """
        リストから項目を選択

        Args:
            items: 選択肢のリスト
            message: 選択を促すメッセージ

        Returns:
            選択された項目（キャンセル時はNone）
        """
        if not items:
            return None

        if len(items) == 1:
            return items[0]

        print(f"\n{message}")
        for i, item in enumerate(items, 1):
            print(f"  {i}. {item}")
        print("  0. キャンセル")

        while True:
            try:
                response = input(f"選択してください [1-{len(items)}]: ").strip()

                if response == "0":
                    return None

                try:
                    index = int(response) - 1
                    if 0 <= index < len(items):
                        return items[index]
                    else:
                        print(f"1から{len(items)}の範囲で入力してください。")
                except ValueError:
                    print("数字を入力してください。")

            except KeyboardInterrupt:
                print("\n操作がキャンセルされました")
                return None
            except EOFError:
                print("\n入力が終了しました")
                return None

    def show_summary(self, title: str, items: dict):
        """
        処理概要を表示

        Args:
            title: タイトル
            items: 項目と数のディクショナリ
        """
        print(f"\n=== {title} ===")
        for key, value in items.items():
            print(f"  {key}: {value}個")

    def show_process_info(self):
        """処理内容の説明を表示"""
        print("\n以下の処理を実行します:")
        print("  1. 既存dotfilesのバックアップ")
        print("  2. dotfilesのシンボリックリンク作成")
        print("  3. テンプレートディレクトリのコピー")
