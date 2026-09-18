#!/usr/bin/env python3
"""字型共用邏輯 —— build_demo.py、make_pdf_font.py、check_glyphs.py 都用呢度。

點解要三隻字型：

  NotoSansTC   主力，靚，但係「繁體常用字」子集 —— 唔覆蓋 CJK 擴展區。
  HanaMinA     補 CJK 擴展 A（例如「㣇」＝說文㣇部，豪字嘅形符）同埋
               冷僻嘅基本區字（籒 爲 鬛 筓 呢啲舊字形）。
  HanaMinB     補 CJK 擴展 B（例如「𩫚」＝說文「豪」本字、「𩫕」＝籀文）。

呢啲罕見字係【原文】引文嘅一部分，**唔可以用常見字代替** —— 咁做等於改古籍原文。
所以一定要用覆蓋得到嘅字型，唔係改個文。

HanaMin 喺 Ubuntu 叫 fonts-hanazono（apt 裝到）。冇裝嘅話，罕見字會變豆腐格，
check_glyphs.py 會出聲。
"""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

PRIMARY = os.path.join(ROOT, 'fonts', 'NotoSansTC-Regular.otf')

# 順序有意思：搵到邊隻用邊隻，前面優先
HANAMIN_DIRS = [
    os.path.expanduser('~/.local/share/fonts'),
    '/usr/share/fonts/truetype/hanazono',
    '/usr/share/fonts/opentype/hanazono',
    os.path.join(ROOT, 'fonts'),
]


# DejaVu Sans —— 純西文／符號字型，喺 PDF 同 HTML 嘅 fallback stack 最尾
# （見 build_pdf.py 嘅 PRINT_CSS，同 CLAUDE.md「四個已知字型坑」第 3 條）。
# 佢負責 NotoSansTC 同 HanaMin 都冇嘅符號，例如 ✓ ✗ ○ 同 IPA 附加符號
# （上古音構擬會用到 n̥ 咁嘅組合符號 U+0325）。呢度要檢查佢，
# 否則 check_glyphs.py 會就住呢啲字報假警。
DEJAVU_PATHS = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/TTF/DejaVuSans.ttf',
    '/Library/Fonts/DejaVuSans.ttf',
    os.path.join(ROOT, 'fonts', 'DejaVuSans.ttf'),
]


def find_dejavu():
    """搵 DejaVu Sans，搵唔到回傳 None。"""
    for p in DEJAVU_PATHS:
        if os.path.exists(p):
            return p
    return None


def find_hanamin():
    """搵 HanaMinA / HanaMinB，回傳 {'A': path, 'B': path}，搵唔到就唔放入去。"""
    out = {}
    for letter in ('A', 'B'):
        for d in HANAMIN_DIRS:
            p = os.path.join(d, 'HanaMin%s.ttf' % letter)
            if os.path.exists(p):
                out[letter] = p
                break
    return out


# 呢啲 .md 唔係字卡，係俾人／Claude 睇嘅說明，唔會 render 入 PDF
NOT_CARDS = {'CLAUDE.md', 'README.md', 'SETUP.md'}


def card_files(root=ROOT):
    """邊啲 .md 先算係字卡（一隻字一張卡）。"""
    return [f[:-3] for f in sorted(os.listdir(root))
            if f.endswith('.md') and f not in NOT_CARDS and not f.startswith('_')]


def cards_text(root=ROOT):
    """所有字卡用到嘅字元，連網站介面文字。

    介面文字（「上一字」「放大字體」…）好多時唔喺任何一張卡入面。
    如果唔加入 subset 範圍，佢哋喺網頁同 PDF 都會變豆腐格，而且唔會報錯。
    單一來源喺 ui_strings.py。
    """
    import ui_strings
    t = ''
    for name in card_files(root):
        t += open(os.path.join(root, name + '.md'), encoding='utf-8').read()
    return t + ui_strings.ALL_TEXT


def subset_bytes(path, text, flavor='woff2'):
    """只留實際用到嘅字，令字型由幾 MB 縮到幾百 KB。回傳 bytes。"""
    import io
    from fontTools import subset
    opts = subset.Options()
    opts.flavor = flavor
    opts.desubroutinize = True
    opts.ignore_missing_glyphs = True
    font = subset.load_font(path, opts)
    sub = subset.Subsetter(options=opts)
    sub.populate(text=text)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = flavor
    font.save(buf)
    return buf.getvalue()


def coverage(text):
    """將每個字元分去邊隻字型負責。

    回傳 (primary_chars, hana_a_chars, hana_b_chars, dejavu_chars, nobody_chars)

    次序同 render 時嘅 fallback stack 一樣：
    NotoSansTC → HanaMinA → HanaMinB → DejaVu Sans。
    """
    from fontTools.ttLib import TTFont

    chars = {c for c in text if not c.isspace()}
    prim = set(TTFont(PRIMARY).getBestCmap())

    hana = find_hanamin()
    cmaps = {}
    for letter, path in hana.items():
        cmaps[letter] = set(TTFont(path).getBestCmap())

    dv = find_dejavu()
    dv_cmap = set(TTFont(dv).getBestCmap()) if dv else set()

    in_primary, in_a, in_b, in_dv, nobody = set(), set(), set(), set(), set()
    for c in chars:
        cp = ord(c)
        if cp in prim:
            in_primary.add(c)
        elif 'A' in cmaps and cp in cmaps['A']:
            in_a.add(c)
        elif 'B' in cmaps and cp in cmaps['B']:
            in_b.add(c)
        elif cp in dv_cmap:
            in_dv.add(c)
        else:
            nobody.add(c)
    return in_primary, in_a, in_b, in_dv, nobody
