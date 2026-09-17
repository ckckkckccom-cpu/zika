#!/usr/bin/env python3
"""由 DEMO.html 出 PDF。

用法：python3 build_pdf.py [輸出檔名]
先跑 build_demo.py 出 DEMO.html，再跑呢個。
"""
import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'DEMO.html')

# 螢幕版同紙本版要求唔同，呢度逐項覆蓋：
PRINT_CSS = """
/* 關鍵：Chromium 嘅 page.pdf() 行 Skia PDF backend，嵌入 CFF/OTF（PostScript 輪廓）
   字型會靜靜哋失敗 —— 中文全部消失（實測 PDF 入面 CJK 字數 = 0），連內嵌 woff2
   @font-face 都唔幫得手。螢幕截圖路徑冇呢個問題，所以淨係影響 PDF。
   解決：make_pdf_font.py 將字型轉成 TrueType 輪廓再裝入系統，呢度叫佢個家族名。 */
/* NotoSansTC 係純 CJK 文字字型，冇 ✓ ✗ ○ 呢類符號 —— 一定要留 DejaVu 做 fallback，
   唔係啲符號會變豆腐格（用 *{...!important} 嗰陣特別易中招）。 */
*{font-family:'NotoSansTCPdf','ZikaRareA','ZikaRareB','DejaVu Sans',sans-serif!important}
@page{size:A4;margin:14mm 12mm}
html,body{background:#fff!important;color:#000!important}
/* 螢幕嗰個深色模式唔可以帶落紙 */
:root{--bg:#fff!important;--fg:#000!important;--mut:#555!important;
--line:#bbb!important;--card:#f6f5f2!important;--accent:#7a5c2e!important}
nav{display:none!important}            /* sticky 導覽喺紙上冇用 */
#wrap{max-width:none;padding:0}
body{font-size:10.5pt;line-height:1.6}
/* 表格：螢幕用 block+overflow 橫向捲，紙上要變返真表格先睇到齊 */
table{display:table!important;width:100%!important;table-layout:fixed;
font-size:8.6pt;overflow:visible!important;page-break-inside:auto}
th,td{padding:3px 5px;word-wrap:break-word;overflow-wrap:anywhere}
tr{page-break-inside:avoid}
thead{display:table-header-group}      /* 跨頁時重複表頭 */
td img{max-height:78px}
h1{page-break-before:always;font-size:2em;margin-top:0}
section:first-of-type h1{page-break-before:avoid}
h2,h3,h4{page-break-after:avoid}
h2{font-size:1.3em}h3{font-size:1.1em}
pre,blockquote,img{page-break-inside:avoid}
pre{font-size:8pt;line-height:1.35}
a{color:#000!important;text-decoration:none}
"""


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, '字卡.pdf')
    if not os.path.exists(SRC):
        sys.exit('搵唔到 %s — 請先跑 build_demo.py' % SRC)
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto('file://' + SRC)
        pg.wait_for_timeout(2500)          # 等字型同 base64 圖 load 晒
        pg.add_style_tag(content=PRINT_CSS)
        pg.emulate_media(media='print', color_scheme='light')
        pg.wait_for_timeout(800)
        pg.pdf(path=out, format='A4', print_background=True,
               margin={'top': '14mm', 'bottom': '14mm',
                       'left': '12mm', 'right': '12mm'},
               display_header_footer=True,
               header_template='<div></div>',
               footer_template='<div style="width:100%;font-size:8pt;color:#888;'
                               'text-align:center;padding-top:4px">'
                               '<span class="pageNumber"></span> / '
                               '<span class="totalPages"></span></div>')
        b.close()

    print('出咗: %s  (%.2f MB)' % (out, os.path.getsize(out) / 1e6))


if __name__ == '__main__':
    main()
