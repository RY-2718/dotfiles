#!/usr/bin/env python3
"""
バックアップファイル名生成ロジックのテスト

現在の symlink.py の重複回避ロジックをテストする
"""

def get_backup_name(original_name: str, counter: int) -> str:
    """
    バックアップファイル名を生成する（最適化版）

    Args:
        original_name: 元のファイル名
        counter: 連番

    Returns:
        バックアップファイル名
    """
    # ファイル名の構造を一度だけ解析
    if original_name.startswith('.'):
        # dotfileの場合
        remaining = original_name[1:]  # 最初のピリオドを除く
        if '.' in remaining:
            # dotfileで拡張子あり: .config.json -> .config_1.json
            parts = remaining.split('.')
            base = '.' + '.'.join(parts[:-1])
            ext = parts[-1]
            return f"{base}_{counter}.{ext}"
        else:
            # dotfileで拡張子なし: .bashrc -> .bashrc_1
            return f"{original_name}_{counter}"
    elif '.' in original_name and not original_name.endswith('.'):
        # 通常ファイルで拡張子あり: file.txt -> file_1.txt
        parts = original_name.split('.')
        base = '.'.join(parts[:-1])
        ext = parts[-1]
        return f"{base}_{counter}.{ext}"
    else:
        # 拡張子なし、または末尾ピリオド: README -> README_1, script. -> script._1
        return f"{original_name}_{counter}"
def test_backup_naming():
    """バックアップファイル名生成のテスト"""

    test_cases = [
        # (元ファイル名, 期待される結果, 説明)
        ('.bashrc', '.bashrc_1', 'dotfile、拡張子なし'),
        ('.config.json', '.config_1.json', 'dotfile、拡張子あり'),
        ('.vimrc.bak', '.vimrc_1.bak', 'dotfile、複数拡張子'),
        ('.gitignore', '.gitignore_1', 'dotfile、拡張子なし'),
        ('file.txt', 'file_1.txt', '通常ファイル、拡張子あり'),
        ('README', 'README_1', '通常ファイル、拡張子なし'),
        ('script.', 'script._1', '末尾ピリオド'),
        ('.hidden.', '.hidden._1', 'dotfile、末尾ピリオド'),
        ('test.tar.gz', 'test.tar_1.gz', '複合拡張子'),
        ('.env.local', '.env_1.local', 'dotfile、複合拡張子'),
        ('config', 'config_1', '拡張子なし'),
    ]

    print("=" * 60)
    print("バックアップファイル名生成テスト")
    print("=" * 60)
    print(f"{'元ファイル名':<15} {'生成結果':<20} {'期待結果':<20} {'結果'}")
    print("-" * 60)

    success_count = 0
    total_count = len(test_cases)

    for original, expected, description in test_cases:
        actual = get_backup_name(original, 1)
        status = "✅ OK" if actual == expected else "❌ NG"

        print(f"{original:<15} {actual:<20} {expected:<20} {status}")

        if actual == expected:
            success_count += 1
        else:
            print(f"  → 説明: {description}")
            print(f"  → 期待: {expected}")
            print(f"  → 実際: {actual}")

    print("-" * 60)
    print(f"テスト結果: {success_count}/{total_count} 成功")

    if success_count == total_count:
        print("🎉 全てのテストが成功しました！")
    else:
        print(f"⚠️  {total_count - success_count}個のテストが失敗しました。")

    return success_count == total_count


def test_sequential_naming():
    """連続バックアップのテスト"""
    print("\n" + "=" * 60)
    print("連続バックアップのテスト")
    print("=" * 60)

    test_files = ['.bashrc', '.config.json', 'file.txt']

    for filename in test_files:
        print(f"\n📁 {filename} の連続バックアップ:")
        for i in range(1, 4):
            backup_name = get_backup_name(filename, i)
            print(f"  {i}回目: {backup_name}")


def test_performance():
    """パフォーマンステスト"""
    import time

    print("\n" + "=" * 60)
    print("パフォーマンステスト")
    print("=" * 60)

    test_files = ['.bashrc', '.config.json', '.vimrc.bak', 'file.txt', 'README']
    iterations = 10000

    start_time = time.time()
    for _ in range(iterations):
        for filename in test_files:
            for counter in range(1, 6):  # 1〜5回の重複想定
                _ = get_backup_name(filename, counter)
    end_time = time.time()

    total_calls = iterations * len(test_files) * 5
    elapsed = end_time - start_time
    calls_per_second = total_calls / elapsed

    print(f"総実行回数: {total_calls:,} 回")
    print(f"実行時間: {elapsed:.4f} 秒")
    print(f"1秒あたりの実行回数: {calls_per_second:,.0f} 回/秒")
    print(f"1回あたりの実行時間: {elapsed/total_calls*1000000:.2f} マイクロ秒")


if __name__ == "__main__":
    test_backup_naming()
    test_sequential_naming()
    test_performance()
if __name__ == "__main__":
    test_backup_naming()
    test_sequential_naming()