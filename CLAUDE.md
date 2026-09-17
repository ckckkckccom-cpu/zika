# 漢字多維解構 — 字卡 project

## 呢個 project 做緊咩

將一隻中文字用**幾種唔同方式**解構，交叉核對之後，俾用戶自己攞去做術數層
（斗數十二宮／地支，例如 豕＝豬→亥）。

**分工要守死：**

| 邊個做 | 做咩 |
|---|---|
| **Claude（你）** | 搵文獻、解構字形結構、粵音同音字引申、三者 cross-check |
| **用戶** | 術數層推理。**你唔好做，唔好猜，唔好喺卡入面寫斗數／五行／八字嘅嘢。** |

你嘅工作係令部件、讀音、意思變成用戶可以直接攞去用嘅「鈎」。

## 語言

**全部用廣東話同用戶溝通**，書面語夾口語（即係「嘅」「係」「咗」「喺」咁）。
字卡內容都係廣東話。專有名詞、古籍引文保持原文。

## 做緊邊啲字

中國最常用名字嘅 **28 隻獨立字**（來源：`三地中文名字排行統計.xlsx`）：

> 張 偉 王 李 娜 芳 靜 敏 劉 秀 英 桂 蘭 玉 婷 建 華 梅 珍 海 燕 杰 麗 勇 濤 艷 軍 強

已完成：**家**（v1）、**豪**（v1）、**偉**（v2）、**靜**（v2）、**娜**（v2）。家同豪係台灣榜，唔計入 28。

> 用戶可以指定某一張卡用**中文現代書面語**寫（例如「靜」）。冇特別講就照默認用廣東話。

每次做 5–6 隻，唔好一次過做晒。

## 字卡格式 v2（照跟，唔好自己改）

睇 `偉.md` 做標準樣板。章節同標題層級要**一模一樣**：

```
## 0. 基本資料      （表：部首、筆畫、Unicode、倉頡、粵音全部讀音、國音、中古音、上古音、異體字）
## 1. 結構層
   1.1 字形演變（甲骨→金文→大篆→小篆→楷書，每格圖 + 【觀察】）
   1.2 六書歸類（說文原文 → 各家講法 → 結論）
   1.3 部件分解（位置／部件／Unicode／獨立時係咩字／角色）
   1.4 部件橫向連結（呢個部件去咗邊啲字）
   1.5 異體字
   1.6 部件總表（層級／部件／字典義／粵音／出處，**拆到獨體象形為止**）
## 2. 意思層
   2.1 成隻字查字典（逐本列）
   2.2 部件逐個查字典
   2.3 結構 → 意思推導鏈
## 3. 同音層（粵音）
   3.1 同音同調字表（分 A 組同源／B 組純諧音）
   3.2 同音異調字（只列名，唔引申）
   3.3 引申
## 4. 交叉核對
   4.1 結構 ↔ 意思    4.2 字典 ↔ 字典    4.3 同音 ↔ 結構    4.4 一句總結
## 5. 來源清單
## 6. 存疑／未驗證
```

### 四個標記 — 呢個係成個 project 嘅命脈

| 標記 | 意思 |
|---|---|
| `【原文】` | 字典／古籍**原文照抄**，一個字都唔可以改 |
| `【觀察】` | **你親眼 Read 過字形圖**之後寫嘅。冇睇過圖就唔准用呢個標記 |
| `【分歧】` | 各家講法不一 —— **全部並列，唔好揀一個當定論** |
| `【引申】` | 同音推想，**唔係考據** |

**最大嘅風險係將聯想當考據。** 寫得似層層有道理唔等於有證據。每一句都要交代係邊一級。

### 3.1 同音字關係，只准四選一

1. **同源**（共用聲符）— 最實
2. **通假／聲訓**（文獻有記）
3. **民俗諧音**（有出處，例如 桂→貴 吉祥圖案）
4. **純諧音**（淨係讀音撞）— 最鬆

## 已驗證嘅來源（照用，唔好自己搵過）

| 用途 | 網址 | 注意 |
|---|---|---|
| 粵音全部讀音 + 同音字 | `humanum.arts.cuhk.edu.hk/Lexis/lexi-can/search.php?q=<Big5>` | **Big5 編碼**，要 `iconv -f big5 -t utf8` |
| 同音字全表 | `.../lexi-can/pho-rel.php?s1=<聲母>&s2=<韻母>&s3=<聲調>` | |
| 字形演變、部件、略說 | `humanum.arts.cuhk.edu.hk/Lexis/lexi-mf/search.php?word=<字>` | UTF-8，直接 curl |
| 說文原文、六書、上古音、同聲符系列 | `zh.wiktionary.org/wiki/<字>` | 有鄭張尚芳上古音表，好有用 |
| 義項、詞例 | `dict.revised.moe.edu.tw` | **釋義收喺 `<meta name="Description">` 入面**，睇下面 |
| 異體字 | `dict.variants.moe.edu.tw/search.jsp?QTP=0&WORD=<字>` | dictView 嘅 ID 成日唔啱，會 404 |
| 古文字圖 | `commons.wikimedia.org/wiki/Special:FilePath/<字>-oracle.svg?width=400` | 要 `curl -L`（會 302）；`-bronze` `-bigseal` `-seal` |

### 教育部重編國語辭典 — 兩個坑

1. **釋義唔喺 HTML body，喺 `<meta name="Description">`**。用 `moedict.py`（如果 repo 有）或者照抄佢個做法。
2. **dictView.jsp 會限速** — 回 HTTP 200 但 **0 bytes**。要 session cookie + referer + User-Agent + 重試。
   **唔好將失敗嘅檔存落 cache**，否則之後永遠唔會重試。

### 用唔到嘅（唔好再試）

zdic.net、ctext.org、小學堂

## 硬規矩

1. **【觀察】一定要真係 Read 過張圖。** 唔准靠文字描述推，唔准靠記憶作。
   呢個係用戶明確要求，亦係成個 project 最有價值嘅部分。
2. **每個判斷後面要註來源。**
3. **學界有分歧就全部並列**，唔好揀一個當定論。
4. **每張卡最尾要有「存疑／未驗證」**，老實列明邊啲係二手轉述、邊啲未親眼證實。
5. **唔准掂術數層。**

## 砌 PDF／網頁

```bash
python check_glyphs.py     # 先檢查每隻字都有字型畫得出
python make_pdf_font.py    # 整 PDF 專用字型（加咗新字要重跑）
fc-cache -f ~/.local/share/fonts
python build_demo.py       # 出 HTML（可以跟字名，例如 build_demo.py 偉 家）
                           #   合訂本 → DEMO.html、site/index.html
                           #   每隻字 → site/cards/<字>.html
python build_pdf.py 字卡.pdf          # 合訂本 PDF
python build_pdf.py --each pdf        # 每隻字一份 → pdf/<字>.pdf
python check_pdf.py 字卡.pdf pdf/*.pdf  # 驗證每份 PDF 真係有中文
```

**兩種 PDF 都要出**：`字卡.pdf` 係合訂本，`pdf/<字>.pdf` 係每隻字一份（方便單獨睇、
打印、send 俾人）。兩樣都 commit 入 repo，GitHub Actions 會自動更新。
刪咗一張卡之後，CI 會 `rm -rf pdf` 再砌返，唔會留低孤兒 PDF。

要裝一次：`sudo apt-get install -y fonts-hanazono`（罕見字用）

Push 上 main 之後 GitHub Actions 會自動做晒呢幾步，出去 GitHub Pages。

### 四個已知字型坑（已經解決，唔好再踩）

0. **NotoSansTC 係「繁體常用字」子集，唔覆蓋 CJK 擴展區。** 說文引文入面嘅古字
   （㣇 U+38C7、𩫚 U+29ADA、𩫕 U+29AD5…）同 IPA 上古音符號（ɢ ʷ ɯ ʔ ə）佢都冇 →
   變豆腐格，而且**唔會報錯**。
   解法：HanaMinA（擴展 A）+ HanaMinB（擴展 B）做 fallback，`fontkit.py` 處理。
   **呢啲罕見字係【原文】引文嘅一部分，絕對唔可以用常見字代替** —— 咁做等於改古籍原文。
   每次加新字卡之後跑 `python3 check_glyphs.py`，佢會列出邊隻字冇字型畫得到。


1. **Chromium 出 PDF 唔食 CFF/OTF 字型** → 中文全部消失，但 PDF 照出，睇落正常。
   解法：`make_pdf_font.py` 轉做 TrueType。`check_pdf.py` 係安全網。
2. **`<code>` 預設用 monospace，monospace 冇 CJK** → `【原文】` 呢類標記變豆腐格。
   解法：CSS 明確指定 `code,pre{font-family:...}`。
3. **NotoSansTC 係純 CJK 字型，冇 `✓ ✗ ○` 呢啲符號** → 用 `*{font-family:...!important}`
   會殺埋 fallback，符號變豆腐。解法：fallback stack 留 `'DejaVu Sans'`。
   **唔好用 emoji（✅❌），兩個字型都冇。**

## 老規則（用戶定嘅）

每個回覆收尾要寫：**下一步係咩 ｜ 建議 model ｜ effort ｜ 理由**，然後**停低**等用戶轉 model
先開始執行。Plan 批准咗都要停。
