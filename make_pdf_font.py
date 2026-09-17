#!/usr/bin/env python3
"""整一個俾 PDF 用嘅 TrueType 字型。

點解要呢步：Chromium 嘅 page.pdf() 行 Skia PDF backend，佢嵌入 CFF/OTF
（PostScript 輪廓）字型會靜靜哋失敗 —— 出嚟嘅 PDF 中文全部唔見（實測 CJK 字數 = 0）。
螢幕截圖路徑冇呢個問題，所以只影響 PDF。

解法：subset → CFF 輪廓轉 TrueType（二次貝茲）→ 裝落 ~/.local/share/fonts。
"""
import os
import sys

from fontTools import subset
from fontTools.ttLib import TTFont, newTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'fonts', 'NotoSansTC-Regular.otf')
DEST_DIR = os.path.expanduser('~/.local/share/fonts')
MAX_ERR = 1.0          # 轉換容差（units/em），1.0 肉眼睇唔出分別


def used_text():
    """收集所有字卡用到嘅字元。"""
    import fontkit
    return fontkit.cards_text(ROOT)


def otf_to_ttf(font, max_err=MAX_ERR):
    """CFF 三次貝茲 → glyf 二次貝茲。"""
    glyph_order = font.getGlyphOrder()
    glyph_set = font.getGlyphSet()
    glyf = newTable('glyf')
    glyf.glyphOrder = glyph_order
    glyf.glyphs = {}

    for name in glyph_order:
        pen = TTGlyphPen(glyph_set)
        glyph_set[name].draw(Cu2QuPen(pen, max_err, reverse_direction=True))
        g = pen.glyph()
        g.recalcBounds(glyf)      # CFF 冇 xMin/yMin，唔算就 compile 唔到
        glyf[name] = g

    font['glyf'] = glyf
    font['loca'] = newTable('loca')
    font['maxp'] = maxp = newTable('maxp')
    maxp.tableVersion = 0x00010000
    maxp.maxZones = 1
    for a in ('maxTwilightPoints', 'maxStorage', 'maxFunctionDefs',
              'maxInstructionDefs', 'maxStackElements',
              'maxSizeOfInstructions', 'maxComponentElements'):
        setattr(maxp, a, 0)
    maxp.recalc(font)             # maxPoints/maxContours 等要由 glyf 算返出嚟
    font['head'].glyphDataFormat = 0
    font['head'].indexToLocFormat = 0
    del font['CFF ']
    for t in ('VORG', 'BASE'):
        if t in font:
            del font[t]
    font.sfntVersion = '\x00\x01\x00\x00'
    return font


def main():
    text = used_text()
    print('用到嘅字元: %d 個（去重後 %d）' % (len(text), len(set(text))))

    opts = subset.Options()
    opts.drop_tables += ['BASE', 'JSTF', 'DSIG']
    opts.notdef_outline = True
    font = subset.load_font(SRC, opts)
    s = subset.Subsetter(options=opts)
    s.populate(text=text)
    s.subset(font)
    print('subset 後 glyphs: %d' % len(font.getGlyphOrder()))

    print('CFF → TrueType 轉換中…')
    font = otf_to_ttf(font)

    # 改名，避免同原本 OTF 撞 family 令 fontconfig 揀錯
    name_tbl = font['name']
    for rec in name_tbl.names:
        if rec.nameID in (1, 3, 4, 6):
            v = rec.toUnicode().replace('Noto Sans TC', 'NotoSansTC')
            rec.string = v.replace('NotoSansTC', 'NotoSansTCPdf')

    os.makedirs(DEST_DIR, exist_ok=True)
    out = os.path.join(DEST_DIR, 'NotoSansTCPdf-Regular.ttf')
    font.save(out)
    print('出咗: %s (%.2f MB)' % (out, os.path.getsize(out) / 1e6))

    chk = TTFont(out)
    print('驗證 — 輪廓格式:', 'glyf ✓' if 'glyf' in chk else 'CFF ✗')
    cmap = chk.getBestCmap()
    miss = [c for c in '偉韋家豪豕盛符聲觀察原文引申' if ord(c) not in cmap]
    print('驗證 — 關鍵字:', '全部有 ✓' if not miss else '缺 %s ✗' % miss)

    # 罕見字（㣇 𩫚 IPA 音標…）NotoSansTC 冇，要 HanaMin 補。
    # HanaMin 本身已經係 TrueType，唔使轉輪廓，subset 完直接裝。
    import fontkit
    _, in_a, in_b, nobody = fontkit.coverage(text)
    hana = fontkit.find_hanamin()
    for letter, chars in (('A', in_a), ('B', in_b)):
        if not chars:
            continue
        if letter not in hana:
            print('⚠ 冇 HanaMin%s，%d 個罕見字會變豆腐格' % (letter, len(chars)))
            continue
        o2 = subset.Options()
        o2.drop_tables += ['BASE', 'JSTF', 'DSIG']
        o2.ignore_missing_glyphs = True
        hf = subset.load_font(hana[letter], o2)
        hs = subset.Subsetter(options=o2)
        hs.populate(text=''.join(chars))
        hs.subset(hf)
        dest = os.path.join(DEST_DIR, 'ZikaRare%s-Regular.ttf' % letter)
        for rec in hf['name'].names:
            if rec.nameID in (1, 3, 4, 6):
                rec.string = 'ZikaRare%s' % letter
        hf.save(dest)
        print('出咗: %s (%d 個罕見字)' % (dest, len(chars)))

    if nobody:
        print('✗ 呢啲字冇任何字型畫得出: %s' % ''.join(sorted(nobody)))
        return 1
    return 0 if not miss and 'glyf' in chk else 1


if __name__ == '__main__':
    sys.exit(main())
