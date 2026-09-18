/* 網站互動：字體大小、自動展開、放大鏡。冇用任何 framework。 */
(function () {
  'use strict';

  var SIZES = ['17px', '20px', '24px', '28px'];
  var KEY = 'zika-fs';

  /* ── 字體大小 ── */
  function current() {
    try { return Math.min(SIZES.length - 1, Math.max(0, +localStorage.getItem(KEY) || 0)); }
    catch (e) { return 0; }        // 無痕模式會掟錯，當預設處理
  }
  function apply(i) {
    document.documentElement.style.setProperty('--fs-base', SIZES[i]);
    var b = document.querySelectorAll('.fs-ctl .btn');
    if (b[0]) b[0].setAttribute('aria-disabled', i === 0);
    if (b[1]) b[1].setAttribute('aria-disabled', i === SIZES.length - 1);
  }
  function bump(d) {
    var i = Math.min(SIZES.length - 1, Math.max(0, current() + d));
    try { localStorage.setItem(KEY, i); } catch (e) {}
    apply(i);
  }

  /* ── 連結去到摺埋咗嘅章節，要幫佢打開 ── */
  function openTo(hash) {
    if (!hash || hash.length < 2) return;
    var el;
    try { el = document.getElementById(decodeURIComponent(hash.slice(1))); }
    catch (e) { return; }
    if (!el) return;
    var p = el.parentElement;
    while (p) {
      if (p.tagName === 'DETAILS') p.open = true;
      p = p.parentElement;
    }
    setTimeout(function () { el.scrollIntoView({ block: 'start' }); }, 30);
  }

  /* ── 放大鏡 ── */
  function lightbox(node) {
    var dlg = document.getElementById('lb');
    if (!dlg || !dlg.showModal) return;
    var body = dlg.querySelector('.lb-body');
    body.innerHTML = '';
    body.appendChild(node.cloneNode(true));
    var img = body.querySelector('img');
    if (img) { img.style.maxHeight = 'none'; img.style.height = 'auto'; img.style.cursor = 'auto'; }
    var svg = body.querySelector('svg');
    if (svg) { svg.removeAttribute('width'); svg.removeAttribute('height'); svg.style.width = '100%'; }
    dlg.showModal();
  }

  document.addEventListener('DOMContentLoaded', function () {
    apply(current());

    var ctl = document.querySelector('.fs-ctl');
    if (ctl) ctl.addEventListener('click', function (e) {
      var b = e.target.closest('.btn');
      if (b) bump(b.dataset.step === '+' ? 1 : -1);
    });

    document.addEventListener('click', function (e) {
      var a = e.target.closest('a[href^="#"]');
      if (a) { setTimeout(function () { openTo(a.getAttribute('href')); }, 0); return; }
      var z = e.target.closest('.strip img, td img, .net svg');
      if (z) { e.preventDefault(); lightbox(z); }
    });

    window.addEventListener('hashchange', function () { openTo(location.hash); });
    if (location.hash) openTo(location.hash);

    var close = document.querySelector('#lb .lb-close');
    if (close) close.addEventListener('click', function () { document.getElementById('lb').close(); });
  });
})();
