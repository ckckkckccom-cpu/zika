#!/usr/bin/env python3
"""封存一張字卡嘅現有 PDF，之後先好升級佢。

點解要有：已經出版過嘅嘢唔應該消失。git 歷史其實一直都留住，
但埋喺歷史入面唔方便攞；呢度將佢哋集中放喺 archive/，
網站每張卡底部亦都會連出去。

版本號 ＝ **格式版本**（v1 結構＋意思／v2 再加同音層同交叉核對／
v3 再加推理網絡、總覽、組合同做部件時）。
唔係每次改字都封存 —— 咁樣 repo 會爆，而且大部分改動唔值得留一版。

用法：
  python3 archive_card.py 靜          # 用佢而家嘅格式版本做號碼
  python3 archive_card.py 靜 --as 2   # 明確指定版本號
  python3 archive_card.py --list      # 睇下封存咗啲咩

**升級格式之前一定要跑呢個**，否則舊版 PDF 會俾新版蓋過。
"""
import os
import shutil
import sys

import cardfmt
import fontkit

ROOT = fontkit.ROOT
ARCHIVE = os.path.join(ROOT, 'archive')


def listing():
    """回傳 {字: [(版本, 檔名), …]}，版本由細到大。"""
    out = {}
    if not os.path.isdir(ARCHIVE):
        return out
    for fn in sorted(os.listdir(ARCHIVE)):
        if not fn.endswith('.pdf') or '_v' not in fn:
            continue
        ch, _, ver = fn[:-4].rpartition('_v')
        if ch and ver.isdigit():
            out.setdefault(ch, []).append((int(ver), fn))
    for ch in out:
        out[ch].sort()
    return out


def archive(ch, version=None):
    src = os.path.join(ROOT, 'pdf', '%s.pdf' % ch)
    if not os.path.exists(src):
        return '✗ %s：搵唔到 pdf/%s.pdf —— 請先跑 build_pdf.py' % (ch, ch)
    if version is None:
        card = cardfmt.parse_card(os.path.join(ROOT, '%s.md' % ch))
        version = card.format_version
    os.makedirs(ARCHIVE, exist_ok=True)
    dest = os.path.join(ARCHIVE, '%s_v%d.pdf' % (ch, version))
    if os.path.exists(dest):
        return '・%s v%d 已經封存過，冇覆蓋（已出版嘅嘢唔應該改）' % (ch, version)
    shutil.copy2(src, dest)
    return '✓ 封存咗 archive/%s_v%d.pdf（%.2f MB）' % (
        ch, version, os.path.getsize(dest) / 1e6)


def main():
    args = sys.argv[1:]
    if '--list' in args or not args:
        got = listing()
        if not got:
            print('archive/ 入面暫時乜都冇')
            return
        print('已封存嘅版本：')
        for ch in sorted(got):
            vs = '、'.join('v%d' % v for v, _ in got[ch])
            size = sum(os.path.getsize(os.path.join(ARCHIVE, f)) for _, f in got[ch])
            print('   %s  %s  （共 %.1f MB）' % (ch, vs, size / 1e6))
        return
    version = None
    if '--as' in args:
        i = args.index('--as')
        version = int(args[i + 1])
        del args[i:i + 2]
    for ch in [a for a in args if not a.startswith('--')]:
        print(archive(ch, version))


if __name__ == '__main__':
    main()
