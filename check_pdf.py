#!/usr/bin/env python3
"""驗 PDF 真係有中文。

點解要呢個：Chromium 出 PDF 如果揀錯字型，會照出一份「睇落正常」嘅 PDF ——
頁數、圖片全部喺度，但中文一個字都冇。唔檢查就會靜靜哋出爛嘢。
呢個 script 讀 PDF 嘅 ToUnicode 表，數返有幾多個中日韓字。

用法：python3 check_pdf.py site/cards.pdf
出事會 exit code 1，令 GitHub Actions 標紅。
"""
import re
import sys
import zlib

# 呢啲字喺每張字卡都應該出現；有一個缺就當字型出事
MUST_HAVE = '結構意思層部件字典來源觀察原文'
MIN_CJK = 200


def cjk_in_pdf(path):
    data = open(path, 'rb').read()
    found = set()
    for m in re.finditer(rb'stream\r?\n', data):
        start = m.end()
        end = data.find(b'endstream', start)
        try:
            raw = zlib.decompress(data[start:end])
        except Exception:
            continue

        # ToUnicode CMap 有兩種寫法，兩種都要讀
        for blk in re.findall(rb'beginbfchar(.*?)endbfchar', raw, re.S):
            for mm in re.finditer(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', blk):
                found.update(_codepoints(mm.group(2)))
        for blk in re.findall(rb'beginbfrange(.*?)endbfrange', raw, re.S):
            for mm in re.finditer(
                    rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', blk):
                lo, hi = int(mm.group(1), 16), int(mm.group(2), 16)
                dst = int(mm.group(3).decode()[:4], 16)
                found.update(dst + k for k in range(hi - lo + 1))
    return {c for c in found if 0x3000 <= c <= 0x9FFF}, len(data)


def _codepoints(hexbytes):
    u = hexbytes.decode()
    return [int(u[i:i + 4], 16) for i in range(0, len(u), 4)]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'site/cards.pdf'
    cjk, size = cjk_in_pdf(path)
    print('%s — %.2f MB，中文字數 %d' % (path, size / 1e6, len(cjk)))

    problems = []
    if len(cjk) < MIN_CJK:
        problems.append('中文字數得 %d 個（應該最少 %d）—— 字型好可能冇嵌入'
                        % (len(cjk), MIN_CJK))
    missing = [c for c in MUST_HAVE if ord(c) not in cjk]
    if missing:
        problems.append('缺咗呢啲常用字：%s' % ''.join(missing))

    if problems:
        print('\n✗ PDF 有問題：')
        for p in problems:
            print('  -', p)
        print('\n多數係字型問題。睇 make_pdf_font.py 開頭嘅解釋。')
        return 1

    print('✓ PDF 正常')
    return 0


if __name__ == '__main__':
    sys.exit(main())
