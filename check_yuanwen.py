#!/usr/bin/env python3
"""改寫字卡文字嗰陣，守住【原文】唔可以變。

點解要有：由廣東話改成書面語，係一個逐句重寫嘅動作。
一個唔小心就會順手「執順」埋古籍引文 —— 咁就等於改咗《說文》。
呢個 project 嘅價值就係建基於「原文一個字都冇改過」，所以要有機器守住。

做法：由 git 攞返改之前嗰版，抽出所有【原文】段落同入面嘅「…」引文，
逐個逐字比。唔同就失敗，而且會指出邊一段變咗。

用法：
  python3 check_yuanwen.py 偉.md              # 同 HEAD 比
  python3 check_yuanwen.py --base main *.md   # 同某個 branch 比
  python3 check_yuanwen.py --list 偉.md       # 淨係列出而家有咩引文
  python3 check_yuanwen.py --dedupe 靜.md     # 去重版：見下面「--dedupe 係咩」

--dedupe 係咩：
  PDF presentation 去重（CLAUDE.md「同一引文超過一行只全抄一次」）要將
  同一條【原文】引文第二次、第三次出現嘅位置，改做「（引文見 §2.1）」呢類
  指回文字。呢種改法用**預設模式**驗會誤判 —— 因為預設模式逐條逐次序比
  （list 比 list），刪走重複出現會即刻判定做「delete」。

  --dedupe 改為比較**唯一引文集合**（set 比 set）：舊版有嘅唯一引文，
  新版一定要原封不動仲喺度（一個字都唔可以變、唔可以完全消失）；
  但同一條引文出現幾多次唔計較——3 次減到 1 次通過，1 次變 0 次（真係刪咗）
  先算失敗。加新引文照樣冇問題。
"""
import difflib
import re
import subprocess
import sys

MARK = '【原文】'
# 「…」『…』 —— 引文本體。呢啲係最唔可以郁嘅部分。
QUOTE = re.compile(r'[「『]([^「」『』]*)[」』]')


def segments(text):
    """抽出所有【原文】段落。"""
    out = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if MARK not in line:
            continue
        if line.lstrip().startswith('|'):
            # 表格：淨係要含住個標記嗰一格，唔好連埋隔籬格
            for cell in line.split('|'):
                if MARK in cell:
                    out.append(cell.strip())
        else:
            seg = line[line.index(MARK):].strip()
            # 「【原文】…：」之後跟住落一段引文嘅寫法，要連埋下面幾行
            if seg.rstrip().endswith(('：', ':')):
                j = i + 1
                while j < len(lines) and lines[j].strip():
                    seg += '\n' + lines[j].strip()
                    j += 1
            out.append(seg)
    return out


def quotes(segs):
    """段落入面所有「…」引文。呢個係最嚴格嗰層。"""
    out = []
    for s in segs:
        out += [q.strip() for q in QUOTE.findall(s) if q.strip()]
    return out


def git_show(base, path):
    try:
        return subprocess.check_output(['git', 'show', '%s:%s' % (base, path)],
                                       stderr=subprocess.DEVNULL).decode('utf-8')
    except subprocess.CalledProcessError:
        return None


def report(path, old, new, kind):
    """回傳 1 代表真係有嘢被改／被刪，0 代表冇問題。

    **淨係新增唔算失敗。** 加新章節（例如 1.7 組合分析引多幾條《說文》）
    本來就會加引文；硬規矩係「已經有嘅引文一個字都唔可以變」，
    唔係「唔准加」。所以只有 delete／replace 先算違規。
    """
    a, b = old, new
    if a == b:
        return 0
    ops = difflib.SequenceMatcher(None, a, b).get_opcodes()
    bad = [o for o in ops if o[0] in ('delete', 'replace')]
    if not bad:
        added = sum(j2 - j1 for tag, _, _, j1, j2 in ops if tag == 'insert')
        print('✓ %s：原有%s一條都冇變，另外新增咗 %d 條' % (path, kind, added))
        return 0
    print('\n✗ %s 嘅%s被改咗或者刪咗：' % (path, kind))
    shown = 0
    for tag, i1, i2, j1, j2 in bad:
        for x in a[i1:i2]:
            print('   － %s' % x[:160])
            shown += 1
        for x in b[j1:j2]:
            print('   ＋ %s' % x[:160])
            shown += 1
        if shown > 24:
            print('   …（仲有）')
            break
    return 1


def dedupe_report(path, old_qs, new_qs):
    """--dedupe 版嘅 report()：比較唯一引文集合，唔理次序、唔理重複次數。

    回傳 1 代表有唯一引文完全消失咗（真係刪咗嘢），0 代表冇問題。
    """
    old_set, new_set = set(old_qs), set(new_qs)
    missing = old_set - new_set
    if missing:
        print('\n✗ %s（--dedupe）：呢啲【原文】引文喺新版一次都搵唔返：' % path)
        for q in sorted(missing):
            print('   － 「%s」' % q[:160])
        return 1
    added = len(new_set - old_set)
    old_occurrences = len(old_qs)
    new_occurrences = len(new_qs)
    print('✓ %s（--dedupe）：%d 條唯一引文全部仲喺度（另加 %d 條新嘅）；'
          '出現次數由 %d 減到 %d'
          % (path, len(old_set), added, old_occurrences, new_occurrences))
    return 0


def main():
    args = sys.argv[1:]
    base = 'HEAD'
    if '--base' in args:
        i = args.index('--base')
        base = args[i + 1]
        del args[i:i + 2]
    listing = '--list' in args
    dedupe = '--dedupe' in args
    args = [a for a in args if not a.startswith('--')]
    if not args:
        sys.exit('用法：python3 check_yuanwen.py [--base <ref>] [--dedupe] <檔案.md>…')

    bad = 0
    for path in args:
        new_text = open(path, encoding='utf-8').read()
        new_segs = segments(new_text)
        new_qs = quotes(new_segs)

        if listing:
            print('── %s：%d 段【原文】，%d 條引文' % (path, len(new_segs), len(new_qs)))
            for q in new_qs:
                print('   「%s」' % q)
            continue

        old_text = git_show(base, path)
        if old_text is None:
            print('── %s：%s 度未有呢個檔，跳過（新卡）' % (path, base))
            continue
        old_segs = segments(old_text)
        old_qs = quotes(old_segs)

        if dedupe:
            bad += dedupe_report(path, old_qs, new_qs)
            continue

        # 引文本體係硬規矩，一個字都唔可以變
        bad += report(path, old_qs, new_qs, '引文（「…」）')
        # 段落文字可以有少少差別（例如標點統一），淨係出警告
        if old_segs != new_segs and old_qs == new_qs:
            print('！ %s：【原文】段落嘅外圍文字有改動，但引文本體冇變 —— 請自己確認一次'
                  % path)
        if old_qs == new_qs:
            print('✓ %s：%d 條【原文】引文完全一致' % (path, len(new_qs)))

    if bad:
        what = '有唯一引文喺去重時被刪咗' if dedupe else '嘅【原文】引文被改咗'
        print('\n有 %d 個檔%s。呢個係硬規矩，要改返。' % (bad, what))
        sys.exit(1)


if __name__ == '__main__':
    main()
