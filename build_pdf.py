#!/usr/bin/env python3
"""由 build_site.py 出嘅網頁砌 PDF。

兩個模式：
  python3 build_pdf.py [輸出檔名]      # 合訂本，由 site/all.html 出（預設 字卡.pdf）
  python3 build_pdf.py --each [資料夾]  # 每隻字一份，由 site/cards/<字>.html 出

先跑 build_site.py。

紙本同螢幕嘅分別，大部分已經寫喺 assets/style.css 個 @media print 入面
（收起導覽、收起摺疊掣、表格唔堆疊）。呢度淨係處理三件淨係 PDF 先有嘅事：
  1. 字型一定要用系統裝住嘅 TrueType（見下面 PRINT_CSS 註）
  2. <details> 要全部打開，否則詳細考證印唔到出嚟
  3. 頁邊、頁碼、分頁位置
"""
import os
import shutil
import sys
import urllib.parse

from playwright.sync_api import sync_playwright

import fontkit
import localserver

ROOT = fontkit.ROOT
SITE = os.path.join(ROOT, 'site')
PDF_DIR = os.path.join(ROOT, 'pdf')

PRINT_CSS = """
/* Chromium 嘅 page.pdf() 行 Skia PDF backend，嵌入 CFF/OTF（PostScript 輪廓）
   字型會靜靜哋失敗 —— 中文全部消失（實測 PDF 入面 CJK 字數 = 0），
   連內嵌 woff2 @font-face 都唔幫得手。螢幕截圖路徑冇呢個問題，所以淨係影響 PDF。
   解決：make_pdf_font.py 將字型轉成 TrueType 再裝入系統，呢度叫佢個家族名。
   罕見字嗰兩隻特登叫 ZikaRareAPdf／BPdf，同網頁嗰個 @font-face 撞名嘅話，
   網頁版會贏咗系統字型，結果變成靠運氣。
   最尾一定要留返 DejaVu：NotoSansTC 係純 CJK 字型，冇 ✓ ✗ ○ 呢類符號。 */
*{font-family:'NotoSansTCPdf','ZikaRareAPdf','ZikaRareBPdf','DejaVu Sans',sans-serif!important}
@page{size:A4;margin:14mm 12mm}
html{font-size:12pt}
html,body{background:#fff!important}
#lb,dialog,.topbar,.fs-ctl,.hint,.no-print{display:none!important}
main{max-width:none;padding:0}
body{line-height:1.6}
/* 螢幕上摺埋嘅詳細考證，紙本一定要攤開（open 由 JS 設，呢度淨係收起個掣） */
details.deep{border-top:none;margin-top:1.2rem}
details.deep>summary{display:none!important}
.deep-body{padding-top:0}
table{font-size:9.5pt;table-layout:fixed;width:100%!important;page-break-inside:auto}
.t-img{display:table!important;overflow:visible!important;white-space:normal!important}
th,td{padding:3px 5px;word-wrap:break-word;overflow-wrap:anywhere}
tr{page-break-inside:avoid}
thead{display:table-header-group}
td img{max-height:70px}
.strip{max-width:none;grid-template-columns:repeat(7,1fr);gap:4px}
.strip img{height:56px}
.strip figcaption{font-size:7pt}
/* 幅圖好高。唔夾住高度嘅話，佢會頂到成頁都放唔落，
   結果彈去下一頁，第一頁得個大字同一句總結，中間一大片空白。 */
.net{page-break-inside:avoid;border:none;padding:0;text-align:center}
.net svg{max-width:150mm;max-height:170mm;width:auto;height:auto}
.info{grid-template-columns:repeat(4,1fr);page-break-inside:avoid;margin:.4rem 0 .6rem}
.info .ic{font-size:7.5pt;padding:1.5px 4px;line-height:1.4}
.ov{display:block}
.ov section{page-break-inside:avoid;margin-bottom:.6rem}
.hero{padding:0}
.hero .glyph{font-size:36pt}
.hero .verdict{padding:.35rem .8rem;margin-top:.3rem}
h2{margin:1rem 0 .4rem;font-size:15pt}
h3{margin:.8rem 0 .3rem}
h1{page-break-before:always;font-size:24pt;margin-top:0}
section.card-all:first-of-type h1,main>.hero:first-of-type .glyph{page-break-before:avoid}
h2,h3,h4{page-break-after:avoid}
blockquote,pre,img{page-break-inside:avoid}
pre{font-size:8.5pt}
a{color:#000!important;text-decoration:none}
footer.site{display:none}
"""

FOOTER = ('<div style="width:100%;font-size:8pt;color:#888;text-align:center;'
          'padding-top:4px"><span class="pageNumber"></span> / '
          '<span class="totalPages"></span></div>')


def render(pg, url, out):
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    pg.goto(url, wait_until='networkidle')
    # 詳細考證喺螢幕上係摺埋嘅。唔打開就會印出一份得個殼嘅 PDF，
    # 而且唔會報錯 —— check_pdf.py 係最後道防線。
    pg.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
    pg.evaluate("document.fonts.ready")
    pg.wait_for_timeout(1200)
    pg.add_style_tag(content=PRINT_CSS)
    pg.emulate_media(media='print', color_scheme='light')
    pg.wait_for_timeout(600)
    pg.pdf(path=out, format='A4', print_background=True,
           margin={'top': '14mm', 'bottom': '14mm', 'left': '12mm', 'right': '12mm'},
           display_header_footer=True,
           header_template='<div></div>', footer_template=FOOTER)
    print('   出咗 %-24s %6.2f MB' % (os.path.relpath(out, ROOT),
                                      os.path.getsize(out) / 1e6))


def jobs_each(outdir):
    out = []
    for ch in fontkit.card_files(ROOT):
        src = os.path.join(SITE, 'cards', '%s.html' % ch)
        if not os.path.exists(src):
            print('   跳過（冇 %s）—— 請先跑 build_site.py' % os.path.relpath(src, ROOT))
            continue
        out.append(('cards/%s.html' % ch, os.path.join(outdir, '%s.pdf' % ch)))
    return out


def copy_into_site(paths):
    """砌好嘅 PDF 放埋落網站度，令網頁可以俾人直接下載。"""
    dest = os.path.join(SITE, 'pdf')
    os.makedirs(dest, exist_ok=True)
    for p in paths:
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(dest, os.path.basename(p)))


def main():
    args = sys.argv[1:]
    if not os.path.isdir(SITE):
        sys.exit('冇 site/ —— 請先跑 python3 build_site.py')

    if '--each' in args:
        rest = [a for a in args if not a.startswith('--')]
        jobs = jobs_each(rest[0] if rest else PDF_DIR)
        if not jobs:
            sys.exit('冇單張卡 HTML —— 請先跑 build_site.py')
    else:
        if not os.path.exists(os.path.join(SITE, 'all.html')):
            sys.exit('搵唔到 site/all.html —— 請先跑 build_site.py')
        jobs = [('all.html', args[0] if args else os.path.join(ROOT, '字卡.pdf'))]

    httpd, port = localserver.serve(os.path.dirname(SITE))
    base = 'http://127.0.0.1:%d/site/' % port
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            for rel, out in jobs:
                render(pg, base + urllib.parse.quote(rel), out)
            b.close()
    finally:
        httpd.shutdown()

    copy_into_site([out for _, out in jobs])


if __name__ == '__main__':
    main()
