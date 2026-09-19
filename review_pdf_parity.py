#!/usr/bin/env python3
"""證明改版面之後，PDF 入面嘅字一個都冇少。

點解要有呢個：改 print 版面（縮字、壓行、加分界線）會令表格同段落
**重新斷行**。咁樣逐行比對就一定失敗——唔係因為少咗嘢，
而係因為「…cuhk.edu.hk/L」呢類斷行片段對唔上。
用錯粒度去驗，會得出「少咗 60 行」呢種嚇人但無意義嘅結論。

正確做法：將成份 PDF 嘅文字接成**一條冇空白嘅長字串**再比。
斷行點喺邊完全唔影響呢條字串，所以剩低嘅差異先係真差異。

用法：
  python3 review_pdf_parity.py 舊資料夾 [字…]     # 預設驗全部卡
  python3 review_pdf_parity.py --min 20 舊資料夾   # 只報 ≥20 字嘅差異

判斷準則：
  刪走（舊有新冇）    → 有可能真係少咗嘢，要逐段睇
  新增（新有舊冇）    → 正常（例如新加嘅「詳細考證」分部標題）
"""
import difflib
import os
import re
import sys
import unicodedata

from pypdf import PdfReader

import fontkit

ROOT = fontkit.ROOT
DEFAULT_MIN = 8


def pdf_text(path):
    """抽晒一份 PDF 嘅文字，正規化，剝走所有空白同頁碼。"""
    r = PdfReader(path)
    txt = '\n'.join((p.extract_text() or '') for p in r.pages)
    txt = unicodedata.normalize('NFKC', txt)
    # 頁腳「5 / 33」：純粹版面，唔算內容
    txt = re.sub(r'\b\d+\s*/\s*\d+\b', '', txt)
    return re.sub(r'\s+', '', txt)


def compare(ch, old_path, new_path, min_run):
    old, new = pdf_text(old_path), pdf_text(new_path)
    sm = difflib.SequenceMatcher(None, old, new, autojunk=False)

    deleted, moved, added = [], [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ('delete', 'replace') and (i2 - i1) >= min_run:
            run = old[i1:i2]
            # diff 會將「搬咗位」當成「刪咗再加」。真正要問嘅係：
            # 呢段字喺新版全文入面仲搵唔搵得返？搵得返就唔算少咗嘢
            # ——可能只係表格重排，亦可能係特登去重（同一段本來印兩次，
            # 而家印一次，另一次仍然喺度）。
            (moved if run in new else deleted).append(run)
        if tag in ('insert', 'replace') and (j2 - j1) >= min_run:
            added.append(new[j1:j2])

    print('══ %s ══  舊 %d 字 → 新 %d 字（%+d）'
          % (ch, len(old), len(new), len(new) - len(old)))
    if deleted:
        print('  ✗ 真係搵唔返（≥%d 字）共 %d 段：' % (min_run, len(deleted)))
        for d in deleted[:12]:
            print('       － %s' % d[:110])
        if len(deleted) > 12:
            print('       …（仲有 %d 段）' % (len(deleted) - 12))
    else:
        print('  ✓ 冇任何 ≥%d 字嘅內容消失' % min_run)
    if moved:
        print('  ・搬咗位／去咗重複（≥%d 字）共 %d 段，新版全文仍然搵得返：'
              % (min_run, len(moved)))
        for m in moved[:6]:
            print('       ～ %s' % m[:110])
        if len(moved) > 6:
            print('       …（仲有 %d 段）' % (len(moved) - 6))
    if added:
        print('  ＋ 新版多咗（≥%d 字）共 %d 段（正常，例如新加嘅分部標題）：'
              % (min_run, len(added)))
        for a in added[:6]:
            print('       ＋ %s' % a[:110])
        if len(added) > 6:
            print('       …（仲有 %d 段）' % (len(added) - 6))
    return bool(deleted)


def main():
    args = sys.argv[1:]
    min_run = DEFAULT_MIN
    if '--min' in args:
        i = args.index('--min')
        min_run = int(args[i + 1])
        del args[i:i + 2]
    if not args:
        sys.exit('用法：python3 review_pdf_parity.py <舊 PDF 資料夾> [字…]')

    old_dir = args[0]
    chars = args[1:] or fontkit.card_files(ROOT)

    bad = []
    for ch in chars:
        o = os.path.join(old_dir, '%s.pdf' % ch)
        n = os.path.join(ROOT, 'pdf', '%s.pdf' % ch)
        if not (os.path.exists(o) and os.path.exists(n)):
            print('── %s：舊版或新版 PDF 搵唔到，跳過' % ch)
            continue
        if compare(ch, o, n, min_run):
            bad.append(ch)
        print()

    if bad:
        print('✗ 呢幾張卡有內容喺新版搵唔返：%s' % '、'.join(bad))
        print('  逐段睇下係咪真係少咗嘢（抽字有時會將直排表格拆散，要人眼確認）。')
        return 1
    print('✓ 全部卡：新版 PDF 一個字都冇少。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
