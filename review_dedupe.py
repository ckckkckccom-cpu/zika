#!/usr/bin/env python3
"""PDF 去重（C2–C4）嘅機械比對安全網 —— 俾審核 AI（R1）／人手覆核用。

呢個 script **唔做判斷**，淨係機械咁列出前後有咩分別，等審核嗰個知道要
睇邊度。真正判斷「呢個刪法啱唔啱」係 R1 審核 AI 嘅事，唔係呢個 script 嘅事
——尤其係「（見 §x.y）」指返嗰個位置，呢度只做粗略檢查（嗰節仲有冇
【原文】標記），唔會逐條引文核對返去邊個位置。

比對嘅單位（全部係「唔理次序、唔理重複次數」嘅集合比較）：
  - 唯一【原文】引文（借用 check_yuanwen.py 嘅 segments/quotes）
  - 表格記錄嘅身份（每列第一格），唔係成行 string 比——
    去重成日淨係改一格入面嘅長引文，唔可以誤判做「成行消失」
  - 唯一要點行（≥15 字嘅段落／列點，跳過表格、標題、圖片行）
  - 四個標記（原文／觀察／分歧／引申）各自嘅出現次數
  - 標題樹（## ### 一路到 ####）
  - 圖片數（![...](...）
  - §5 來源清單、§6 存疑／未驗證 嘅項目數

輸出分三截：
  (a) 舊版有、新版完全冇嘅單位 —— 紅色，呢啲一定要查
  (b) 新版每一處「（見 §x.y）」，嗰節係咪仲有內容 —— 淺色警示，人手覆核
  (c) 前後字數／行數／表數，純資訊

用法：
  python3 review_dedupe.py 靜.md 財.md 美.md
  python3 review_dedupe.py --base main 靜.md
"""
import collections
import difflib
import re
import sys

import cardfmt
import check_yuanwen as cy

MARKS = ('原文', '觀察', '分歧', '引申')
MARK_RE = re.compile(r'【(原文|觀察|分歧|引申)】')
HEADING_RE = re.compile(r'^(#{2,4})\s*(.+?)\s*$', re.M)
TABLE_SEP_RE = re.compile(r'^\|[\s:\-|]+\|$')
IMAGE_RE = re.compile(r'!\[[^\]]*\]\([^)]+\)')
LIST_ITEM_RE = re.compile(r'^\s*(?:[-*]|\d+[.、．])\s')
# 「（見 §1.7）」「（引文見 2.1）」「（見總覽）」之類嘅指回標記
BACKREF_RE = re.compile(r'[（(](?:引文)?見\s*(?:總覽|§?\s*(\d+(?:\.\d+)*))[）)]')


def strip_fm(text):
    m = cardfmt._FM.match(text)
    return text[m.end():] if m else text


def table_rows(body):
    out = []
    for line in body.splitlines():
        s = line.strip()
        if s.startswith('|') and s.count('|') >= 3 and not TABLE_SEP_RE.match(s):
            out.append(s)
    return out


def table_row_keys(body):
    """表格每一列嘅『身份』（第一格文字），唔理其他格點變。

    去重編輯成日淨係改一格入面嘅長引文（改成「見 §x.y」），如果用成行
    string 逐字比，呢種正常編輯都會被當做「成行消失」報大假警報。
    真正要捉嘅係「成條記錄（例如同族字表入面『靖』嗰一列）冧咗」，
    唔係「呢格文字執過」——所以淨係睇第一格（通常係字／類別呢啲識別碼）。

    局限：如果兩個唔同表格啱啱好第一格撞名，會漏檢；R1 仲要親身睇 diff。
    """
    out = []
    for line in body.splitlines():
        s = line.strip()
        if s.startswith('|') and s.count('|') >= 3 and not TABLE_SEP_RE.match(s):
            cells = [c.strip() for c in s.strip('|').split('|')]
            if cells and cells[0]:
                out.append(cells[0])
    return out


def bullet_lines(body):
    out = []
    for line in body.splitlines():
        s = line.strip()
        if len(s) >= 15 and not s.startswith(('|', '#', '!', '<')):
            out.append(s)
    return out


def headings(body):
    return [(len(m.group(1)), m.group(2).strip()) for m in HEADING_RE.finditer(body)]


def mark_counts(body):
    c = collections.Counter(MARK_RE.findall(body))
    return {m: c.get(m, 0) for m in MARKS}


def section_entries(detail, ref):
    """某一節（例如 §5、§6）嘅項目：bullet／編號列點，或者表格列——兩種格式都計。

    §5 來源清單成日用表格（| # | 來源 | URL |），§6 存疑／未驗證通常用 bullet，
    兩種都要計到，唔可以淨係認一種格式。
    """
    sec = cardfmt.section_text(detail, ref)
    items = [l.strip() for l in sec.splitlines() if LIST_ITEM_RE.match(l)]
    items += table_rows(sec)
    return items


def backrefs(body):
    return sorted({m.group(1) for m in BACKREF_RE.finditer(body) if m.group(1)})


SIMILAR_ENOUGH = 0.75


def lost_lines(old_lines, new_lines):
    """分開「真係冇咗」同「改過但仲喺度」。

    去重成日會喺原本嗰行後面加一句指回（「…（圖表見 1.4）」），
    如果逐字比，呢種加字會被當做「成行消失」，同表格列嗰個問題一樣。
    所以搵唔到一模一樣嘅時候，再搵下新版有冇一行同佢好似（≥85%）：
    有就當「改過」（軟提示，要人睇下改成點），冇先當「真係冇咗」（紅色）。

    回傳 (真係冇咗, [(舊行, 最相似嘅新行, 相似度)…])。
    """
    new_set = set(new_lines)
    lost, edited = [], []
    for line in set(old_lines) - new_set:
        best, ratio = None, 0.0
        for cand in new_lines:
            r = difflib.SequenceMatcher(None, line, cand).ratio()
            if r > ratio:
                best, ratio = cand, r
        if ratio >= SIMILAR_ENOUGH:
            edited.append((line, best, ratio))
        else:
            lost.append(line)
    return lost, edited


def compare_one(ch, old_raw, new_raw):
    """回傳 (has_hard_issue: bool, report_lines: list[str])。"""
    lines = []
    hard = False

    old_body, new_body = strip_fm(old_raw), strip_fm(new_raw)
    _, _, old_detail = cardfmt.split_body(old_body)
    _, _, new_detail = cardfmt.split_body(new_body)
    old_detail = old_detail or old_body
    new_detail = new_detail or new_body

    lines.append('══ %s ══' % ch)

    # ── (a) 完全消失嘅單位 ──
    old_qs = cy.quotes(cy.segments(old_raw))
    new_qs = cy.quotes(cy.segments(new_raw))
    missing_qs = set(old_qs) - set(new_qs)

    old_tr, new_tr = table_row_keys(old_body), table_row_keys(new_body)
    missing_tr = set(old_tr) - set(new_tr)

    old_bl, new_bl = bullet_lines(old_body), bullet_lines(new_body)
    missing_bl, edited_bl = lost_lines(old_bl, new_bl)

    old_h, new_h = headings(old_body), headings(new_body)
    missing_h = [h for h in old_h if h not in new_h]

    old_mk, new_mk = mark_counts(old_raw), mark_counts(new_raw)
    dropped_mk = {m: (old_mk[m], new_mk[m]) for m in MARKS if new_mk[m] < old_mk[m]}

    # 圖片用「唯一圖檔」比，唔用總數：去重有時係將重覆咗嘅同一張圖表
    # 由兩個章節減到一個，嗰張圖仍然喺卡入面——咁樣唔算少咗資料。
    # 真正要捉嘅係「有張圖成張唔見咗」。
    old_img_set = set(IMAGE_RE.findall(old_body))
    new_img_set = set(IMAGE_RE.findall(new_body))
    missing_img = old_img_set - new_img_set
    old_img, new_img = len(old_img_set), len(new_img_set)

    old_s5, new_s5 = section_entries(old_detail, '5'), section_entries(new_detail, '5')
    missing_s5 = [x for x in old_s5 if x not in new_s5]
    old_s6, new_s6 = section_entries(old_detail, '6'), section_entries(new_detail, '6')
    missing_s6 = [x for x in old_s6 if x not in new_s6]

    if missing_qs:
        hard = True
        lines.append('  ✗ (a) 有 %d 條【原文】引文喺新版一次都搵唔返：' % len(missing_qs))
        for q in sorted(missing_qs):
            lines.append('       － 「%s」' % q[:100])
    if missing_tr:
        hard = True
        lines.append('  ✗ (a) 有 %d 條表格記錄（第一格識別碼）喺新版完全消失：' % len(missing_tr))
        for r in sorted(missing_tr):
            lines.append('       － %s' % r[:80])
    if missing_bl:
        hard = True
        lines.append('  ✗ (a) 有 %d 行要點／段落（≥15 字）喺新版完全消失：' % len(missing_bl))
        for b in sorted(missing_bl):
            lines.append('       － %s' % b[:100])
    if missing_h:
        hard = True
        lines.append('  ✗ (a) 有 %d 個標題喺新版消失（去重唔應該改標題／章節）：' % len(missing_h))
        for lvl, txt in missing_h:
            lines.append('       － %s %s' % ('#' * lvl, txt))
    if dropped_mk:
        hard = True
        lines.append('  ✗ (a) 四個標記嘅出現次數減少咗（去重應該淨係減引文重複，唔應該減標記）：')
        for m, (o, n) in dropped_mk.items():
            lines.append('       － 【%s】：%d → %d' % (m, o, n))
    if missing_img:
        hard = True
        lines.append('  ✗ (a) 有 %d 張圖喺新版完全搵唔返：' % len(missing_img))
        for im in sorted(missing_img):
            lines.append('       － %s' % im[:100])
    if missing_s5:
        hard = True
        lines.append('  ✗ (a) §5 來源清單少咗 %d 項：' % len(missing_s5))
        for x in missing_s5:
            lines.append('       － %s' % x[:100])
    if missing_s6:
        hard = True
        lines.append('  ✗ (a) §6 存疑／未驗證少咗 %d 項：' % len(missing_s6))
        for x in missing_s6:
            lines.append('       － %s' % x[:100])
    if not (missing_qs or missing_tr or missing_bl or missing_h or dropped_mk
            or missing_img or missing_s5 or missing_s6):
        lines.append('  ✓ (a) 冇單位完全消失：引文 %d 條唯一、表列 %d 條唯一、'
                     '要點 %d 行唯一、標題 %d 個、唯一圖 %d 張、§5 %d 項、§6 %d 項，全部仲喺度'
                     % (len(set(new_qs)), len(set(new_tr)), len(set(new_bl)),
                        len(new_h), new_img, len(new_s5), len(new_s6)))

    if edited_bl:
        lines.append('  ！ (b) 有 %d 行改過（但仲喺度，≥%d%% 似）——R1 要睇下改成點：'
                     % (len(edited_bl), int(SIMILAR_ENOUGH * 100)))
        for old_l, new_l, r in edited_bl:
            lines.append('       舊 %s' % old_l[:90])
            lines.append('       新 %s   （%.0f%% 似）' % (new_l[:90], r * 100))

    # ── (b) 「見 §x.y」指返有冇嘢 —— 淺色警示，唔算 hard issue，R1 要人手覆核 ──
    refs = backrefs(new_body)
    if refs:
        lines.append('  ！ (b) 新版有 %d 個「（見 §x.y）」指回標記，人手／R1 要逐條核對' % len(refs))
        for ref in refs:
            sec = cardfmt.section_text(new_detail, ref)
            if not sec.strip():
                lines.append('       ✗ §%s：搵唔到呢一節（章節號可能打錯）' % ref)
            elif '【原文】' not in sec:
                lines.append('       ？ §%s：呢節冇【原文】標記——指返嗰個位置未必有原文可對'
                             % ref)
            else:
                lines.append('       ✓ §%s：呢節有【原文】，睇落合理（R1 仍要核對內容係咪啱條）'
                             % ref)

    # ── (c) 純資訊 ──
    old_tr_full, new_tr_full = table_rows(old_body), table_rows(new_body)
    lines.append('  ｜(c) 字數 %d → %d；行數 %d → %d；表格列（成行） %d → %d；'
                 '表格記錄（識別碼） %d → %d；【原文】次數 %d → %d'
                 % (len(old_raw), len(new_raw),
                    len(old_raw.splitlines()), len(new_raw.splitlines()),
                    len(old_tr_full), len(new_tr_full),
                    len(old_tr), len(new_tr), old_mk['原文'], new_mk['原文']))

    return hard, lines


def main():
    args = sys.argv[1:]
    base = 'HEAD'
    if '--base' in args:
        i = args.index('--base')
        base = args[i + 1]
        del args[i:i + 2]
    args = [a for a in args if not a.startswith('--')]
    if not args:
        sys.exit('用法：python3 review_dedupe.py [--base <ref>] <檔案.md>…')

    any_hard = False
    for path in args:
        ch = path[:-3] if path.endswith('.md') else path
        new_raw = open(ch + '.md', encoding='utf-8').read()
        old_raw = cy.git_show(base, ch + '.md')
        if old_raw is None:
            print('── %s：%s 度未有呢個檔，跳過（新卡）' % (ch, base))
            continue
        hard, lines = compare_one(ch, old_raw, new_raw)
        any_hard = any_hard or hard
        print('\n'.join(lines))
        print()

    print('（(a) 紅色一定要查；(b) 要人手／R1 逐條核對指回位置係咪真係啱；'
         '(c) 純資訊，唔代表有冇問題）')
    if any_hard:
        print('\n✗ 有卡出現 (a) 級問題——有內容完全消失，唔准直接 commit。')
        sys.exit(1)
    print('\n✓ 冇 (a) 級問題（(b) 仍然要人手／R1 覆核先可以 commit）。')


if __name__ == '__main__':
    main()
