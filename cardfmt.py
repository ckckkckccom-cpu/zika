#!/usr/bin/env python3
"""字卡格式 v3：YAML front matter 解析、正文分段、驗證。

一張 v3 字卡長成咁：

    ---
    format: 3
    char: 靜
    jyutping: [zing6]
    verdict: 一句總結
    nodes:
      - {id: qing, label: 青, layer: 部件, ref: "1.3"}
      ...
    edges:
      - {from: qing, to: jing, label: 聲符, evidence: 原文}
      ...
    ---
    # 靜
    ## 總覽
    ### 結構 / ### 意思 / ### 同音 / ### 交叉核對
    ## 詳細考證
    ## 0. 基本資料 …… ## 6. 存疑／未驗證

點解用 `---` 自己切而唔用 markdown-it 個 front_matter plugin：
check_glyphs.py、make_pdf_font.py、check_yuanwen.py 都要攞 YAML 同正文，
但佢哋唔 render markdown。呢度做一次，全部人用同一個結果。
"""
import os
import re

import yaml

LAYERS = ('部件', '字', '意思', '同音', '結論')
EVIDENCE = ('原文', '觀察', '分歧', '引申')
# 由硬到軟。誠實檢查靠呢個次序。
EVIDENCE_RANK = {name: i for i, name in enumerate(EVIDENCE)}

MARKS = EVIDENCE            # 四個標記同證據級別同名，唔係巧合

H_OVERVIEW = '## 總覽'
H_DETAIL = '## 詳細考證'
# 總覽五格。次序有意思：先出結果（字典點講、部件點解、引申到咩、
# 同音字通到咩），最後「其他結果」放交叉核對同存疑。
# 基本資料同完整考據一律排喺後面，唔好喺最前面阻住。
OVERVIEW_BLOCKS = ('查字典的解釋', '不同部份結構解釋', '同族字', '做部件時',
                   '引申義', '同音字引申', '其他結果')

# front matter 一定要喺檔案最頂。卡入面有好多 `---` 做分隔線，
# 所以一定要用 \A 錨死開頭，唔可以任意搵。
_FM = re.compile(r'\A---\r?\n(.*?)\r?\n---\r?\n', re.S)


class Card:
    """一張字卡。meta 係 None 就代表舊格式（v1／v2），冇 front matter。"""

    def __init__(self, ch, meta, body, raw, path):
        self.ch = ch
        self.meta = meta
        self.body = body
        self.raw = raw
        self.path = path

    @property
    def is_v3(self):
        return bool(self.meta)

    @property
    def format_version(self):
        """呢張卡係邊個格式版本。

        v3 喺 front matter 寫明。舊卡冇 front matter，靠有冇同音層／
        交叉核對去判斷：有＝v2，冇＝v1。
        版本封存（archive/<字>_v<N>.pdf）就係按呢個號碼。
        """
        if self.meta and self.meta.get('format'):
            try:
                return int(self.meta['format'])
            except (TypeError, ValueError):
                pass
        _, _, detail = split_body(self.body)
        body = detail or self.body
        return 2 if (section_text(body, '3.1') or section_text(body, '4.4')) else 1

    @property
    def jyutping(self):
        """回傳讀音 list。舊卡由 0 節個表撈返出嚟。"""
        if self.meta and self.meta.get('jyutping'):
            j = self.meta['jyutping']
            return [j] if isinstance(j, str) else list(j)
        return _sniff_jyutping(self.body)

    @property
    def verdict(self):
        """一句總結。舊卡撈 4.4 節第一句，撈唔到就回空。"""
        if self.meta and self.meta.get('verdict'):
            return str(self.meta['verdict']).strip()
        return _sniff_verdict(self.body)

    @property
    def nodes(self):
        return list(self.meta.get('nodes') or []) if self.meta else []

    @property
    def edges(self):
        return list(self.meta.get('edges') or []) if self.meta else []


def parse_card(path):
    """讀一個 .md，切走 front matter。"""
    raw = open(path, encoding='utf-8').read()
    ch = os.path.basename(path)[:-3]
    m = _FM.match(raw)
    if not m:
        return Card(ch, None, raw, raw, path)
    meta = yaml.safe_load(m.group(1)) or {}
    if not isinstance(meta, dict):
        raise ValueError('%s：front matter 要係一個 mapping，而家係 %s'
                         % (os.path.basename(path), type(meta).__name__))
    return Card(ch, meta, raw[m.end():], raw, path)


def split_body(body):
    """切成三段：(開頭, 總覽, 詳細考證)。

    冇 `## 詳細考證` 標題（舊卡）就全部當詳細考證，總覽留空。
    """
    i_ov = _find_heading(body, H_OVERVIEW)
    i_dt = _find_heading(body, H_DETAIL)

    if i_dt is None:
        return body, '', body if i_ov is None else body[:i_ov] + body[i_ov:]
    head = body[:i_ov if i_ov is not None else i_dt]
    overview = body[i_ov:i_dt] if i_ov is not None else ''
    detail = body[i_dt:]
    return head, overview, detail


def _find_heading(text, heading):
    """搵一個獨佔一行嘅標題，回傳 index。"""
    for m in re.finditer(r'^%s\s*$' % re.escape(heading), text, re.M):
        return m.start()
    return None


def section_text(detail_md, ref):
    """攞出某一節嘅正文，例如 ref="1.3" → `### 1.3 …` 到下一個同級／上級標題為止。

    俾誠實檢查用：睇下嗰節到底用咗邊啲標記。
    """
    ref = str(ref).strip()
    # `## 0. 基本資料` / `### 1.3 部件分解` / `### 4.4 一句總結`
    pat = re.compile(r'^(#{2,4})\s*%s[.、．]?\s' % re.escape(ref), re.M)
    m = pat.search(detail_md)
    if not m:
        return ''
    level = len(m.group(1))
    # 一定要行到標題嗰行完 —— 唔係嘅話標題自己啲字（「一句總結」）
    # 會變咗係嗰節嘅第一句，喺首頁字磚度顯示出嚟。
    nl = detail_md.find('\n', m.end())
    rest = detail_md[nl + 1:] if nl != -1 else ''
    nxt = re.search(r'^#{2,%d}\s' % level, rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def basic_rows(card):
    """由第 0 節嗰個表撈出基本資料，回傳 [(項目, 內容 markdown)]。

    俾網頁頂部嗰條密集資料格用（仿漢典嘅做法）。
    有圖嘅行（楷書）唔要 —— 大字本身已經喺上面。
    來源一欄都唔要 —— 頂部係速查，來源留喺詳細考證嗰個完整表。
    """
    _, _, detail = split_body(card.body)
    sec = section_text(detail, '0') or section_text(card.body, '0')
    rows, seen = [], set()
    for line in sec.splitlines():
        line = line.strip()
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) < 2:
            continue
        label = re.sub(r'[*`]', '', cells[0]).strip()
        val = cells[1].strip()
        if not label or not val or label == '項目':
            continue
        if set(label) <= set('-: '):          # 表格分隔行
            continue
        if '![' in val or '<img' in val:      # 字形圖
            continue
        if label in seen:
            continue
        seen.add(label)
        rows.append((label, val))
    return rows


def marks_in(text):
    """嗰段文字用咗邊幾個標記。"""
    return {m for m in MARKS if '【%s】' % m in text}


def validate(card):
    """回傳 (錯誤 list, 警告 list)，全部中文，方便用戶自己睇得明。"""
    errs, warns = [], []
    ch = card.ch
    if not card.meta:
        return errs, warns                       # 舊卡唔驗，照砌

    meta = card.meta
    if meta.get('char') and meta['char'] != ch:
        errs.append('%s.md：front matter 寫住 char: %s，同檔名對唔上' % (ch, meta['char']))
    if not str(meta.get('verdict', '')).strip():
        errs.append('%s.md：front matter 缺少 verdict（一句總結）' % ch)
    if not meta.get('jyutping'):
        errs.append('%s.md：front matter 缺少 jyutping（粵音）' % ch)

    nodes = card.nodes
    edges = card.edges
    if not nodes:
        errs.append('%s.md：front matter 冇 nodes，畫唔到推理網絡圖' % ch)
        return errs, warns

    ids = []
    for i, n in enumerate(nodes, 1):
        if not isinstance(n, dict):
            errs.append('%s.md：第 %d 個節點唔係 mapping' % (ch, i))
            continue
        nid = n.get('id')
        if not nid:
            errs.append('%s.md：第 %d 個節點冇 id' % (ch, i))
        elif nid in ids:
            errs.append('%s.md：節點 id 重複 —— %s' % (ch, nid))
        else:
            ids.append(nid)
        if not str(n.get('label', '')).strip():
            errs.append('%s.md：節點 %s 冇 label' % (ch, nid))
        if n.get('layer') not in LAYERS:
            errs.append('%s.md：節點 %s 嘅 layer 係「%s」，只可以係 %s'
                        % (ch, nid, n.get('layer'), '／'.join(LAYERS)))

    if not any(n.get('layer') == '結論' for n in nodes if isinstance(n, dict)):
        errs.append('%s.md：最少要有一個 layer: 結論 嘅節點' % ch)

    idset = set(ids)
    for i, e in enumerate(edges, 1):
        if not isinstance(e, dict):
            errs.append('%s.md：第 %d 條邊唔係 mapping' % (ch, i))
            continue
        for side in ('from', 'to'):
            if e.get(side) not in idset:
                errs.append('%s.md：第 %d 條邊嘅 %s: %s 搵唔到對應節點'
                            % (ch, i, side, e.get(side)))
        if e.get('evidence') not in EVIDENCE:
            errs.append('%s.md：第 %d 條邊嘅 evidence 係「%s」，只可以係 %s'
                        % (ch, i, e.get('evidence'), '／'.join(EVIDENCE)))

    # 節點太多會變一團漿糊，長者睇唔到
    if len(nodes) > 12:
        warns.append('%s.md：推理網絡有 %d 個節點，多過 12 個好難睇，建議精簡'
                     % (ch, len(nodes)))
    for layer in LAYERS:
        cnt = sum(1 for n in nodes if isinstance(n, dict) and n.get('layer') == layer)
        if cnt > 4:
            warns.append('%s.md：「%s」層有 %d 個節點，一行排得落 3 個，會摺行'
                         % (ch, layer, cnt))

    warns += _honesty_check(card)
    warns += _overview_check(card)
    warns += _combo_check(card)
    return errs, warns


def _combo_check(card):
    """組合字一定要有 combo 資料（組合圖同 1.7 專章靠佢）。

    獨體字冇得組合，寫 combo: {layout: 獨體} 就當交代咗。
    """
    out = []
    cb = (card.meta or {}).get('combo')
    if cb is None:
        out.append('%s.md：front matter 冇 combo —— 組合字一定要有，'
                   '獨體字就寫 combo: {layout: 獨體}' % card.ch)
        return out
    if not isinstance(cb, dict):
        out.append('%s.md：combo 要係一個 mapping' % card.ch)
        return out
    if cb.get('layout') == '獨體':
        return out
    for k in ('layout', 'form', 'sound'):
        if not cb.get(k):
            out.append('%s.md：combo 缺少 %s' % (card.ch, k))
    for axis, name in (('same_form', '同形符'), ('same_sound', '同聲符')):
        rows = cb.get(axis) or []
        if not rows:
            out.append('%s.md：combo 嘅 %s（%s）一個字都冇 —— '
                       '真係一個都搵唔到嘅話，喺 note 講明' % (card.ch, axis, name))
            continue
        for i, r in enumerate(rows, 1):
            if not isinstance(r, dict) or not r.get('char') or not r.get('with'):
                out.append('%s.md：combo %s 第 %d 項要有 char 同 with'
                           % (card.ch, axis, i))
    _, _, detail = split_body(card.body)
    if not section_text(detail, '1.7'):
        out.append('%s.md：冇「### 1.7 字族定位」—— 組合字要有呢個專章' % card.ch)
    if not section_text(detail, '1.8'):
        out.append('%s.md：冇「### 1.8 這個字做部件時」—— 每張卡都要有' % card.ch)
    labels = {k for k, _ in basic_rows(card)}
    if '部件組合' not in labels:
        out.append('%s.md：第 0 節冇「部件組合」一行（IDS 分解式，例如 ⿰貝才）' % card.ch)
    sec13 = section_text(detail, '1.3')
    if sec13 and '字樣說明' not in sec13:
        out.append('%s.md：1.3 冇引教育部「字樣說明」—— 拆法對照係重中之重' % card.ch)
    if not cb.get('downstream'):
        out.append('%s.md：combo 冇 downstream —— 呢隻字做部件時去咗邊，'
                   '一個都冇都要寫明 count: 0' % card.ch)
    return out


def _honesty_check(card):
    """誠實檢查 —— 呢個係整個 project 嘅命脈落到圖上面嘅版本。

    一條邊如果標住【原文】，佢兩頭指住嘅章節就一定要真係有【原文】撐。
    唔係嘅話，一幅圖就會將引申偷偷升格做考據，
    而圖正正係最多人只睇嗰一眼嘅嘢。

    兩頭都睇（唔淨係睇 to），因為總結一類章節（4.4）本身唔會再標記，
    佢嘅根據喺上游嗰節。
    """
    out = []
    _, _, detail = split_body(card.body)
    by_id = {n['id']: n for n in card.nodes if isinstance(n, dict) and n.get('id')}
    for i, e in enumerate(card.edges, 1):
        if not isinstance(e, dict):
            continue
        ev = e.get('evidence')
        if ev not in EVIDENCE_RANK:
            continue
        marks, missing = set(), []
        for side in ('to', 'from'):
            ref = (by_id.get(e.get(side)) or {}).get('ref')
            if not ref:
                continue
            sec = section_text(detail, ref)
            if not sec:
                missing.append(str(ref))
            else:
                marks |= marks_in(sec)
        for ref in missing:
            out.append('%s.md：第 %d 條邊連住第 %s 節，但正文搵唔到呢一節'
                       % (card.ch, i, ref))
        if missing or not marks:
            if not missing and EVIDENCE_RANK[ev] <= EVIDENCE_RANK['觀察']:
                out.append('%s.md：第 %d 條邊標住【%s】，但佢連住嘅章節一個標記都冇'
                           % (card.ch, i, ev))
            continue
        best = min(EVIDENCE_RANK[m] for m in marks)
        if best > EVIDENCE_RANK[ev]:
            out.append('%s.md：第 %d 條邊標住【%s】，但佢連住嘅章節最硬只有【%s】'
                       '—— 圖唔可以講到硬過正文'
                       % (card.ch, i, ev, EVIDENCE[best]))
    return out


def _overview_check(card):
    """總覽四格齊唔齊、每格點數夠唔夠。"""
    out = []
    _, ov, _ = split_body(card.body)
    if not ov.strip():
        out.append('%s.md：冇「## 總覽」一節' % card.ch)
        return out
    for name in OVERVIEW_BLOCKS:
        if not re.search(r'^###\s*%s\s*$' % re.escape(name), ov, re.M):
            out.append('%s.md：總覽缺少「### %s」一格' % (card.ch, name))
    for m in re.finditer(r'^###\s*(\S+)\s*$(.*?)(?=^###\s|\Z)', ov, re.M | re.S):
        name, block = m.group(1), m.group(2)
        pts = len(re.findall(r'^\s*[-*]\s+\S', block, re.M))
        if pts < 2:
            out.append('%s.md：總覽「%s」只有 %d 點，建議 2 至 6 點'
                       % (card.ch, name, pts))
        elif pts > 6:
            out.append('%s.md：總覽「%s」有 %d 點，多過 6 點就唔算摘要'
                       % (card.ch, name, pts))
    return out


def _sniff_jyutping(body):
    """舊卡：由 0 節「粵音」一行撈。"""
    m = re.search(r'^\|\s*\*{0,2}粵音\*{0,2}\s*\|\s*(.+?)\s*\|', body, re.M)
    if not m:
        return []
    cell = m.group(1)
    return re.findall(r'[a-z]{1,6}[1-6]', cell) or []


def _sniff_verdict(body):
    """舊卡：撈 4.4 一句總結嘅第一段，剝走 markdown 記號。

    只係過渡用 —— 升到 v3 之後應該喺 front matter 寫返句像樣嘅 verdict。
    """
    sec = section_text(body, '4.4')
    for line in sec.splitlines():
        line = line.strip()
        if not line or line.startswith(('#', '>', '|', '-')):
            continue
        line = re.sub(r'\*{1,2}|【|】|`|\\', '', line).strip()
        # 「X 最硬嘅證據鏈：」一類引子唔使入字磚
        head, sep, rest = line.partition('：')
        if sep and len(head) <= 14 and rest.strip():
            line = rest.strip()
        cut = line.find('。')
        if 0 < cut < 72:
            return line[:cut + 1]
        if len(line) > 72:
            # 切喺標點度，唔好斬到一半個詞
            edge = max(line.rfind(c, 0, 72) for c in '，；、）」→')
            line = line[:edge + 1 if edge > 30 else 72].rstrip('，、；→') + '⋯'
        return line
    return ''


def cards_in(root):
    """所有字卡（一隻字一張）。同 fontkit.card_files 一致。"""
    import fontkit
    return [parse_card(os.path.join(root, ch + '.md'))
            for ch in fontkit.card_files(root)]


if __name__ == '__main__':
    import sys
    root = os.path.dirname(os.path.abspath(__file__))
    names = sys.argv[1:] or None
    bad = 0
    for card in cards_in(root):
        if names and card.ch not in names:
            continue
        errs, warns = validate(card)
        tag = 'v3' if card.is_v3 else '舊格式'
        print('── %s（%s）' % (card.ch, tag))
        for e in errs:
            print('   ✗ %s' % e)
            bad += 1
        for w in warns:
            print('   ! %s' % w)
        if not errs and not warns:
            print('   ✓ 冇問題')
    sys.exit(1 if bad else 0)
