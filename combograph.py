#!/usr/bin/env python3
"""組合圖：一隻組合字擺喺兩條軸嘅交叉點上。

點解要獨立一幅圖：一隻形聲字唔係「兩嚿嘢黐埋」咁簡單，佢同時屬於兩個家族——

  橫軸　同一個形符，換聲符 → 貝+才=財、貝+化=貨、貝+有=賄、貝+次=資
  縱軸　同一個聲符，換形符 → 貝+才=財、木+才=材、豸+才=豺

兩條軸嘅**長度差異**本身就係資料：「貝」係極能產嘅形符，「才」係弱聲符。
呢啲嘢淨係拆開兩邊講係睇唔出嚟嘅，一定要畫出嚟先至一眼睇到。

點解出 HTML 唔出 SVG：呢個係一個矩陣，五格橫排喺手機一定要碌左右。
SVG 係固定版面，縮到啱手機嘅話啲小字會細到睇唔到（實測 15px 縮到 8px）。
改用會自動摺行嘅 HTML：手機兩欄、電腦一行過，兩邊都唔使碌。
而且目標字喺兩條軸各出現一次，「佢同時屬於兩個家族」呢點反而講得更清楚。
"""
import sys

import cardfmt

C_SELF = ('#fff7ed', '#c2410c')      # 目標字
C_FORM = ('#eff6ff', '#1d4ed8')      # 同形符
C_SOUND = ('#ecfdf5', '#047857')     # 同聲符


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def _cell(ch, make, gloss, kind, self_=False):
    return ('<div class="cc cc-%s%s"><span class="cc-ch">%s</span>'
            '<span class="cc-mk">%s</span><span class="cc-gl">%s</span></div>'
            % (kind, ' cc-self' if self_ else '', esc(ch), esc(make), esc(gloss)))


def _axis(title, cells, kind):
    return ('<div class="cax cax-%s"><div class="cax-t">%s</div>'
            '<div class="cax-r">%s</div></div>' % (kind, esc(title), ''.join(cells)))


def render_family_html(card):
    """一張卡 → 組合圖 HTML。冇 combo 資料就回 None。"""
    cb = (card.meta or {}).get('combo')
    if not cb or cb.get('layout') == '獨體':
        return None
    form = cb.get('form') or {}
    sound = cb.get('sound') or {}
    fp, sp = form.get('part', ''), sound.get('part', '')
    self_mk = '%s＋%s' % (fp, sp)

    row = [_cell(card.ch, self_mk, cb.get('gloss', ''), 'form', True)]
    for r in (cb.get('same_form') or []):
        if isinstance(r, dict):
            row.append(_cell(r.get('char', ''), '%s＋%s' % (fp, r.get('with', '')),
                             r.get('gloss', ''), 'form'))
    col = [_cell(card.ch, self_mk, cb.get('gloss', ''), 'sound', True)]
    for r in (cb.get('same_sound') or []):
        if isinstance(r, dict):
            col.append(_cell(r.get('char', ''), '%s＋%s' % (r.get('with', ''), sp),
                             r.get('gloss', ''), 'sound'))

    out = ['<div class="combo">']
    out.append(_axis('同形符「%s」，換聲符' % fp, row, 'form'))
    out.append(_axis('同聲符「%s」，換形符' % sp, col, 'sound'))
    if cb.get('note'):
        out.append('<p class="cnote">%s</p>' % esc(cb['note']))
    out.append('</div>')
    return ''.join(out)


def main():
    import os
    root = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) < 2:
        sys.exit('用法：python3 combograph.py <字>')
    card = cardfmt.parse_card(os.path.join(root, sys.argv[1] + '.md'))
    html = render_family_html(card)
    if not html:
        sys.exit('%s 冇 combo 資料' % sys.argv[1])
    sys.stdout.write(html + '\n')


if __name__ == '__main__':
    main()


def render_downstream_html(card):
    """呢隻字自己做部件嗰陣，去咗邊啲字。

    同 1.7 啱啱相反方向：1.7 問「佢企喺邊個家族」，呢度問「佢生出咗啲乜」。
    一個字可以由極能產嘅部件造出嚟，自己卻係一個終點（例：財）。
    呢個落差淨係睇成隻字係睇唔到嘅，要數過先知。
    """
    cb = (card.meta or {}).get('combo') or {}
    ds = cb.get('downstream')
    if not ds:
        return None
    items = [r for r in (ds.get('items') or []) if isinstance(r, dict)]
    out = ['<div class="combo">']
    n = ds.get('count', len(items))
    title = '「%s」做部件，進入了 %s 個字' % (card.ch, n)
    if not items:
        out.append('<div class="cax cax-down"><div class="cax-t">%s</div></div>'
                   % esc(title))
    else:
        cells = [_cell(r.get('char', ''), '%s＋%s' % (r.get('with', ''), card.ch),
                       r.get('gloss', ''), 'down') for r in items]
        out.append(_axis(title, cells, 'down'))
    if ds.get('note'):
        out.append('<p class="cnote">%s</p>' % esc(ds['note']))
    out.append('</div>')
    return ''.join(out)
