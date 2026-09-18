#!/usr/bin/env python3
"""將字卡砌成一個真正嘅網站（GitHub Pages 用）。

同舊嘅 build_demo.py 三個大分別：

  1. **唔再 base64 內嵌。** 字型、圖片、CSS 各自獨立檔案，一個網站共用一份，
     第二頁開始係 cache 命中。舊做法每一頁都內嵌自己一份字型（幾 MB）。
  2. **三層版面。** 第一層推理網絡圖 + 一句總結，第二層總覽四格，
     第三層先至係完整考證（摺埋喺 <details> 入面）。
  3. **相對路徑。** GitHub Pages 喺 /zika/ 子路徑，所有連結一律相對，
     唔可以用 /assets/…，否則本機開得成、上線就爛。

出咩：
  site/index.html           首頁
  site/cards/<字>.html      每隻字一頁
  site/all.html             合訂本（淨係俾 build_pdf.py 出 PDF 用）
  site/assets/{fonts.css,style.css,site.js,fonts/*.woff2}
  site/img/**  site/pdf/**  site/qr.png

用法：
  python3 build_site.py                 全部
  python3 build_site.py 靜 偉           淨係砌呢兩張（首頁照出全部）
"""
import hashlib
import os
import re
import shutil
import sys
import urllib.parse

from markdown_it import MarkdownIt

import cardfmt
import fontkit
import netgraph
import ui_strings

ROOT = fontkit.ROOT
SITE = os.path.join(ROOT, 'site')
SITE_URL = os.environ.get('ZIKA_SITE_URL', 'https://ckckkckccom-cpu.github.io/zika/')

# 書體排序：檔名頭嗰個編號已經係年代次序
STROKE_ORDER = re.compile(r'^(\d+)([a-z]?)_(.+)\.png$')


# ──────────────────────────────────────────────────────────
# Markdown → HTML
# ──────────────────────────────────────────────────────────

def _plain(tok):
    """attrs／data-label 用嘅純文字，剝走粗體等記號。"""
    out = []
    for c in (tok.children or []):
        if c.type in ('text', 'code_inline'):
            out.append(c.content)
    return ''.join(out).strip()


def table_labels(state):
    """俾每個 <td> 加 data-label，手機上表格可以逐列堆疊。

    另外：表格入面有圖就標 .t-img —— 五期字形一定要並排先比較到，
    堆疊咗就冇晒意思，所以嗰類表格唔堆疊，改為橫向捲。
    """
    toks = state.tokens
    i, n = 0, len(toks)
    while i < n:
        if toks[i].type != 'table_open':
            i += 1
            continue
        headers, in_head, has_img, col = [], False, False, 0
        j = i + 1
        while j < n and toks[j].type != 'table_close':
            t = toks[j]
            if t.type == 'thead_open':
                in_head = True
            elif t.type == 'thead_close':
                in_head = False
            elif t.type == 'tr_open':
                col = 0
            elif t.type == 'th_open' and in_head and j + 1 < n:
                headers.append(_plain(toks[j + 1]))
            elif t.type == 'td_open':
                if col < len(headers) and headers[col]:
                    t.attrSet('data-label', headers[col])
                col += 1
            elif t.type == 'inline' and any(
                    c.type == 'image' for c in (t.children or [])):
                has_img = True
            j += 1
        if has_img:
            toks[i].attrJoin('class', 't-img')
        i = j + 1


def anchor_id(ch, text):
    """`### 1.3 部件分解` → `靜-sec-1-3`；其餘標題用序數，保證唯一。"""
    m = re.match(r'\s*(\d+)(?:\.(\d+))?[.、．]?\s', text)
    if not m:
        return None
    num = m.group(1) if m.group(2) is None else '%s-%s' % (m.group(1), m.group(2))
    return '%s-sec-%s' % (ch, num)


def make_md():
    md = MarkdownIt('commonmark', {'html': True}).enable('table').enable('strikethrough')
    md.core.ruler.push('zika_table_labels', table_labels)

    def heading_open(self, tokens, idx, options, env):
        tok = tokens[idx]
        text = _plain(tokens[idx + 1]) if idx + 1 < len(tokens) else ''
        aid = anchor_id(env.get('ch', ''), text)
        if aid:
            tok.attrSet('id', aid)
        return self.renderToken(tokens, idx, options, env)

    def link_open(self, tokens, idx, options, env):
        tok = tokens[idx]
        href = tok.attrGet('href') or ''
        if href and '://' not in href and not href.startswith('#'):
            # 卡與卡之間互相引用寫嘅係 偉.md，網站冇 .md，要改指去 .html
            name = urllib.parse.unquote(href)
            if name.endswith('.md'):
                tok.attrSet('href', '%scards/%s.html'
                            % (env.get('root', ''),
                               urllib.parse.quote(name[:-3])))
        return self.renderToken(tokens, idx, options, env)

    def image(self, tokens, idx, options, env):
        tok = tokens[idx]
        src = tok.attrGet('src') or ''
        if src and '://' not in src and not src.startswith('data:'):
            tok.attrSet('src', env.get('root', '') + src)
        tok.attrSet('loading', 'lazy')
        return self.renderToken(tokens, idx, options, env)

    md.add_render_rule('heading_open', heading_open)
    md.add_render_rule('link_open', link_open)
    md.add_render_rule('image', image)
    return md


_MARK = re.compile(r'【(原文|觀察|分歧|引申)】')


def badges(html):
    """四個標記轉做彩色徽章。呢四個記號係成個 project 嘅命脈，要一眼睇到。"""
    return _MARK.sub(lambda m: '<span class="mk mk-%s">【%s】</span>'
                     % (m.group(1), m.group(1)), html)


def render(md, text, ch, root):
    return badges(md.render(text, {'ch': ch, 'root': root}))


# ──────────────────────────────────────────────────────────
# 字型
# ──────────────────────────────────────────────────────────

def build_fonts(text):
    """砌全站共用嘅 subset 字型，回傳 fonts.css 內容。

    檔名帶內容 hash：加咗新字之後，舊 cache 唔會靜靜哋繼續供應舊 subset
    （個結果會係手機出豆腐格，而且本機重現唔到）。
    """
    outdir = os.path.join(SITE, 'assets', 'fonts')
    os.makedirs(outdir, exist_ok=True)
    for old in os.listdir(outdir):
        os.remove(os.path.join(outdir, old))

    prim, in_a, in_b, in_dv, nobody = fontkit.coverage(text)
    hana = fontkit.find_hanamin()
    dv = fontkit.find_dejavu()

    jobs = [('ZikaMain', fontkit.PRIMARY, prim)]
    for letter in ('A', 'B'):
        chars = in_a if letter == 'A' else in_b
        if chars and letter in hana:
            jobs.append(('ZikaRare%s' % letter, hana[letter], chars))
    # DejaVu 一定要內嵌。手機（iOS／Android）根本冇裝，
    # 靠佢頂住嘅 IPA 附加符號同 ✓✗ 會靜靜哋變豆腐格。
    if in_dv and dv:
        jobs.append(('ZikaSym', dv, in_dv))

    css = []
    for family, path, chars in jobs:
        data = fontkit.subset_bytes(path, ''.join(sorted(chars)))
        h = hashlib.sha1(data).hexdigest()[:8]
        name = '%s-%s.woff2' % (family, h)
        open(os.path.join(outdir, name), 'wb').write(data)
        css.append("@font-face{font-family:'%s';src:url(fonts/%s) format('woff2');"
                   "font-display:swap}" % (family, name))
        print('   字型 %-9s %5d 字  %6.0f KB' % (family, len(chars), len(data) / 1024))

    if nobody:
        print('\n⚠ 呢啲字冇任何字型畫得出，會變豆腐格: %s' % ''.join(sorted(nobody)))
    return '\n'.join(css) + '\n'


# ──────────────────────────────────────────────────────────
# 版面零件
# ──────────────────────────────────────────────────────────

def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def head(title, desc, root, extra=''):
    return """<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="stylesheet" href="%sassets/fonts.css">
<link rel="stylesheet" href="%sassets/style.css">
<script>/* 早啲套用字體大小，避免載入時跳一跳 */
try{var _i=+localStorage.getItem('zika-fs')||0;
document.documentElement.style.setProperty('--fs-base',['20px','24px','28px'][_i]||'20px');}catch(e){}</script>
%s</head>
<body>
""" % (esc(title), esc(desc), root, root, extra)


def topbar(root, prev=None, nxt=None):
    out = ['<header class="topbar"><div class="inner">']
    out.append('<a class="btn btn-home" href="%sindex.html">%s</a>'
               % (root, ui_strings.NAV_HOME))
    if prev is not None or nxt is not None:
        for label, target in ((ui_strings.NAV_PREV, prev), (ui_strings.NAV_NEXT, nxt)):
            if target:
                out.append('<a class="btn" href="%s.html">%s　%s</a>'
                           % (urllib.parse.quote(target), label, esc(target)))
            else:
                out.append('<span class="btn" aria-disabled="true">%s</span>' % label)
    out.append('<span class="spacer"></span>')
    out.append('<div class="fs-ctl" aria-label="%s">'
               '<button class="btn" data-step="-" title="%s">%s</button>'
               '<button class="btn" data-step="+" title="%s">%s</button></div>'
               % (ui_strings.FS_LABEL, ui_strings.FS_SMALLER, ui_strings.FS_SMALLER,
                  ui_strings.FS_LARGER, ui_strings.FS_LARGER))
    out.append('</div></header>')
    return ''.join(out)


def tail(root):
    return """<dialog id="lb" class="lightbox"><div class="lb-body"></div>
<button class="btn lb-close">關閉</button></dialog>
<footer class="site"><p>%s ・ <a href="%sindex.html">%s</a></p></footer>
<script src="%sassets/site.js"></script>
</body></html>
""" % (ui_strings.SITE_TITLE, root, ui_strings.BACK_TO_INDEX, root)


def strip_html(ch, root):
    """字形演變圖帶：直接由 img/<字>/ 嘅檔名砌，唔使人手維護。"""
    d = os.path.join(ROOT, 'img', ch)
    if not os.path.isdir(d):
        return ''
    items = []
    for fn in sorted(os.listdir(d)):
        m = STROKE_ORDER.match(fn)
        if not m:
            continue
        caption = m.group(3).replace('_', '・')
        src = '%simg/%s/%s' % (root, urllib.parse.quote(ch), urllib.parse.quote(fn))
        items.append('<figure><img src="%s" alt="%s %s" loading="lazy">'
                     '<figcaption>%s</figcaption></figure>'
                     % (src, esc(ch), esc(caption), esc(caption)))
    if not items:
        return ''
    return ('<h2>%s</h2>\n<div class="strip">%s</div>\n<p class="hint">%s</p>\n'
            % (ui_strings.SEC_EVOLUTION, ''.join(items), ui_strings.IMG_HINT))


_OV_BLOCK = re.compile(r'^###\s*(\S+)\s*$(.*?)(?=^###\s|\Z)', re.M | re.S)


def overview_html(md, card, root):
    """總覽四格。每格自己一個方塊，唔用一長條文字。"""
    _, ov, _ = cardfmt.split_body(card.body)
    blocks = _OV_BLOCK.findall(ov)
    if not blocks:
        return ''
    out = ['<h2>%s</h2>\n<div class="ov">' % ui_strings.SEC_OVERVIEW]
    for name, body in blocks:
        out.append('<section id="%s-ov-%s"><h3>%s</h3>%s</section>'
                   % (esc(card.ch), esc(name), esc(name),
                      render(md, body, card.ch, root)))
    out.append('</div>')
    return ''.join(out)


def detail_html(md, card, root, open_default=False):
    _, _, detail = cardfmt.split_body(card.body)
    detail = re.sub(r'^##\s*詳細考證\s*$', '', detail, count=1, flags=re.M)
    body = render(md, detail, card.ch, root)
    return ('<details class="deep"%s><summary>%s'
            '<span class="sub">%s</span></summary>'
            '<div class="deep-body">%s</div></details>'
            % (' open' if open_default else '', ui_strings.SEC_DETAIL,
               ui_strings.SEC_DETAIL_HINT, body))


def hero_html(card, root, heading=False):
    jyut = '／'.join(card.jyutping)
    tag = 'h1' if heading else 'div'
    out = ['<div class="hero">',
           '<%s class="glyph" id="%s-top">%s</%s>' % (tag, esc(card.ch), esc(card.ch), tag)]
    if jyut:
        out.append('<div class="jyut">%s %s</div>' % (ui_strings.JYUTPING_LABEL, esc(jyut)))
    if card.verdict:
        out.append('<p class="verdict">%s</p>' % esc(card.verdict))
    out.append('</div>')
    return ''.join(out)


def net_html(card):
    svg = netgraph.render_svg(card)
    if not svg:
        return '<p class="hint">%s</p>' % ui_strings.FMT_LEGACY
    return ('<h2>%s</h2>\n<div class="net">%s</div>\n<p class="hint">%s</p>\n'
            % (ui_strings.SEC_NETWORK, svg, '按方格可跳去對應章節；按圖可放大'))


def card_page(md, card, prev, nxt):
    root = '../'
    body = [head('%s — %s' % (card.ch, ui_strings.SITE_TITLE),
                 card.verdict or ui_strings.SITE_SUB, root),
            topbar(root, prev, nxt),
            '<main>',
            hero_html(card, root, heading=True),
            net_html(card),
            strip_html(card.ch, root),
            overview_html(md, card, root),
            detail_html(md, card, root)]
    pdf = os.path.join(ROOT, 'pdf', '%s.pdf' % card.ch)
    if os.path.exists(pdf):
        body.append('<p class="cards-nav no-print"><a class="btn" href="%spdf/%s.pdf">'
                    '下載「%s」的 PDF</a></p>'
                    % (root, urllib.parse.quote(card.ch), esc(card.ch)))
    body.append('</main>')
    body.append(tail(root))
    return '\n'.join(body)


def index_page(cards):
    root = ''
    tiles = []
    for c in cards:
        tiles.append('<a class="tile" href="cards/%s.html"><span class="glyph">%s</span>'
                     '<span class="jyut">%s</span><span class="verdict">%s</span></a>'
                     % (urllib.parse.quote(c.ch), esc(c.ch),
                        esc('／'.join(c.jyutping)), esc(c.verdict)))
    legend = ''.join(
        '<div><span class="mk mk-%s">【%s】</span><p>%s</p></div>' % (n, n, esc(d))
        for n, d in ui_strings.MARKS)
    howto = ''.join('<li>%s</li>' % esc(s) for s in ui_strings.HOWTO_STEPS)

    pdfs = []
    if os.path.exists(os.path.join(ROOT, '字卡.pdf')):
        pdfs.append('<a class="btn" href="pdf/%s">%s</a>'
                    % (urllib.parse.quote('字卡.pdf'), ui_strings.PDF_ALL))
    for c in cards:
        if os.path.exists(os.path.join(ROOT, 'pdf', '%s.pdf' % c.ch)):
            pdfs.append('<a class="btn" href="pdf/%s.pdf">%s</a>'
                        % (urllib.parse.quote(c.ch), esc(c.ch)))

    body = [head(ui_strings.SITE_TITLE, ui_strings.SITE_SUB, root),
            topbar(root),
            '<main>',
            '<div class="site-head"><h1>%s</h1><p class="sub">%s</p></div>'
            % (ui_strings.SITE_TITLE, ui_strings.SITE_SUB),
            '<h2>%s</h2>' % ui_strings.SEC_CARDS,
            '<div class="tiles">%s</div>' % ''.join(tiles) if tiles
            else '<p>%s</p>' % ui_strings.NO_CARDS,
            '<h2>%s</h2><ol>%s</ol>' % (ui_strings.SEC_HOWTO, howto),
            '<h2>%s</h2><div class="legend">%s</div>' % (ui_strings.SEC_LEGEND, legend),
            '<h2>%s</h2><p>%s</p><p class="cards-nav">%s</p>'
            % (ui_strings.SEC_PDF, ui_strings.PDF_NOTE, ''.join(pdfs)),
            '<h2>%s</h2><p>%s</p><p>%s</p>'
            % (ui_strings.ADD_HOME_TITLE, ui_strings.ADD_HOME_IOS,
               ui_strings.ADD_HOME_AND),
            '<p><img src="qr.png" alt="網址二維碼" width="180" height="180"></p>',
            '</main>', tail(root)]
    return '\n'.join(body)


def all_page(md, cards):
    """合訂本。淨係俾 build_pdf.py 出 PDF 用，唔喺首頁連出去。"""
    root = ''
    body = [head('%s — %s' % (ui_strings.SITE_TITLE, '、'.join(c.ch for c in cards)),
                 ui_strings.SITE_SUB, root),
            '<main>',
            '<div class="site-head"><h1>%s</h1><p class="sub">%s</p></div>'
            % (ui_strings.SITE_TITLE, ui_strings.SITE_SUB)]
    for c in cards:
        body += ['<section class="card-all">',
                 hero_html(c, root),
                 net_html(c),
                 strip_html(c.ch, root),
                 overview_html(md, c, root),
                 detail_html(md, c, root, open_default=True),
                 '</section>', '<hr>']
    body += ['</main>', tail(root)]
    return '\n'.join(body)


# ──────────────────────────────────────────────────────────
# 靜態檔 + 檢查
# ──────────────────────────────────────────────────────────

def copy_static():
    os.makedirs(os.path.join(SITE, 'assets'), exist_ok=True)
    for name in ('style.css', 'site.js'):
        shutil.copy2(os.path.join(ROOT, 'assets', name),
                     os.path.join(SITE, 'assets', name))
    shutil.copytree(os.path.join(ROOT, 'img'), os.path.join(SITE, 'img'),
                    dirs_exist_ok=True)
    dest = os.path.join(SITE, 'pdf')
    os.makedirs(dest, exist_ok=True)
    src = os.path.join(ROOT, 'pdf')
    if os.path.isdir(src):
        for fn in os.listdir(src):
            if fn.endswith('.pdf'):
                shutil.copy2(os.path.join(src, fn), os.path.join(dest, fn))
    book = os.path.join(ROOT, '字卡.pdf')
    if os.path.exists(book):
        shutil.copy2(book, os.path.join(dest, '字卡.pdf'))


def write_qr():
    try:
        import segno
    except ImportError:
        print('   （冇裝 segno，跳過二維碼）')
        return
    segno.make(SITE_URL, error='m').save(
        os.path.join(SITE, 'qr.png'), scale=6, border=2, dark='#16181d')


_HREF = re.compile(r'(?:href|src)="([^"]+)"')
_ID = re.compile(r'\bid="([^"]+)"')


def check_links():
    """靜態檢查：每個內部連結指到嘅檔存唔存在、每個 #錨點有冇對應 id。

    Pages 喺 /zika/ 子路徑，一個 `/assets/…` 就足以令成個網站喺線上爛晒，
    但喺本機 file:// 睇落完全正常。所以呢一步係必要嘅。
    """
    bad = []
    pages = []
    for base, _, files in os.walk(SITE):
        for fn in files:
            if fn.endswith('.html'):
                pages.append(os.path.join(base, fn))
    for page in pages:
        html = open(page, encoding='utf-8').read()
        ids = set(_ID.findall(html))
        here = os.path.dirname(page)
        rel = os.path.relpath(page, SITE)
        for link in _HREF.findall(html):
            if link.startswith(('http://', 'https://', 'data:', 'mailto:')):
                continue
            if link.startswith('/'):
                bad.append('%s：用咗絕對路徑 %s（Pages 喺子路徑，一定爛）' % (rel, link))
                continue
            path, _, frag = link.partition('#')
            if path:
                target = os.path.normpath(os.path.join(here, urllib.parse.unquote(path)))
                if not os.path.exists(target):
                    bad.append('%s：連結指去唔存在嘅檔 %s' % (rel, link))
            elif frag and urllib.parse.unquote(frag) not in ids:
                bad.append('%s：錨點 #%s 喺本頁搵唔到' % (rel, urllib.parse.unquote(frag)))
    return bad


def write(path, text):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    open(path, 'w', encoding='utf-8').write(text)
    print('   出咗 %-32s %6.0f KB' % (os.path.relpath(path, ROOT),
                                      len(text.encode()) / 1024))


def main():
    only = [a for a in sys.argv[1:] if not a.startswith('--')]
    cards = cardfmt.cards_in(ROOT)
    if not cards:
        sys.exit('一張卡都搵唔到')

    print('── 檢查字卡格式 ──')
    fatal = 0
    for c in cards:
        errs, warns = cardfmt.validate(c)
        for e in errs:
            print('   ✗ %s' % e)
            fatal += 1
        for w in warns:
            print('   ! %s' % w)
    if fatal:
        sys.exit('\n有 %d 個錯，改好先再砌。' % fatal)
    print('   %d 張卡，%d 張已升級 v3'
          % (len(cards), sum(1 for c in cards if c.is_v3)))

    print('\n── 字型 ──')
    os.makedirs(SITE, exist_ok=True)
    fonts_css = build_fonts(fontkit.cards_text(ROOT))
    write(os.path.join(SITE, 'assets', 'fonts.css'), fonts_css)

    print('\n── 靜態檔 ──')
    copy_static()
    write_qr()
    print('   圖片、樣式、PDF 已複製')

    md = make_md()
    targets = [c for c in cards if not only or c.ch in only]

    print('\n── 字卡 ──')
    for i, c in enumerate(cards):
        if c not in targets:
            continue
        prev = cards[i - 1].ch if i > 0 else None
        nxt = cards[i + 1].ch if i < len(cards) - 1 else None
        write(os.path.join(SITE, 'cards', '%s.html' % c.ch),
              card_page(md, c, prev, nxt))

    print('\n── 首頁同合訂本 ──')
    write(os.path.join(SITE, 'index.html'), index_page(cards))
    write(os.path.join(SITE, 'all.html'), all_page(md, cards))

    print('\n── 連結檢查 ──')
    bad = check_links()
    if bad:
        for b in bad[:30]:
            print('   ✗ %s' % b)
        sys.exit('\n有 %d 個爛連結。' % len(bad))
    print('   ✓ 全部連結同錨點都通')
    print('\n網站砌好咗：%s' % os.path.relpath(SITE, ROOT))


if __name__ == '__main__':
    main()
