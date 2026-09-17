#!/usr/bin/env python3
"""將字卡 Markdown 砌成自足 HTML：圖片 base64 內嵌，CJK 字型 subset 內嵌。

出兩種嘢：
  1. **合訂本** —— DEMO.html（本機睇）同 site/index.html，所有卡砌埋一份
  2. **每隻字一份** —— site/cards/<字>.html，之後 build_pdf.py --each 會逐份出 PDF

用法：
  python3 build_demo.py              # 做晒所有卡
  python3 build_demo.py 靜 偉        # 淨係做呢兩張
  python3 build_demo.py --no-each    # 淨係出合訂本，唔出單張
"""
import base64
import io
import os
import re
import sys
import urllib.parse

from markdown_it import MarkdownIt

import fontkit

ROOT = fontkit.ROOT
FONT = fontkit.PRIMARY
SITE = os.path.join(ROOT, 'site')
CARDS = os.path.join(SITE, 'cards')     # 每隻字一份 HTML，俾 build_pdf.py --each 用


def embed_images(html):
    """將 <img src="img/..."> 換成 base64 data URI。"""
    bad = []

    def repl(m):
        src = urllib.parse.unquote(m.group(1))   # markdown-it 會 percent-encode 中文路徑
        path = os.path.join(ROOT, src)
        if not os.path.exists(path):
            bad.append(src)
            return m.group(0)
        data = base64.b64encode(open(path, 'rb').read()).decode()
        return 'src="data:image/png;base64,%s"' % data

    out = re.sub(r'src="([^"]+)"', repl, html)
    return out, bad


def subset_font(path, text):
    """只留實際用到嘅字，令字型由幾 MB 縮到幾百 KB。回傳 base64 woff2。"""
    from fontTools import subset
    opts = subset.Options()
    opts.flavor = 'woff2'
    opts.desubroutinize = True
    opts.ignore_missing_glyphs = True
    font = subset.load_font(path, opts)
    subsetter = subset.Subsetter(options=opts)
    subsetter.populate(text=text)
    subsetter.subset(font)
    buf = io.BytesIO()
    font.flavor = 'woff2'
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def build_font_faces(text):
    """砌 @font-face。主力 NotoSansTC，罕見字交俾 HanaMinA/B。

    冇 HanaMin 嘅話罕見字會變豆腐格 —— 呢度出聲，唔好靜靜哋出爛嘢。
    """
    prim, in_a, in_b, nobody = fontkit.coverage(text)
    faces, stack = [], []

    faces.append("@font-face{font-family:'ZikaMain';src:url(data:font/woff2;base64,%s)"
                 " format('woff2');font-display:swap}" % subset_font(FONT, ''.join(prim)))
    stack.append("'ZikaMain'")

    hana = fontkit.find_hanamin()
    for letter, chars in (('A', in_a), ('B', in_b)):
        if chars and letter in hana:
            faces.append(
                "@font-face{font-family:'ZikaRare%s';src:url(data:font/woff2;base64,%s)"
                " format('woff2');font-display:swap}"
                % (letter, subset_font(hana[letter], ''.join(chars))))
            stack.append("'ZikaRare%s'" % letter)
            print('   罕見字 HanaMin%s: %d 個  %s'
                  % (letter, len(chars), ''.join(sorted(chars))[:30]))

    if nobody:
        print('\n⚠ 呢啲字冇任何字型畫得出，會變豆腐格: %s' % ''.join(sorted(nobody)))
        print('  跑 python3 check_glyphs.py 睇詳情')

    stack.append('sans-serif')
    return '\n'.join(faces), ','.join(stack)


CSS = """
:root{--bg:#fdfdfc;--fg:#1a1a1a;--mut:#666;--line:#e0ded9;--card:#fff;--accent:#8a6d3b}
@media(prefers-color-scheme:dark){:root{--bg:#16161a;--fg:#e8e6e1;--mut:#9a978f;
--line:#32323a;--card:#1e1e24;--accent:#d4b483}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font-family:__STACK__;line-height:1.75;font-size:16px}
#wrap{max-width:900px;margin:0 auto;padding:0 20px 80px}
nav{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);
padding:12px 0;margin-bottom:28px;z-index:10}
nav a{margin-right:18px;color:var(--accent);text-decoration:none;font-weight:600}
h1{font-size:2.6em;border-bottom:3px solid var(--accent);padding-bottom:.2em;margin-top:1.4em}
h2{font-size:1.6em;margin-top:1.8em;border-left:5px solid var(--accent);padding-left:.5em}
h3{font-size:1.2em;margin-top:1.5em;color:var(--accent)}
h4{font-size:1.05em;margin-top:1.2em}
table{border-collapse:collapse;width:100%;margin:1em 0;font-size:.93em;
display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top}
th{background:var(--card);font-weight:600}
img{max-width:100%;background:#fff;border:1px solid var(--line);border-radius:4px}
td img{max-height:120px;display:block;margin:0 auto}
blockquote{border-left:4px solid var(--line);margin:1em 0;padding:.4em 1em;
color:var(--mut);background:var(--card)}
/* 注意：<code> 瀏覽器預設 monospace，而 monospace 多數冇 CJK → 豆腐字。
   一定要明確指定字型，CJK 先至 render 到。 */
code,pre{font-family:__STACK__,ui-monospace,SFMono-Regular,Menlo,monospace}
code{background:var(--card);padding:2px 6px;border-radius:3px;font-size:.9em}
pre{background:var(--card);padding:16px;border-radius:6px;overflow-x:auto;
border:1px solid var(--line);line-height:1.5}
pre code{background:none;padding:0}
hr{border:none;border-top:1px solid var(--line);margin:2.5em 0}
"""


def render_card(md, ch):
    """讀 <字>.md，render 成 <section>。回傳 (原文, section html, 壞連結)。"""
    path = os.path.join(ROOT, '%s.md' % ch)
    if not os.path.exists(path):
        return None
    src = open(path, encoding='utf-8').read()
    html, bad = embed_images(md.render(src))
    return src, '<section id="c%s">%s</section>' % (ord(ch), html), bad


def build_page(chars, sections, text, title, with_nav=True):
    """砌一份自足 HTML。字型淨係 subset 呢一頁用到嘅字。"""
    faces, stack = build_font_faces(text)
    nav = ''
    if with_nav and len(chars) > 1:
        nav = '<nav>%s</nav>' % ''.join(
            '<a href="#c%s">%s</a>' % (ord(c), c) for c in chars)
    return """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<style>%s
%s</style></head><body><div id="wrap">
%s%s</div></body></html>""" % (
        title, faces, CSS.replace('__STACK__', stack), nav, ''.join(sections))


def write(dest, html):
    os.makedirs(os.path.dirname(dest) or '.', exist_ok=True)
    open(dest, 'w', encoding='utf-8').write(html)
    print('出咗: %s  (%.1f MB)' % (dest, os.path.getsize(dest) / 1e6))


# 砌頁面本身會用到、但可能唔喺任何一張卡入面嘅字
EXTRA = '字卡索引結構意思同音交叉核對'


def main():
    args = sys.argv[1:]
    each = '--no-each' not in args
    chars = [a for a in args if not a.startswith('--')] or fontkit.card_files(ROOT)

    md = MarkdownIt('commonmark', {'html': True}).enable('table').enable('strikethrough')

    done, srcs, sections, allbad = [], [], [], []
    for ch in chars:
        got = render_card(md, ch)
        if got is None:
            print('跳過（冇此卡）:', ch)
            continue
        src, section, bad = got
        done.append(ch)
        srcs.append(src)
        sections.append(section)
        allbad += bad
        print('✓ %s  （%d 張圖內嵌）' % (ch, section.count('data:image/png')))

    if allbad:
        print('\n❌ 壞連結:', allbad)
    if not done:
        sys.exit('一張卡都砌唔到')

    # 1. 合訂本
    print('\n── 合訂本 ──')
    page = build_page(done, sections, ''.join(srcs) + ''.join(done) + EXTRA,
                      '字卡 — %s' % '、'.join(done))
    write(os.path.join(ROOT, 'DEMO.html'), page)        # 本機睇
    write(os.path.join(SITE, 'index.html'), page)       # GitHub Pages 睇

    # 2. 每隻字一份（build_pdf.py --each 會攞呢啲去出單字 PDF）
    if each:
        print('\n── 每隻字一份 ──')
        for ch, src, section in zip(done, srcs, sections):
            one = build_page([ch], [section], src + ch + EXTRA,
                             '字卡 — %s' % ch, with_nav=False)
            write(os.path.join(CARDS, '%s.html' % ch), one)


if __name__ == '__main__':
    main()
