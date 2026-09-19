#!/usr/bin/env python3
"""字庫名單 —— 由「名」榜（xlsx）同「姓氏」榜（tsv）合埋一份可查嘅字庫。

點解要有呢個：28 隻目標字舊時淨係寫死喺 CLAUDE.md，做咗邊隻、
未做邊隻要人手記。而家用戶想連台灣、香港嘅名，同姓氏都計埋，
清單會脹到成百幾字，一定要有機讀嘅單一來源。

資料嚟源：
  三地中文名字排行統計.xlsx   三地「名」榜（B1 全名、B2 名、A 速查三個表）
  姓氏榜.tsv                  「姓氏」榜（人手整理，內地／台灣官方 + 標明嘅二手）

呢個 script 淨係讀資料、拆字、計優先分、對埋現有字卡嘅完成狀態，
唔會判斷邊隻字「應該」做 —— 呢個係用戶嘅事，佢淨係出個排咗序嘅清單
俾用戶揀。

用法：
  python3 charlist.py            # 出 字庫.tsv，並喺 terminal 印未做嘅頭 20 個
  python3 charlist.py --todo 10  # 印未做嘅頭 10 個（唔改 --todo 就預設 20）
"""
import os
import re
import sys
import zipfile
import html as htmllib
from collections import defaultdict

import cardfmt
import fontkit

ROOT = fontkit.ROOT
XLSX = os.path.join(ROOT, '三地中文名字排行統計.xlsx')
SURNAME_TSV = os.path.join(ROOT, '姓氏榜.tsv')
OUT = os.path.join(ROOT, '字庫.tsv')

# 分層次序：內地名（現有 28 隻嘅出處）排最前，跟住台灣名、姓氏、香港非官方
TIER_ORDER = ['一 內地名', '二 台灣名', '三 姓氏', '四 香港名（非官方）']

# 榜權重：官方人口統計 > 官方但唔係人口統計 / 姓氏 > 非官方流量榜
WEIGHT = {
    '內地全名': 3, '內地雙字名': 3, '內地單字名': 3,
    '台灣全名': 3, '台灣名(合併)': 3, '台灣名(男)': 3,
    '內地姓氏': 2, '台灣姓氏': 2,
    '香港名(男,非官方)': 1, '香港名(女,非官方)': 1,
}


# ──────────────────────────────────────────────────────────
# 讀 xlsx（純標準庫：zipfile + regex 抽 inline string，repo 冇裝 openpyxl）
# ──────────────────────────────────────────────────────────

_ROW = re.compile(r'<row[^>]*>(.*?)</row>', re.S)
_CELL = re.compile(r'<c r="([A-Z]+)\d+"[^>]*>(.*?)</c>', re.S)
_T = re.compile(r'<t[^>]*>(.*?)</t>', re.S)
_V = re.compile(r'<v>(.*?)</v>')


def _cell_text(cell_xml):
    t = _T.findall(cell_xml)
    if t:
        return htmllib.unescape(''.join(t))
    v = _V.findall(cell_xml)
    return htmllib.unescape(v[0]) if v else ''


def read_sheet(z, n):
    """讀 xl/worksheets/sheet<n>.xml，回傳 list of dict（用第一行做欄名）。"""
    xml = z.read('xl/worksheets/sheet%d.xml' % n).decode('utf-8')
    rows = []
    for row_xml in _ROW.findall(xml):
        cells = {}
        for col, cell_xml in _CELL.findall(row_xml):
            cells[col] = _cell_text(cell_xml)
        if cells:
            rows.append(cells)
    if not rows:
        return []
    # 揾表頭：第一行有 >=3 個非空格仔嘅就當表頭（前面可能有標題／注釋行）
    header_i = 0
    for i, r in enumerate(rows):
        if sum(1 for v in r.values() if v.strip()) >= 3:
            header_i = i
            break
    header = rows[header_i]
    out = []
    for r in rows[header_i + 1:]:
        rec = {header[col]: r.get(col, '') for col in header}
        if any(v.strip() for v in rec.values()):
            out.append(rec)
    return out


# ──────────────────────────────────────────────────────────
# 拆字
# ──────────────────────────────────────────────────────────

def split_chars(name):
    """一個名／全名拆做單字，去重（同一個名入面重複字淨計一次）。"""
    seen = []
    for c in name:
        if '一' <= c <= '鿿' and c not in seen:
            seen.append(c)
    return seen


class Hit:
    __slots__ = ('src', 'rank', 'name')

    def __init__(self, src, rank, name):
        self.src = src
        self.rank = rank
        self.name = name


def add_hits(hits, src, rank, name):
    for ch in split_chars(name):
        hits[ch].append(Hit(src, rank, name))


# ──────────────────────────────────────────────────────────
# 三個工作表 → 逐字命中記錄
# ──────────────────────────────────────────────────────────

def collect_from_xlsx():
    hits = defaultdict(list)
    if not os.path.exists(XLSX):
        print('！搵唔到 %s，跳過名榜' % os.path.basename(XLSX), file=sys.stderr)
        return hits
    z = zipfile.ZipFile(XLSX)

    # sheet1＝B1 全名：地區｜排名｜姓名｜…
    for r in read_sheet(z, 1):
        region, rank, name = r.get('地區', ''), r.get('排名', ''), r.get('姓名', '')
        if not name or not rank.strip().isdigit():
            continue
        if region == '中國':
            add_hits(hits, '內地全名', int(rank), name)
        elif region == '台灣':
            add_hits(hits, '台灣全名', int(rank), name)
        # 香港「無數據」，冇 rank，自然跳過

    # sheet2＝B2 名：地區｜榜別｜排名｜名字｜…
    for r in read_sheet(z, 2):
        region, category, rank, name = (r.get('地區', ''), r.get('榜別', ''),
                                        r.get('排名', ''), r.get('名字', ''))
        if not name or not rank.strip().isdigit():
            continue
        rank = int(rank)
        if region == '中國' and category == '雙字名':
            add_hits(hits, '內地雙字名', rank, name)
        elif region == '中國' and category == '單字名':
            add_hits(hits, '內地單字名', rank, name)
        elif region == '香港' and '男' in category:
            add_hits(hits, '香港名(男,非官方)', rank, name)
        elif region == '香港' and '女' in category:
            add_hits(hits, '香港名(女,非官方)', rank, name)

    # sheet3＝A 速查：A2 表有「台灣 男女合併」「台灣 男」兩欄，
    # 呢兩欄冇喺 sheet1/2 出現過（sheet1 淨係台灣「全名」，sheet2 冇台灣）。
    # A 速查係「排名」做第一欄、跟住幾條唔同地區/榜別欄，逐格自己係一個名。
    for r in read_sheet(z, 3):
        rank = r.get('排名', '')
        if not rank.strip().isdigit():
            continue
        rank = int(rank)
        for col, name in r.items():
            if col == '排名' or not name.strip():
                continue
            if '台灣' in col and '男女' in col:
                add_hits(hits, '台灣名(合併)', rank, name)
            elif '台灣' in col and col.strip().endswith('男'):
                add_hits(hits, '台灣名(男)', rank, name)
            # 中國／香港欄喺呢個表淨係複述 sheet1/2 已經有嘅嘢，唔重複計
    return hits


def collect_from_surnames():
    hits = defaultdict(list)
    if not os.path.exists(SURNAME_TSV):
        print('！搵唔到 %s，跳過姓氏榜' % os.path.basename(SURNAME_TSV), file=sys.stderr)
        return hits
    lines = [l for l in open(SURNAME_TSV, encoding='utf-8').read().splitlines()
             if l and not l.startswith('#')]
    if not lines:
        return hits
    header = lines[0].split('\t')
    for line in lines[1:]:
        cells = line.split('\t')
        rec = dict(zip(header, cells))
        region, rank, surname = rec.get('地區', ''), rec.get('排名', ''), rec.get('姓', '')
        if not surname or not rank.strip().isdigit():
            continue
        src = '內地姓氏' if region == '內地' else '台灣姓氏' if region == '台灣' else None
        if src:
            add_hits(hits, src, int(rank), surname)
    return hits


# ──────────────────────────────────────────────────────────
# 分層、優先分、狀態
# ──────────────────────────────────────────────────────────

_28 = set('張偉王李娜芳靜敏劉秀英桂蘭玉婷建華梅珍海燕杰麗勇濤艷軍強')


def tier_of(ch, srcs):
    if ch in _28:
        return '一 內地名'
    if any(s.startswith('台灣') and '姓氏' not in s for s in srcs):
        return '二 台灣名'
    if any('姓氏' in s for s in srcs):
        return '三 姓氏'
    if any('香港' in s for s in srcs):
        return '四 香港名（非官方）'
    return '二 台灣名'  # 保底：xlsx 入面唔喺 28 隻、又唔係姓氏／香港嘅名用字


def priority(hit_list):
    return round(sum(WEIGHT.get(h.src, 1) / h.rank for h in hit_list), 3)


def card_status():
    """讀現有 <字>.md，回傳 {字: (狀態文字, 版本)}。"""
    out = {}
    for ch in fontkit.card_files(ROOT):
        try:
            card = cardfmt.parse_card(os.path.join(ROOT, ch + '.md'))
            out[ch] = ('已做', card.format_version)
        except Exception as e:
            out[ch] = ('讀取失敗：%s' % e, 0)
    return out


def src_summary(hit_list):
    """人睇嘅出處摘要，例如「內地單字名:3、台灣姓氏:12」。"""
    by_src = defaultdict(list)
    for h in hit_list:
        by_src[h.src].append(h.rank)
    parts = []
    for src in sorted(by_src, key=lambda s: min(by_src[s])):
        ranks = sorted(set(by_src[src]))
        rs = ','.join(str(r) for r in ranks[:3]) + ('…' if len(ranks) > 3 else '')
        parts.append('%s:%s' % (src, rs))
    return '、'.join(parts)


def build():
    hits = collect_from_xlsx()
    for ch, lst in collect_from_surnames().items():
        hits[ch].extend(lst)

    status = card_status()

    rows = []
    for ch, lst in hits.items():
        tier = tier_of(ch, {h.src for h in lst})
        st, ver = status.get(ch, ('未做', 0))
        rows.append({
            'ch': ch, 'tier': tier, 'src': src_summary(lst),
            'priority': priority(lst), 'status': st, 'version': ver,
        })

    # 28 隻目標字如果因為冇對應 xlsx 榜（理論上唔會，但保險）漏咗，補返
    for ch in _28:
        if ch not in hits:
            st, ver = status.get(ch, ('未做', 0))
            rows.append({'ch': ch, 'tier': '一 內地名', 'src': '（28 隻清單）',
                        'priority': 0.0, 'status': st, 'version': ver})

    rows.sort(key=lambda r: (TIER_ORDER.index(r['tier']), -r['priority'], r['ch']))
    return rows


def write_tsv(rows):
    lines = ['# 字庫 —— 姓名字卡候選字清單。由 charlist.py 自動生成，唔好手改。',
            '# 重新產生：python3 charlist.py',
            '# 欄：字｜分層｜出現於（榜:排名,…）｜優先分｜狀態｜版本',
            '字\t分層\t出現於\t優先分\t狀態\t版本']
    for r in rows:
        lines.append('%s\t%s\t%s\t%s\t%s\t%s'
                     % (r['ch'], r['tier'], r['src'], r['priority'], r['status'], r['version']))
    open(OUT, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')


def main():
    args = sys.argv[1:]
    n_todo = 20
    if '--todo' in args:
        i = args.index('--todo')
        n_todo = int(args[i + 1])

    rows = build()
    write_tsv(rows)
    total = len(rows)
    done = sum(1 for r in rows if r['status'] == '已做')
    print('✓ 出咗 %s —— 共 %d 個字，已做 %d 個' % (os.path.relpath(OUT, ROOT), total, done))

    todo = [r for r in rows if r['status'] != '已做']
    print('\n未做，按優先分排（頭 %d 個）：' % n_todo)
    for r in todo[:n_todo]:
        print('  %s  %s  優先分 %.2f  （%s）' % (r['ch'], r['tier'], r['priority'], r['src']))


if __name__ == '__main__':
    main()
