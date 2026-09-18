#!/usr/bin/env python3
"""由字卡 front matter 畫推理網絡 SVG。

設計取向：呢幅圖係成頁最多人只望一眼嘅嘢，所以

  1. **字要夠大。** 唔用 viewBox 縮放去遷就手機 —— 咁做等於將 22px 嘅字
     縮到 10px，長者睇唔到。改為固定邏輯闊度，手機上放喺可橫捲嘅框入面，
     再加 lightbox 放大。字永遠係原大。
  2. **線嘅樣式＝證據強弱。** 實線粗＝原文，實線＝觀察，虛線＝分歧，
     點線灰＝引申。圖例畫喺 SVG 入面，所以印落紙都仲喺度。
  3. **顏色唔係唯一線索。** 每種線型都唔同，色盲或者黑白影印都分得出。

用法：python3 netgraph.py 靜 > /tmp/靜.svg
"""
import re
import sys
import unicodedata

import cardfmt

# ── 版面常數（SVG 邏輯單位，1 單位 ≈ 1px）──
# 呢啲數字係就住手機度身訂做嘅。
# 幅圖喺 CSS 度係 width:100% —— 手機上大約 320px 闊，即係縮到 0.67 倍。
# 所以邏輯字級要夠大（26），縮完之後喺手機上仲有 17px，長者先睇得到。
# 電腦上反過嚟放大到 560px，字變 30px，更加舒服。
W_MIN = 480            # 邏輯闊度：窄，先至唔使喺手機縮得咁犀利
PAD_X = 24
ROW_H = 150            # 一行節點佔幾高（要留夠位俾邊上面嘅字）
ROW_GAP = 104          # 兩行之間最少留幾多空位俾邊標籤
NODE_PAD_X = 16
NODE_PAD_Y = 12
LINE_H = 32
FS_NODE = 26           # 節點字級
FS_CHAR = 42           # 中央嗰隻字大啲
FS_EDGE = 20           # 邊上面嘅標籤
EDGE_LINE_H = 24
MAX_LINE_CHARS = 6.5   # 節點標籤一行最多幾多個全形字，超過就摺行
EDGE_LINE_CHARS = 8.5  # 邊標籤可以闊少少（佢哋短，而且擺喺空隙度）
MAX_PER_ROW = 2
GAP_X = 24

# 每層嘅色。淺底＋深框＋黑字，對比夠，列印都清楚。
LAYER_STYLE = {
    '部件': ('#eef2ff', '#4f46e5'),
    '字':   ('#ffffff', '#111827'),
    '意思': ('#ecfdf5', '#047857'),
    '同音': ('#fffbeb', '#b45309'),
    '結論': ('#faf5ff', '#7c3aed'),
}

# 證據級別 → (顏色, 線粗, dasharray, 線頭)
EDGE_STYLE = {
    '原文': ('#1d4ed8', 4.0, '', 'butt'),
    '觀察': ('#047857', 3.0, '', 'butt'),
    '分歧': ('#b45309', 3.0, '10 7', 'butt'),
    '引申': ('#6b7280', 2.6, '1 8', 'round'),
}


def _cw(c):
    """一個字元佔幾多 em。全形當 1，其餘當 0.56。"""
    if unicodedata.combining(c):
        return 0.0
    return 1.0 if unicodedata.east_asian_width(c) in ('W', 'F') else 0.56


def _width(s):
    return sum(_cw(c) for c in s)


def wrap(label, limit=MAX_LINE_CHARS):
    """摺行。先跟人手寫嘅 \n，再按闊度摺。中文可以任意位摺。"""
    out = []
    for part in str(label).split('\n'):
        line, w = '', 0.0
        for c in part:
            cw = _cw(c)
            # 標點唔好留喺行頭
            if w + cw > limit and line and c not in '，。、）」』？！':
                out.append(line)
                line, w = c, cw
            else:
                line += c
                w += cw
        if line:
            out.append(line)
    return out or ['']


class Node:
    def __init__(self, spec):
        self.id = spec.get('id')
        self.label = str(spec.get('label', ''))
        self.layer = spec.get('layer')
        self.ref = spec.get('ref')
        self.note = spec.get('note')
        self.lines = wrap(self.label)
        self.is_char = (self.layer == '字')
        fs = FS_CHAR if self.is_char else FS_NODE
        self.fs = fs
        self.w = round(max(_width(l) for l in self.lines) * fs) + NODE_PAD_X * 2
        self.h = LINE_H * len(self.lines) + NODE_PAD_Y * 2
        if self.is_char:
            self.h += 8
        self.x = self.y = 0        # 左上角，layout 之後先有

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def top(self):
        return self.y

    @property
    def bottom(self):
        return self.y + self.h


def layout(nodes):
    """分層由上而下排。同一層排唔落就摺去下一行。回傳 (rows, W, H)。"""
    rows = []
    for layer in cardfmt.LAYERS:
        group = [n for n in nodes if n.layer == layer]
        row = []
        for n in group:
            fits = (len(row) < MAX_PER_ROW and
                    sum(x.w for x in row) + n.w + GAP_X * len(row) <= W_MIN - PAD_X * 2)
            if row and not fits:
                rows.append(row)
                row = []
            row.append(n)
        if row:
            rows.append(row)

    width = W_MIN
    for row in rows:
        need = sum(n.w for n in row) + GAP_X * (len(row) - 1) + PAD_X * 2
        width = max(width, need)

    y = 16
    for row in rows:
        rw = sum(n.w for n in row) + GAP_X * (len(row) - 1)
        x = (width - rw) / 2
        rh = max(n.h for n in row)
        for n in row:
            n.x = x
            n.y = y + (rh - n.h) / 2
            x += n.w + GAP_X
        y += max(ROW_H, rh + ROW_GAP)
    return rows, width, y


def _bezier(a, b):
    """兩個節點之間嘅曲線。回傳 (path d, 中點 x, 中點 y)。"""
    if abs(a.y - b.y) < 1:                       # 同一行：由下面兜個彎
        x1, y1 = a.cx, a.bottom
        x2, y2 = b.cx, b.bottom
        dip = 54
        c1 = (x1, y1 + dip)
        c2 = (x2, y2 + dip)
    else:
        going_down = b.top > a.top
        x1, y1 = a.cx, (a.bottom if going_down else a.top)
        x2, y2 = b.cx, (b.top if going_down else b.bottom)
        dy = (y2 - y1) * 0.45
        c1 = (x1, y1 + dy)
        c2 = (x2, y2 - dy)
    d = 'M%.1f %.1f C%.1f %.1f %.1f %.1f %.1f %.1f' % (
        x1, y1, c1[0], c1[1], c2[0], c2[1], x2, y2)
    mx = (x1 + 3 * c1[0] + 3 * c2[0] + x2) / 8
    my = (y1 + 3 * c1[1] + 3 * c2[1] + y2) / 8
    return d, mx, my, ((x1, y1), c1, c2, (x2, y2))


def _point_at_y(d_pts, ty):
    """喺一條三次貝茲曲線上，搵返高度 ty 嗰點嘅 x。二分法就夠。"""
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = d_pts

    def at(t):
        u = 1 - t
        bx = u*u*u*x0 + 3*u*u*t*x1 + 3*u*t*t*x2 + t*t*t*x3
        by = u*u*u*y0 + 3*u*u*t*y1 + 3*u*t*t*y2 + t*t*t*y3
        return bx, by

    lo, hi = 0.0, 1.0
    if y3 < y0:
        lo, hi = hi, lo
    for _ in range(24):
        mid = (lo + hi) / 2
        if at(mid)[1] < ty:
            lo = mid
        else:
            hi = mid
    return at((lo + hi) / 2)[0]


def _free_spot(x, y, w, h, taken):
    """搵一個唔會壓住節點、又唔會壓住其他標籤嘅位。

    邊嘅標籤如果直接放喺曲線中點，跨層嘅邊會啱啱好將字疊喺中間嗰排節點上面，
    睇落好似亂碼。呢度逐個候選位試，揀第一個唔撞嘅。
    """
    def hit(bx, by):
        for (ax0, ay0, ax1, ay1) in taken:
            if bx - w / 2 < ax1 and bx + w / 2 > ax0 and \
               by - h / 2 < ay1 and by + h / 2 > ay0:
                return True
        return False

    step = h + 8
    for dy in (0, -step, step, -step * 2, step * 2):
        for dx in (0, -w * 0.58, w * 0.58, -w * 1.1, w * 1.1):
            if not hit(x + dx, y + dy):
                return x + dx, y + dy
    return None


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def _legend(width, y):
    """圖例。畫喺 SVG 入面，所以印落紙一樣有。"""
    out = ['<g class="lg">',
           '<line x1="%d" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#d4d4d8" '
           'stroke-width="1.5"/>' % (PAD_X, y, width - PAD_X, y)]
    out.append('<text x="%d" y="%.1f" font-size="20" fill="#52525b">%s</text>'
               % (PAD_X, y + 30, esc('線的樣式 ＝ 證據有多硬')))
    col_w = (width - PAD_X * 2) / 2
    for i, name in enumerate(cardfmt.EVIDENCE):
        color, sw, dash, cap = EDGE_STYLE[name]
        cx = PAD_X + (i % 2) * col_w
        cy = y + 66 + (i // 2) * 38
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
                   'stroke-width="%.1f" stroke-dasharray="%s" stroke-linecap="%s"/>'
                   % (cx, cy, cx + 62, cy, color, sw, dash, cap))
        out.append('<text x="%.1f" y="%.1f" font-size="20" fill="#27272a">%s</text>'
                   % (cx + 76, cy + 7, esc('【%s】' % name)))
    out.append('</g>')
    return '\n'.join(out), y + 66 + 38 + 20


def render_svg(card, anchor_prefix=None):
    """一張卡 → SVG 字串。冇 front matter 就回 None。"""
    if not card.is_v3 or not card.nodes:
        return None
    prefix = anchor_prefix if anchor_prefix is not None else card.ch
    nodes = [Node(s) for s in card.nodes if isinstance(s, dict)]
    by_id = {n.id: n for n in nodes}
    rows, width, y_end = layout(nodes)

    parts = []

    # 箭嘴：每種證據一個，因為 context-stroke 太新，唔可以靠
    defs = ['<defs>']
    for name, (color, sw, dash, cap) in EDGE_STYLE.items():
        defs.append('<marker id="%s-ar-%s" viewBox="0 0 10 10" refX="9" refY="5" '
                    'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                    '<path d="M0 0 L10 5 L0 10 z" fill="%s"/></marker>'
                    % (prefix, name, color))
    defs.append('</defs>')
    parts.append('\n'.join(defs))

    # 先畫邊，後畫節點，咁線就唔會壓住字。
    # taken 記住已經佔咗嘅長方形（節點 + 已擺好嘅標籤），用嚟避開。
    taken = [(n.x - 6, n.y - 6, n.x + n.w + 6, n.y + n.h + 6) for n in nodes]

    # 先行一轉，將每條線佔咗嘅位計晒出嚟。
    # 唔預先計嘅話，排前面嘅標籤避唔到排後面先至畫嘅線，結果字壓住線。
    valid = [e for e in card.edges
             if isinstance(e, dict) and by_id.get(e.get('from')) and by_id.get(e.get('to'))]
    wires = []
    for e in valid:
        _, _, _, pts = _bezier(by_id[e['from']], by_id[e['to']])
        (wx0, wy0), wc1, wc2, (wx3, wy3) = pts
        seg = []
        for k in range(1, 12):
            t = k / 12.0
            u = 1 - t
            bx = u*u*u*wx0 + 3*u*u*t*wc1[0] + 3*u*t*t*wc2[0] + t*t*t*wx3
            by = u*u*u*wy0 + 3*u*u*t*wc1[1] + 3*u*t*t*wc2[1] + t*t*t*wy3
            seg.append((bx - 5, by - 11, bx + 5, by + 11))
        wires.append(seg)
    for ei, e in enumerate(valid):
        a, b = by_id[e['from']], by_id[e['to']]
        ev = e.get('evidence', '引申')
        color, sw, dash, cap = EDGE_STYLE.get(ev, EDGE_STYLE['引申'])
        d, mx, my, pts = _bezier(a, b)
        # 除咗自己條線，其他線都要避開
        others = [r for j, seg in enumerate(wires) if j != ei for r in seg]
        parts.append('<path d="%s" fill="none" stroke="%s" stroke-width="%.1f" '
                     'stroke-dasharray="%s" stroke-linecap="%s" '
                     'marker-end="url(#%s-ar-%s)"><title>%s</title></path>'
                     % (d, color, sw, dash, cap, prefix, ev,
                        esc('【%s】%s' % (ev, e.get('label', '')))))
        label = str(e.get('label', '')).strip()
        if label:
            lines = wrap(label, EDGE_LINE_CHARS)[:2]
            lw = max(_width(l) for l in lines) * FS_EDGE
            lh = len(lines) * EDGE_LINE_H
            # 跨層嘅邊，中點會落喺中間嗰排節點上面。
            # 所以起點揀「離開源頭之後第一個空隙」，再由 _free_spot 執位。
            # 沿住自己條線由上而下試幾個位，務求個標籤留喺自己條邊附近，
            # 唔好飄咗去第二條邊隔籬，搞到讀者唔知邊個標籤配邊條線。
            if abs(a.y - b.y) < 1 or b.top <= a.bottom:
                anchors = [(mx, my)]
            else:
                ys, yy = [], a.bottom + 46
                while yy < b.top - 20 or not ys:
                    ys.append(min(yy, max(a.bottom + 46, b.top - 40)))
                    yy += 60
                anchors = [(_point_at_y(pts, y), y) for y in ys]
            spot = None
            for ax, ay in anchors:
                ax = min(max(ax, PAD_X + lw / 2), width - PAD_X - lw / 2)
                spot = _free_spot(ax, ay, lw, lh, taken + others)
                if spot:
                    break
            lx, ly = spot or (anchors[0][0], anchors[0][1])
            lx = min(max(lx, PAD_X + lw / 2), width - PAD_X - lw / 2)
            taken.append((lx - lw / 2, ly - lh / 2, lx + lw / 2, ly + lh / 2))
            for j, line in enumerate(lines):
                parts.append(
                    '<text x="%.1f" y="%.1f" font-size="%d" fill="%s" '
                    'font-weight="600" text-anchor="middle" paint-order="stroke" '
                    'stroke="#ffffff" stroke-width="6" stroke-linejoin="round">%s</text>'
                    % (lx, ly - lh / 2 + (j + 1) * EDGE_LINE_H - 6,
                       FS_EDGE, color, esc(line)))

    for n in nodes:
        fill, stroke = LAYER_STYLE.get(n.layer, ('#ffffff', '#111827'))
        sw = 3.5 if n.layer in ('字', '結論') else 2.2
        body = ['<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="14" '
                'fill="%s" stroke="%s" stroke-width="%.1f"/>'
                % (n.x, n.y, n.w, n.h, fill, stroke, sw)]
        ty = n.y + NODE_PAD_Y + n.fs * 0.82 + (4 if n.is_char else 0)
        weight = '700' if n.layer in ('字', '結論') else '500'
        for j, line in enumerate(n.lines):
            body.append('<text x="%.1f" y="%.1f" font-size="%d" font-weight="%s" '
                        'fill="#111827" text-anchor="middle">%s</text>'
                        % (n.cx, ty + j * LINE_H, n.fs, weight, esc(line)))
        inner = '\n'.join(body)
        if n.ref:
            inner = ('<a href="#%s-sec-%s" class="nd"><title>%s</title>%s</a>'
                     % (prefix, str(n.ref).replace('.', '-'),
                        esc('跳去第 %s 節' % n.ref), inner))
        parts.append('<g class="nd-g">%s</g>' % inner)

    legend, height = _legend(width, y_end + 4)
    parts.append(legend)

    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d" role="img" aria-label="%s">\n%s\n</svg>'
            % (width, round(height), width, round(height),
               esc('%s 字的推理網絡圖' % card.ch), '\n'.join(parts)))


def main():
    import os
    root = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) < 2:
        sys.exit('用法：python3 netgraph.py <字>')
    card = cardfmt.parse_card(os.path.join(root, sys.argv[1] + '.md'))
    svg = render_svg(card)
    if not svg:
        sys.exit('%s 未有 front matter，畫唔到圖' % sys.argv[1])
    sys.stdout.write(svg + '\n')


if __name__ == '__main__':
    main()
