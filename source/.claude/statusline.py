#!/usr/bin/env python3
"""Claude Code statusline: プログレスバー付き使用率表示"""
import json, sys, subprocess, os, time

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

data = json.load(sys.stdin)

# ── ANSI装飾 ──
BLOCKS = ' ▏▎▍▌▋▊▉█'
R = '\033[0m'
DIM = '\033[2m'
GREEN = '\033[32m'
CYAN = '\033[36m'

# ── 表示パーツ生成 ──

def gradient(pct):
    """使用率に応じた色（緑→黄→赤）"""
    if pct < 50:
        r = int(pct * 5.1)
        return f'\033[38;2;{r};200;80m'
    else:
        g = int(200 - (pct - 50) * 4)
        return f'\033[38;2;255;{max(g,0)};60m'

def bar(pct, width=10):
    """プログレスバー文字列を生成"""
    pct = min(max(pct, 0), 100)
    filled = pct * width / 100
    full = int(filled)
    frac = int((filled - full) * 8)
    b = '█' * full
    if full < width:
        b += BLOCKS[frac]
        b += '░' * (width - full - 1)
    return b

def fmt_pct(label, pct):
    """ラベル付きプログレスバー（例: ctx ██░░ 20%）"""
    p = round(pct)
    return f'{label} {gradient(pct)}{bar(pct)} {p}%{R}'

def fmt_remaining(resets_at):
    """resets_atまでの残り時間を「残Nh Mm」形式で整形（1時間未満は「残Mm」）"""
    remain_min = max(int((resets_at - time.time()) / 60), 0)
    hours, minutes = divmod(remain_min, 60)
    if hours > 0:
        return f'残{hours}h{minutes}m'
    return f'残{minutes}m'

def get_git_branch():
    """現在のgitブランチ名を取得（git管理外ならNone）"""
    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None

# ── パーツ組み立て ──
parts = []

# モデル名
model = data.get('model', {}).get('display_name', 'Claude')
parts.append(model)

# カレントディレクトリ名（起動時のディレクトリ。cdでは変わらない）
cwd = data.get('workspace', {}).get('current_dir', '')
if cwd:
    home = os.path.expanduser('~')
    display_cwd = cwd.replace(home, '~', 1)
    parts.append(f'{GREEN}{display_cwd}{R}')

# gitブランチ
branch = get_git_branch()
if branch:
    parts.append(f'{CYAN}⎇ {branch}{R}')

# コンテキストウィンドウ使用率
ctx = data.get('context_window', {}).get('used_percentage')
if ctx is not None:
    parts.append(fmt_pct('ctx', ctx))

# 5時間レートリミット
five_hour = data.get('rate_limits', {}).get('five_hour', {})
five = five_hour.get('used_percentage')
if five is not None:
    five_str = fmt_pct('5h', five)
    resets_at = five_hour.get('resets_at')
    if resets_at is not None:
        five_str += f' {DIM}{fmt_remaining(resets_at)}{R}'
    parts.append(five_str)

# 7日間レートリミット
week = data.get('rate_limits', {}).get('seven_day', {}).get('used_percentage')
if week is not None:
    parts.append(fmt_pct('7d', week))

# ── 出力 ──
print(f'{DIM}│{R}'.join(f' {p} ' for p in parts), end='')
