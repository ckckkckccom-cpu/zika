# 由 0 開始：將字卡搬上雲端

**目標**：電腦完全不用開，用手機就可以（一）叫 Claude 做新字卡、（二）隨時看到最新的
**網站**和 PDF，（三）把一條網址傳給師傅，他按一下就看得到。

做一次就搞定。全程約 **35 分鐘**。

> 第 1 至 5 部分是原本的設定（放上 GitHub、自動砌 PDF、在手機叫 Claude 開工）。
> **第 6 部分是新加的：開網站。** 已經做過前五部分的話，直接跳去第 6 部分。

---

## 睇之前：幾個字眼

唔使背，見到嗰陣返嚟查就得。

| 個字 | 即係咩 |
|---|---|
| **repository**（簡稱 **repo**） | 一個資料夾，放住成個 project 嘅檔案。中文有時叫「倉庫」 |
| **Private** | 私人。淨係你自己登入咗先睇到 |
| **Public** | 公開。全世界都睇到 |
| **commit** | 儲存一次改動。同「另存新檔」似，但佢會記住每一次，可以回帶 |
| **push** | 將電腦度嘅改動，送上 GitHub |
| **Actions** | GitHub 幫你自動做嘢嘅功能。我哋用佢自動砌 PDF |
| **token** | 一條好長嘅字串，代替密碼用 |

## 你要準備

- 你個 GitHub 戶口（已經有）
- 你部電腦 —— **淨係第 2 部分用一次**，之後永遠唔使再開
- Claude **Pro** 或 **Max** 月費計劃 —— 第 5 部分要用（免費版冇雲端功能）

## 個設定係點運作

```
你部手機打字        →   Claude 喺雲端做新字卡   →  放上 GitHub
                                                        ↓
                                            GitHub 自動砌 PDF
                                                        ↓
                                            PDF 放返入個 repo
                                                        ↓
                            你喺手機開 GitHub 撳個 PDF 就睇到
```

PDF 會**直接放入 repo**，在 GitHub 按一下就打開得到。
另外第 6 部分會再開一個**公開網站**，網址可以直接傳給師傅，他不用登入、不用下載。

---

# 第 1 部分：開一個新 repo

⏱ 約 3 分鐘 ｜ 📱 手機或電腦都得

### 步驟

**1.** 開 **https://github.com** ，登入。

**2.** 望**右上角**，有個 **＋**（加號）。撳佢。

**3.** 彈出一個小選單，揀最上面嗰項 **New repository**。

**4.** 入到一版嘢，由上而下咁填：

| 欄位 | 點做 |
|---|---|
| **Owner** | 唔使郁（應該已經係你個 username） |
| **Repository name** | 打 `zika`<br>⚠️ 全細楷英文，冇空格。呢個係「字卡」嘅拼音 |
| **Description** | 可以唔填。想填就打 `漢字多維解構字卡` |
| **Public / Private** | 撳 **Private** 嗰個圓點 |
| **Add a README file** | ⚠️ **唔好剔** |
| **Add .gitignore** | ⚠️ 留喺 `None` |
| **Choose a license** | ⚠️ 留喺 `None` |

> 💡 **點解嗰三樣唔好剔？** 因為你部電腦度已經有齊呢啲檔案。
> 剔咗嘅話 GitHub 會自己整多份，兩邊撞，第 2 部分會出錯。

**5.** 拉到最底，撳綠色 **Create repository**。

### ✅ 做啱咗會見到

一版差唔多空白嘅嘢，中間有一段灰色嘅字，入面有一行好似咁：

```
https://github.com/你嘅username/zika.git
```

**呢行字好重要。** 撳佢右邊嗰個**複製圖示**（兩個疊埋嘅方格），copy 低佢。

📝 **貼去一個你搵返到嘅地方**（WhatsApp 俾自己、備忘錄都得）。下一步要用。

---

# 第 2 部分：將檔案送上 GitHub

⏱ 約 10 分鐘 ｜ 💻 **呢部分要用電腦**（一次過，之後唔使）

檔案而家喺你部電腦嘅 `/home/user25/字卡` 入面，要送上去。

## 2A. 攞一條 token（通行證）

GitHub 唔收密碼，要用一條叫 token 嘅長字串。

**1.** 開呢個網址（直接開，唔使自己搵）：

```
https://github.com/settings/tokens?type=beta
```

**2.** 撳 **Generate new token**（綠色掣，喺右上）。

**3.** 一版表格，由上而下：

| 欄位 | 點做 |
|---|---|
| **Token name** | 打 `zika-upload` |
| **Resource owner** | 唔使郁 |
| **Expiration** | 撳開個選單，揀 **90 days** |
| **Description** | 唔使填 |

**4.** 再落少少，見到 **Repository access**，有三個圓點。撳**中間**嗰個：

> ◉ **Only select repositories**

撳咗之後下面會多咗個 **Select repositories** 掣 → 撳佢 → 喺清單搵 **zika** → 撳佢。

**5.** 再落，見到 **Permissions**，下面有個 **Repository permissions**，撳佢個三角形展開。

**6.** 會出一條好長嘅清單（Actions、Administration、Checks…）。
**只需要搵一行：Contents**。

搵到 **Contents** 之後，撳佢**右邊**嗰個選單（預設寫住 `No access`），揀 **Read and write**。

> ⚠️ 其他行全部唔好郁。

**7.** 拉到最底，撳綠色 **Generate token**。

**8.** 出一版，上面有條**綠色底嘅長字串**，`github_pat_` 開頭。

🔴 **即刻撳右邊嘅複製圖示 copy 低佢。**

- 呢條嘢**只會出現呢一次**。撳走咗個版就冇，要重新攞過。
- **當佢係密碼。** 唔好貼上網、唔好影相放social media。

## 2B. 送檔案

📝 呢一刻你手上應該有兩樣嘢：
1. 個 repo 網址 `https://github.com/你嘅username/zika.git`
2. 條 token `github_pat_xxxxx...`

返去你部電腦嘅 **Claude Code**（即係你而家同我傾緊偈嗰度），打：

> 幫我 push 上 GitHub。
> repo：https://github.com/你嘅username/zika.git
> token：github_pat_你條token

我會幫你送上去，完成之後即刻將條 token 由設定入面清走，唔會留底。

<details>
<summary>想自己打指令嘅話（撳開睇）</summary>

喺 terminal 打，記住將 `USERNAME` 同 `TOKEN` 換返做你自己嘅：

```bash
cd /home/user25/字卡
git remote add origin https://USERNAME:TOKEN@github.com/USERNAME/zika.git
git push -u origin main
git remote set-url origin https://github.com/USERNAME/zika.git
```

最後嗰行係將條 token 由設定清走，唔好漏。
</details>

### ✅ 做啱咗會見到

開返 `https://github.com/你嘅username/zika`，會見到一堆檔案名：

```
.github          CLAUDE.md        README.md        SETUP.md
build_demo.py    build_pdf.py     check_glyphs.py  check_pdf.py
fontkit.py       fonts            img              make_pdf_font.py
requirements.txt 偉.md            家.md            豪.md
```

見到 `偉.md`、`家.md`、`豪.md` 就啱晒。

---

# 第 3 部分：開自動砌 PDF

⏱ 約 5 分鐘 ｜ 📱 手機或電腦都得

由呢一刻起，每次有新字卡，GitHub 會**自己**砌好個 PDF。

**1.** 喺你個 repo 版面，望**上面**一行掣：

```
Code   Issues   Pull requests   Actions   Projects   Wiki   Security   Insights   Settings
```

撳 **Actions**。

**2.** 如果佢問你批准（通常寫住 *"Workflows aren't being run..."* 或者
*"I understand my workflows, go ahead and enable them"*），撳個綠色掣批准。

**3.** 望**左邊**，有個清單，入面應該有：

> **自動砌字卡 PDF**

撳佢。

**4.** 撳咗之後，**右邊**會出一行字 *"This workflow has a workflow_dispatch event trigger."*，
旁邊有個灰色掣 **Run workflow**。撳佢。

**5.** 彈出一個細方格，入面有個 **Branch: main**，同埋一個綠色 **Run workflow** 掣。
撳嗰個綠色掣。

**6.** 等 **3 至 5 分鐘**。

拉一拉個版 refresh，會見到一行嘢，前面有個圖示：

| 圖示 | 意思 |
|---|---|
| 🟡 轉緊嘅黃色圓圈 | 做緊，等佢 |
| ✅ 綠色剔 | **成功** |
| ❌ 紅色叉 | 出咗事 |

### ✅ 做啱咗會見到

綠色剔。然後撳返上面個 **Code** 掣返去檔案清單，
會見到**多咗一個檔**：

```
字卡.pdf
```

呢個就係自動砌出嚟嘅。

### ❌ 紅色叉點算

1. 撳入去嗰行
2. 左邊會見到一連串步驟名（攞 repo 落嚟、裝 Python、砌 PDF…）
3. 搵到**紅色叉**嗰一步，撳佢
4. 右邊會出一堆字，**影相**（或者 copy 最後 20 行）
5. 拎返嚟俾我，我幫你睇

---

# 第 4 部分：喺手機睇 PDF

⏱ 約 2 分鐘 ｜ 📱 手機

## 用瀏覽器（最簡單）

**1.** 手機開 Safari 或 Chrome，去：

```
https://github.com/你嘅username/zika
```

（未登入嘅話登入先，因為個 repo 係 Private）

**2.** 拉落去，喺檔案清單搵 **`字卡.pdf`**，撳佢。

**3.** GitHub 會直接顯示份 PDF，可以碌可以放大。

## 想快啲？加去主畫面

**1.** 喺 `字卡.pdf` 嗰版
**2.** 撳底部**分享**掣（一個方格加向上箭嘴）
**3.** 拉落去揀 **加至主畫面**
**4.** 改個名叫「字卡」→ 撳**加入**

之後你部手機主畫面就有個「字卡」圖示，撳一下直接開最新版。

## 用 GitHub app 都得

App Store 搵 **GitHub** 裝咗佢，登入，開 `zika` → **Code** → `字卡.pdf`。

> 💡 **PDF 好似冇更新？**
> 喺瀏覽器拉個版落去 refresh。GitHub app 就熄咗再開。

---

# 第 5 部分：喺手機叫 Claude 做新字卡

⏱ 約 5 分鐘設定 ｜ 📱 手機

**呢部分係關鍵** —— 令你唔使開電腦都可以做新字卡。

## 5A. 接通 GitHub（做一次）

**1.** 手機開 **https://claude.ai/code** ，用你個 Claude 戶口登入。

**2.** 佢會叫你接通 GitHub，撳 **Connect GitHub**。

**3.** 跳去 GitHub 嗰版，撳綠色 **Authorize**。

**4.** 之後問你俾邊啲 repo：

- 撳 **Only select repositories**
- 撳個掣，喺清單揀 **zika**
- 撳 **Install**

### ✅ 做啱咗會見到

返到 claude.ai/code，可以喺個選單揀到 **zika**。

## 5B. 做新字卡

**1.** 開 **https://claude.ai/code**
（或者手機 Claude app 入面個 **Code** 掣）

**2.** 上面有個揀 repo 嘅位，揀 **zika**

**3.** 喺打字格打（可以直接 copy 呢句）：

```
跟 CLAUDE.md 嘅 v2 格式做「靜」呢隻字卡。做完 commit 同 push 上 main。
```

**4.** 撳送出

跟住我會喺雲端開工 —— 抓中大字庫、教育部辭典、古文字圖，睇圖寫【觀察】，
砌好張卡，放返上 GitHub。

**你可以熄咗個 app 去做其他嘢**，佢照跑。大概 **10 至 20 分鐘**。

**5.** 我做完之後，GitHub 會自動重新砌 PDF（再等 **3 至 5 分鐘**）

**6.** 開返個 `字卡.pdf`，新字卡就喺入面

## 常用嘅講法

| 你想做 | copy 呢句 |
|---|---|
| 做一隻字 | `跟 CLAUDE.md 嘅 v2 格式做「靜」呢隻字卡，做完 push 上 main` |
| 一次做幾隻 | `跟 CLAUDE.md 做「靜」「娜」「芳」三隻字卡，做完 push 上 main` |
| 改格式 | `所有字卡嘅 3.1 節加多一欄「出處年代」，改完 push` |
| 睇進度 | `28 隻字入面仲有邊幾隻未做？` |
| PDF 有豆腐格 | `跑 check_glyphs.py，睇下邊隻字冇字型，然後解決佢` |

> 💡 **點解每次都要寫「跟 CLAUDE.md」？**
> `CLAUDE.md` 係放喺 repo 入面嘅一份規矩書，寫晒你要求嘅嘢 ——
> 四個標記（【原文】【觀察】【分歧】【引申】）、同音字四級分類、
> 唔准掂術數層、邊啲來源用得邊啲用唔得。
> 提一提我，我就會照跟，唔會做出另一種格式。

---

# 第 6 部分：開網站（新）

⏱ 約 8 分鐘 ｜ 📱 手機或電腦都可以

做完這一步，會得到一條固定網址：

```
https://ckckkckccom-cpu.github.io/zika/
```

師傅按一下就看得到，**不用登入、不用下載、不用安裝任何東西**。
以後每次做了新字卡，這個網站會自動更新，網址不變。

## 6A. 先決定：公開，還是每月付費

GitHub 的免費網站功能（叫 **Pages**），**只有公開的 repo 才能用**。二選一：

| 做法 | 要做甚麼 | 費用 |
|---|---|---|
| **甲：把 repo 轉為 Public** | 在設定按兩下（見下面） | 免費 |
| **乙：保持 Private，升級 GitHub Pro** | 在 GitHub 訂閱 Pro | 約 US$4／月 |

**兩種做法做出來的網站完全一樣**，師傅看到的東西一模一樣。
分別只在於：甲會連同**原始檔案**（.md 原稿、程式）一併公開；乙不會。

> 網站本身無論選哪一種都是公開網址。差別只是原稿。

### 選甲的話：怎樣轉 Public

1. 打開 `https://github.com/ckckkckccom-cpu/zika`
2. 按上面一排的 **Settings**
3. 拉到最底，有一塊紅色框的 **Danger Zone**
4. 找 **Change repository visibility** → 按 **Change visibility**
5. 選 **Make public**，按提示打一次 repo 名字確認

## 6B. 打開 Pages（兩種做法都要做這一步）

1. 還是在 **Settings** 那一頁，看**左邊**的清單，按 **Pages**
2. 看 **Build and deployment** 下面的 **Source**
3. 按開那個選單，選 **GitHub Actions**
4. 選好就可以了，**不用按儲存**（它自己會記住）

> ⚠️ 這一步一定要自己動手。程式沒有權限替你開。

## 6C. 讓它砌一次

1. 按上面一排的 **Actions**
2. 左邊按 **砌網站同 PDF**
3. 右邊按灰色的 **Run workflow** → 再按綠色的 **Run workflow**
4. 等 **5 至 8 分鐘**

### ✅ 做對了會看到

- Actions 那一行前面是**綠色剔**
- 左邊清單出現 **Deployments**，或者 Settings → Pages 上面出現一條網址

打開 `https://ckckkckccom-cpu.github.io/zika/`，應該看到一頁「漢字多維解構」，
下面一格一格的大字。按其中一隻字，就看到那一隻字的完整字卡。

> 💡 **第一次可能要等多幾分鐘**網址才通。看到 404 就等三五分鐘再試。

## 6D. 傳給師傅

把這句連同網址傳給他就可以：

```
每隻字的研究都放咗喺呢度，隨時開得，唔使下載：
https://ckckkckccom-cpu.github.io/zika/

㩒隻字入去，最上面嗰幅圖係個推理脈絡，睇圖就大概明。
想睇齊晒啲字典原文，㩒最底「詳細考證」就展開。
字細嘅話，右上角有 A＋ 可以放大。
```

網站首頁也有一個**二維碼**，可以截圖傳給他，或者印出來。

## 6E. 之後怎樣更新

**甚麼都不用做。** 每次叫 Claude 做完新字卡並 push 上 main，
GitHub 會自動重新砌網站和 PDF，大約 5 至 8 分鐘後網站就更新了。網址永遠不變。

---

# 日常點用（設定完之後）

```
1. 手機開 claude.ai/code
2. 打「做『靜』字卡，push 上 main」
3. 熄咗個 app，去做其他嘢
4. 半個鐘後開 GitHub 撳個 字卡.pdf
```

**部電腦由頭到尾唔使開。**

---

# 出事點算

| 情況 | 點做 |
|---|---|
| Actions 紅色叉 | 撳入去 → 搵紅色叉嗰步 → 撳開 → 影相俾我 |
| 網址開唔到（404） | 等 5 分鐘再試；仲係唔得就檢查 Settings → Pages 嘅 Source 係咪揀咗 GitHub Actions |
| 網站冇更新到最新 | 去 Actions 睇下跑完未；跑完就喺手機拉個版 refresh |
| 只有 deploy 嗰步紅色 | Pages 未開。做返第 6B 部分 |
| 見唔到 `字卡.pdf` | 去 Actions 睇下係咪跑緊（🟡）或者失敗咗（❌） |
| PDF 好似冇更新 | 拉個版 refresh；GitHub app 就熄咗再開 |
| PDF 有豆腐格（⊠） | 喺 claude.ai/code 打：`跑 check_glyphs.py 睇下邊隻字冇字型` |
| claude.ai/code 揀唔到 zika | 重做第 5A 部分，確認揀咗 zika 先撳 Install |
| Token 90 日後過期 | 唔緊要。只有第 2 部分用過，之後都係用 claude.ai/code |
| 唔記得個 repo 網址 | 開 https://github.com → 右上頭像 → **Your repositories** |

---

# 會唔會使錢

| 項目 | 費用 |
|---|---|
| GitHub 戶口 | 免費 |
| Private repo | 免費（無限個） |
| GitHub Actions（砌網站同 PDF） | Private repo 每月 **2,000 分鐘**免費；Public repo **完全免費**。我哋一次用約 **6 分鐘** |
| GitHub Pages（個網站） | Public repo 免費；想保持 Private 就要 GitHub Pro，約 US$4／月 |
| Claude 雲端 | 用緊你 Pro／Max 月費，**冇額外收費**（但計入你嘅用量上限） |

**即係話：跟住呢份嘢做，唔使多畀錢。**
