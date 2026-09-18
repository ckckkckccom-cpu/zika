#!/usr/bin/env python3
"""全站介面文字的單一來源。

點解要集中喺一個檔：字型係 subset 出嚟嘅，只包含「實際用到嘅字」。
網頁介面用到但唔喺任何字卡入面嘅字（例如「上一字」「放大字體」），
如果唔加入 subset 範圍，就會變豆腐格，而且唔會報錯。

fontkit.cards_text() 會附加呢度嘅 ALL_TEXT，
所以 check_glyphs.py、make_pdf_font.py、build_site.py 三邊自動同步。
改介面文字之後唔使做其他嘢，重新 build 就得。
"""

# ── 導覽 ──
NAV_HOME = '首頁'
NAV_PREV = '上一字'
NAV_NEXT = '下一字'
NAV_TOP = '返回頂部'

# ── 字體大小控制 ──
FS_SMALLER = 'A−'
FS_LARGER = 'A+'
FS_LABEL = '字體大小'

# ── 網站標題 ──
SITE_TITLE = '漢字多維解構'
SITE_SUB = '一隻字，幾種拆法，交叉核對'

# ── 版面區塊 ──
SEC_OVERVIEW = '總覽'
SEC_DETAIL = '詳細考證'
SEC_DETAIL_HINT = '展開全部原始資料：字典原文、字形分析、同音字表、來源清單、存疑事項'
SEC_EVOLUTION = '字形演變'
SEC_NETWORK = '推理網絡'
SEC_HOWTO = '如何閱讀'
SEC_LEGEND = '四個標記'
SEC_CARDS = '字卡一覽'
SEC_PDF = '下載 PDF'

# ── 四個標記的解釋（首頁圖例用）──
MARKS = [
    ('原文', '字典或古籍原文照抄，一個字都沒有改動。最可靠。'),
    ('觀察', '作者親眼看過字形圖之後寫的判斷。'),
    ('分歧', '各家講法不一致，全部並列，不替讀者決定誰對。'),
    ('引申', '由讀音推想出來的聯想，不是考據。最寬鬆。'),
]

# ── 推理網絡圖例 ──
NET_LEGEND_TITLE = '線的粗細代表證據強弱'
LAYER_NAMES = ['部件', '字', '意思', '同音', '結論']

# ── 首頁文案 ──
HOWTO_STEPS = [
    '每隻字先看最上面那幅圖：由部件出發，一路推到結論。',
    '線的樣式代表證據有多硬。實線是文獻原文，虛線是各家分歧，點線只是讀音聯想。',
    '圖下面四格是重點摘要，每格三至六點。',
    '想看完整資料，按最底的「詳細考證」展開。',
]
PDF_NOTE = '每隻字一份，另有合訂本。方便列印或傳送。'
PDF_ALL = '合訂本（全部字）'
ADD_HOME_TITLE = '加到手機主畫面'
ADD_HOME_IOS = 'iPhone：在 Safari 按底部分享鍵，選「加至主畫面」。'
ADD_HOME_AND = 'Android：在 Chrome 按右上角選單，選「加至主畫面」。'

# ── 其他 ──
JYUTPING_LABEL = '粵音'
VERDICT_LABEL = '一句總結'
NO_CARDS = '暫時未有字卡'
UPDATED = '最後更新'
BACK_TO_INDEX = '返回首頁'
IMG_HINT = '按圖可放大'
FMT_LEGACY = '此卡仍是舊格式，未有推理網絡圖。'

# 額外字元：數字、常見標點、部件層名、書體名
_EXTRA_CHARS = (
    '0123456789'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    '一二三四五六七八九十百千'
    '／・：；，。、（）「」『』《》〈〉？！…—－·％＋'
    '甲骨文金大篆小楷書簡帛汗古異體摹拓本'
    '第節頁張隻個共至年月日'
)


def _collect():
    """把呢個 module 入面所有字串砌埋一齊，交俾字型 subset。"""
    out = [_EXTRA_CHARS]
    for name, val in sorted(globals().items()):
        if name.startswith('_'):
            continue
        if isinstance(val, str):
            out.append(val)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str):
                    out.append(item)
                elif isinstance(item, (tuple, list)):
                    out += [x for x in item if isinstance(x, str)]
    return ''.join(out)


ALL_TEXT = _collect()

if __name__ == '__main__':
    print('介面文字共 %d 個不同字元' % len(set(ALL_TEXT)))
