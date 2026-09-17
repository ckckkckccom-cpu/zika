#!/usr/bin/env python3
"""檢查每隻字卡用到嘅字，係咪全部有字型畫得出。

點解要呢個：字型冇某隻字，HTML 同 PDF 都會出現「豆腐格」（⊠），但唔會報錯 ——
我哋就係咁樣漏咗「豪」卡入面嘅「㣇」「𩫚」，出咗份 PDF 先俾用戶發現。

用法：python3 check_glyphs.py
有字冇字型畫得出 → exit code 1（GitHub Actions 會標紅）。
"""
import sys
import unicodedata

import fontkit


def main():
    text = fontkit.cards_text()
    hana = fontkit.find_hanamin()
    prim, in_a, in_b, in_dv, nobody = fontkit.coverage(text)

    print('字卡總字元數（去重）: %d'
          % (len(prim) + len(in_a) + len(in_b) + len(in_dv) + len(nobody)))
    print('  NotoSansTC 畫到 : %d' % len(prim))
    print('  HanaMinA 補     : %d  %s' % (len(in_a), ''.join(sorted(in_a))[:40]))
    print('  HanaMinB 補     : %d  %s' % (len(in_b), ''.join(sorted(in_b))[:40]))
    print('  DejaVu Sans 補  : %d  %s' % (len(in_dv), ''.join(sorted(in_dv))[:40]))

    if not fontkit.find_dejavu():
        print('\n⚠ 搵唔到 DejaVu Sans。')
        print('  Ubuntu／Debian： sudo apt-get install -y fonts-dejavu-core')
        print('  冇佢 ✓ ✗ 同 IPA 附加符號會變豆腐格。')

    if not hana:
        print('\n⚠ 搵唔到 HanaMinA/HanaMinB。')
        print('  Ubuntu／Debian： sudo apt-get install -y fonts-hanazono')
        print('  冇佢罕見字會變豆腐格。')

    if nobody:
        print('\n✗ 呢啲字冇任何字型畫得出，會變豆腐格：')
        for c in sorted(nobody):
            try:
                name = unicodedata.name(c)
            except ValueError:
                name = '(無名)'
            print('   %r  U+%05X  %s' % (c, ord(c), name))
        print('\n呢啲多數係【原文】引文入面嘅古字 —— **唔好用常見字代替**，')
        print('咁做等於改古籍原文。要搵覆蓋得到嘅字型。')
        return 1

    print('\n✓ 全部字都畫得出')
    return 0


if __name__ == '__main__':
    sys.exit(main())
