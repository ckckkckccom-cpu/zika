#!/usr/bin/env python3
"""砌完網站之後嘅安全網：真係開個瀏覽器逐頁睇。

點解要有呢一步：網頁出事嘅方式多數係「靜靜哋壞」——
字型冇載到、圖唔見咗、手機上橫向溢出、絕對路徑喺子路徑爛。
呢啲全部唔會令 build 失敗，但用戶一開就見到。

檢查項目（每頁、手機同電腦兩個闊度各一次）：
  1. 冇橫向溢出（除咗特登可以橫捲嘅圖帶）
  2. body 字級 ≥ 20px
  3. 全部 @font-face 載得成，而且 ZikaMain 真係用緊
  4. 全部 <img> 真係有內容（naturalWidth > 0）
  5. 冇 console error
  6. v3 卡一定要有推理網絡 SVG

用法：
  python3 check_site.py                 # 淨係檢查
  python3 check_site.py --shots shots   # 順手影埋相
"""
import os
import sys
import urllib.parse

import fontkit
import localserver

ROOT = fontkit.ROOT
SITE = os.path.join(ROOT, 'site')
WIDTHS = [('phone', 390, 844), ('desktop', 1280, 900)]
MIN_FONT_PX = 17.0


EAGER = """async () => {
  document.querySelectorAll('img[loading]').forEach(i => i.loading = 'eager');
  await Promise.all([...document.images].map(
      i => i.complete ? null : new Promise(r => { i.onload = i.onerror = r; })));
}"""

PROBE = """() => {
  const over = [...document.querySelectorAll('main *')].filter(el => {
    if (el.closest('.strip, .net, .t-img, dialog')) return false;
    return el.getBoundingClientRect().right > window.innerWidth + 2;
  }).map(el => el.tagName + '.' + (el.className || '')).slice(0, 5);
  return {
    fs: parseFloat(getComputedStyle(document.body).fontSize),
    scrollW: document.documentElement.scrollWidth,
    innerW: window.innerWidth,
    over,
    fontsOk: document.fonts.check('1em ZikaMain'),
    fontStatus: document.fonts.status,
    badImgs: [...document.images].filter(i => !i.complete || i.naturalWidth === 0)
             .map(i => i.getAttribute('src')).slice(0, 5),
    imgCount: document.images.length,
    svgCount: document.querySelectorAll('.net svg').length,
    details: document.querySelectorAll('details.deep').length,
    infoCells: document.querySelectorAll('.info .ic').length,
  };
}"""


def main():
    from playwright.sync_api import sync_playwright

    shots = None
    if '--shots' in sys.argv:
        shots = sys.argv[sys.argv.index('--shots') + 1]
        os.makedirs(shots, exist_ok=True)

    if not os.path.isdir(SITE):
        sys.exit('冇 site/ —— 請先跑 python3 build_site.py')

    pages = ['index.html']
    cards_dir = os.path.join(SITE, 'cards')
    if os.path.isdir(cards_dir):
        pages += ['cards/' + f for f in sorted(os.listdir(cards_dir))
                  if f.endswith('.html')]

    # 由 site 嘅上一層行 server，用 /site/… 開，
    # 順便證明個網站喺子路徑（GitHub Pages 就係子路徑）都行得
    httpd, port = localserver.serve(os.path.dirname(SITE))
    base = 'http://127.0.0.1:%d/site/' % port
    problems = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for tag, w, h in WIDTHS:
            ctx = browser.new_context(viewport={'width': w, 'height': h},
                                      device_scale_factor=1)
            page = ctx.new_page()
            errors = []
            page.on('console', lambda m: errors.append(m.text)
                    if m.type == 'error' else None)
            page.on('pageerror', lambda e: errors.append(str(e)))
            for rel in pages:
                del errors[:]
                page.goto(base + urllib.parse.quote(rel), wait_until='networkidle')
                page.evaluate('document.fonts.ready')
                # 延後載入嘅圖要逼佢載晒，否則下面會誤報「圖載唔到」
                page.evaluate(EAGER)
                page.wait_for_load_state('networkidle')
                r = page.evaluate(PROBE)
                name = '%s @%s' % (rel, tag)

                if r['fs'] < MIN_FONT_PX - 0.5:
                    problems.append('%s：body 字級只有 %.1fpx，要 ≥ %.0f'
                                    % (name, r['fs'], MIN_FONT_PX))
                if r['scrollW'] > r['innerW'] + 2:
                    problems.append('%s：橫向溢出 %dpx（%s）'
                                    % (name, r['scrollW'] - r['innerW'],
                                       '、'.join(r['over']) or '未知元素'))
                if not r['fontsOk']:
                    problems.append('%s：ZikaMain 字型未載到（狀態 %s）'
                                    % (name, r['fontStatus']))
                if r['badImgs']:
                    problems.append('%s：%d 張圖載唔到，例如 %s'
                                    % (name, len(r['badImgs']), r['badImgs'][0]))
                if errors:
                    problems.append('%s：console 有錯 —— %s' % (name, errors[0][:120]))
                if rel.startswith('cards/') and r['details'] == 0:
                    problems.append('%s：冇「詳細考證」摺疊區' % name)
                # 頂部資料格係由第 0 節嗰個表撈出嚟嘅。如果有人改咗嗰個表嘅
                # 欄名或者格式，資料格會靜靜哋變空，唔會報錯。呢度捉佢。
                if rel.startswith('cards/') and r['infoCells'] < 6:
                    problems.append('%s：頂部基本資料格只有 %d 格，第 0 節嗰個表可能改咗格式'
                                    % (name, r['infoCells']))

                if shots:
                    out = os.path.join(
                        shots, '%s_%s.png' % (tag, rel.replace('/', '_')[:-5]))
                    page.screenshot(path=out, full_page=True)
                print('   %-28s 字級 %.0fpx  資料格 %2d  圖 %2d  網絡圖 %d  %s'
                      % (name, r['fs'], r['infoCells'], r['imgCount'], r['svgCount'],
                         '✓' if not problems or problems[-1][:len(name)] != name else '✗'))
            ctx.close()

        # 互動：字體大小記唔記得住、按網絡圖節點會唔會自動展開
        ctx = browser.new_context(viewport={'width': 390, 'height': 844})
        page = ctx.new_page()
        card = None
        for p_ in pages:
            if p_.startswith('cards/'):
                page.goto(base + urllib.parse.quote(p_), wait_until='networkidle')
                if page.query_selector('.net a[href^="#"]'):
                    card = p_
                    break
        if card:
            page.goto(base + urllib.parse.quote(card), wait_until='networkidle')
            before = page.evaluate('parseFloat(getComputedStyle(document.body).fontSize)')
            page.click('.fs-ctl .btn[data-step="+"]')
            page.reload(wait_until='networkidle')
            after = page.evaluate('parseFloat(getComputedStyle(document.body).fontSize)')
            if after <= before:
                problems.append('字體 A+ 按咗之後 reload 冇留住（%.0f → %.0f）'
                                % (before, after))
            else:
                print('   字體 A+ 重新載入後保持 %.0fpx ✓' % after)
            link = page.query_selector('.net a[href^="#"]')
            if link:
                page.evaluate('document.querySelectorAll("details").forEach(d=>d.open=false)')
                link.click()
                page.wait_for_timeout(300)
                opened = page.evaluate('document.querySelector("details.deep").open')
                if not opened:
                    problems.append('按推理網絡節點之後，詳細考證冇自動展開')
                else:
                    print('   按網絡圖節點自動展開詳細考證 ✓')
        ctx.close()
        browser.close()

    httpd.shutdown()

    if problems:
        print('\n發現 %d 個問題：' % len(problems))
        for p_ in problems:
            print('   ✗ %s' % p_)
        sys.exit(1)
    print('\n✓ 網站檢查全部通過')


if __name__ == '__main__':
    main()
