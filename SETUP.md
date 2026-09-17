# 由 0 開始：將字卡搬上雲端

目標：**部電腦完全唔使開**，用手機就可以（一）叫 Claude 做新字卡、（二）隨時睇到最新 PDF。

做一次就搞掂，之後日常用就得。全程大概 **30 分鐘**。

---

## 你要準備

- 一個電郵（收驗證碼）
- 你部電腦（**淨係第 2 部分要用一次**，之後永遠唔使再開）
- Claude 嘅 **Pro 或 Max** 月費計劃（第 4 部分要用；免費版冇雲端功能）

---

# 第 1 部分：開 GitHub 戶口同倉庫

> GitHub 係放檔案嘅地方，好似 Google Drive，但佢識自動幫你做嘢。
> 「倉庫」（repository / repo）＝一個放住個 project 所有檔案嘅資料夾。

### 1.1 開戶口

1. 手機或電腦開 **https://github.com/signup**
2. 順住填：電郵 → 密碼 → 改個 username（例如 `ckchan`，只可以用英文字母同數字）
3. 去電郵收驗證碼，填返落去
4. 問你揀計劃嗰陣，揀 **Free**（免費版夠晒用）

### 1.2 開一個倉庫

1. 登入後，撳右上角你個**頭像** → 揀 **Your repositories**
2. 撳綠色 **New** 掣
3. 咁樣填：
   - **Repository name**：打 `zika`（呢個係「字卡」嘅拼音。**用英文，唔好用中文**，因為之後個網址會用到）
   - **Description**：可以留空，或者打 `漢字多維解構字卡`
   - 揀 **Private**（私人，只有你自己睇到）
     > 如果揀 Private，第 3 部分嘅 GitHub Pages 需要付費版先用到。
     > **想免費用網頁版就揀 Public**（公開）。你嘅字卡冇敏感資料，揀 Public 冇問題。
     > 唔肯定就揀 **Public**。
   - 下面 **Add a README file** 等三個剔，**全部唔好剔**
4. 撳 **Create repository**

開完之後，你會見到一版嘢，上面有一行好似咁嘅字：

```
https://github.com/你嘅username/zika.git
```

**呢行嘢好重要，copy 低佢**（撳右邊個複製圖示）。下一步要用。

---

# 第 2 部分：將檔案送上去（**淨係呢部分要用電腦**）

檔案而家喺你部電腦嘅 `/home/user25/字卡` 入面，要送上 GitHub。

### 2.1 攞一條「通行證」

GitHub 唔收密碼，要用一條叫 token 嘅嘢。

1. 開 **https://github.com/settings/tokens?type=beta**
2. 撳 **Generate new token**
3. 填：
   - **Token name**：打 `zika-upload`
   - **Expiration**：揀 **90 days**
   - **Repository access**：揀 **Only select repositories** → 喺下面個掣揀返你頭先開嗰個 `zika`
   - **Permissions** → 撳開 **Repository permissions** → 搵 **Contents** 嗰行 → 右邊揀 **Read and write**
     （其他全部唔使郁）
4. 拉到最底撳 **Generate token**
5. 佢會出一條好長、`github_pat_` 開頭嘅字串 —— **即刻 copy 低**
   ⚠️ 呢條嘢**只會出現一次**，撳走咗就要重新攞過。
   ⚠️ 當佢係密碼，唔好俾人、唔好貼上網。

### 2.2 送檔案

喺你部電腦嘅 Claude Code 度，直接叫我：

> 幫我 push 上 GitHub，我個 repo 網址係 https://github.com/你嘅username/zika.git

然後我會問你攞條 token。你貼返俾我，我會幫你送上去，再即刻清走條 token 唔會留底。

（想自己做嘅話，就喺 terminal 打呢兩行，`USERNAME` 同 `TOKEN` 換返做你自己嘅：）

```bash
cd /home/user25/字卡
git remote add origin https://USERNAME:TOKEN@github.com/USERNAME/zika.git
git push -u origin main
git remote set-url origin https://github.com/USERNAME/zika.git   # 清走條 token
```

送完之後，返去 `https://github.com/你嘅username/zika` 撳 refresh，
應該見到啲檔案（`偉.md`、`家.md`、`img` 資料夾…）。

---

# 第 3 部分：開自動砌 PDF

呢步之後，每次有新字卡，GitHub 會**自己**砌好 PDF 同網頁。

### 3.1 開 Pages

1. 喺你個 repo 版面，撳上面嘅 **Settings**（齒輪圖示）
2. 左邊揀 **Pages**
3. **Source** 嗰度，由 `Deploy from a branch` 揀做 **GitHub Actions**
4. 唔使撳 Save，佢自動記住

### 3.2 撳一次掣試下

1. 撳上面嘅 **Actions**
2. 如果見到 *"Workflows aren't being run on this forked repository"* 之類嘅字，撳綠色掣批准
3. 左邊揀 **字卡自動砌 PDF 同網頁**
4. 右邊撳 **Run workflow** → 再撳一次綠色 **Run workflow**
5. 等大概 **3–5 分鐘**。中間會見到一個轉緊嘅黃色圓圈，完成會變**綠色剔**

> 🔴 **變咗紅色叉？** 撳入去睇邊一步紅咗，將個錯誤訊息影相俾我，我幫你睇。

### 3.3 攞你嘅網址

成功之後：

1. 返去 **Settings → Pages**
2. 最上面會見到：**Your site is live at `https://你嘅username.github.io/zika/`**
3. **呢個就係你嘅字卡網址。收藏佢。**

| 你想睇 | 開呢個 |
|---|---|
| 網頁版（手機睇最方便） | `https://你嘅username.github.io/zika/` |
| PDF 版 | `https://你嘅username.github.io/zika/cards.pdf` |

📱 **建議**：喺手機開個網址 → Safari 撳「分享」→「加至主畫面」，
之後就好似個 app 咁，撳一下就開到。

---

# 第 4 部分：喺手機叫 Claude 做新字卡

呢部分係關鍵 —— **令你唔使開電腦都可以做新字卡。**

### 4.1 接通 GitHub

1. 手機或電腦開 **https://claude.ai/code**
2. 用你個 Claude 戶口登入
3. 佢會問你接通 GitHub → 撳 **Connect GitHub**
4. 跳去 GitHub 之後，撳 **Authorize**
5. 問你俾邊啲倉庫嗰陣，揀 **Only select repositories** → 揀返 `zika` → 撳 **Install**

### 4.2 做新字卡

1. 開 **https://claude.ai/code**（或者手機 Claude app 入面個 **Code** 掣）
2. 上面揀返個倉庫 **zika**
3. 喺打字嗰格打：

> 跟 CLAUDE.md 嘅 v2 格式做「靜」呢隻字卡。做完 commit 同 push 上 main。

4. 撳送出

跟住我會喺雲端開工 —— 抓中大字庫、教育部辭典、古文字圖，睇圖寫【觀察】，
砌好張卡，commit 返上 GitHub。**你可以熄咗個 app 去做其他嘢**，佢照跑。

5. 完成之後，GitHub 會自動重新砌 PDF（等 3–5 分鐘）
6. 開返你個網址，新字卡就喺度

### 常用嘅講法

| 你想做 | 打呢句 |
|---|---|
| 做一隻字 | `跟 CLAUDE.md 嘅 v2 格式做「靜」呢隻字卡，做完 push 上 main` |
| 一次做幾隻 | `跟 CLAUDE.md 做「靜」「娜」「芳」三隻字卡，做完 push 上 main` |
| 改格式 | `所有字卡嘅 3.1 節加多一欄「出處年代」，改完 push` |
| 睇進度 | `仲有邊幾隻字未做？` |

> 💡 **點解要寫「跟 CLAUDE.md」**：`CLAUDE.md` 入面寫晒你嘅規矩 ——
> 四個標記（【原文】【觀察】【分歧】【引申】）、同音字四級分類、
> 唔准掂術數層、邊啲來源用得。提一提我，我就會照跟。

---

# 日常點用

```
手機開 claude.ai/code  →  打「做『靜』字卡，push 上 main」
                              ↓
                      我喺雲端做（10–20 分鐘）
                              ↓
                   GitHub 自動砌 PDF（3–5 分鐘）
                              ↓
              開你個網址 → 見到新字卡
```

**部電腦由頭到尾唔使開。**

---

# 出事點算

| 情況 | 點做 |
|---|---|
| Actions 紅色叉 | 撳入去睇邊步紅咗，將錯誤訊息影相俾我 |
| 網址開唔到 / 404 | 等多 5 分鐘（第一次要耐啲）。仲係唔得就檢查 Settings → Pages 係咪揀咗 **GitHub Actions** |
| PDF 有豆腐格（⊠） | 喺 claude.ai/code 打：`跑 check_glyphs.py 睇下邊隻字冇字型` |
| 手機睇唔到新字卡 | 拉一拉個網頁 refresh；或者揀「重新載入而唔用快取」 |
| Token 過期（90 日後） | 只影響第 2 部分。之後都係用 claude.ai/code，唔會再用到條 token |

---

# 幾個名詞（唔使記，睇到嗰陣識返就得）

| 個名 | 即係咩 |
|---|---|
| **repository / repo** | 一個 project 嘅資料夾 |
| **commit** | 儲存一次改動，好似「另存新檔」但會記住成個歷史 |
| **push** | 將改動由電腦送上 GitHub |
| **GitHub Actions** | GitHub 幫你自動做嘢（我哋用佢砌 PDF） |
| **GitHub Pages** | GitHub 免費幫你放個網頁 |
| **token** | 一條代替密碼嘅長字串 |
| **workflow** | 一張「跟住做」嘅清單，即係 `.github/workflows/build.yml` |

---

# 會唔會使錢

| 項目 | 費用 |
|---|---|
| GitHub 戶口 | 免費 |
| GitHub Actions（砌 PDF） | Public 倉庫**免費無限**；Private 每月 2000 分鐘免費（我哋一次用約 4 分鐘） |
| GitHub Pages | Public 免費 |
| Claude 雲端 | 用緊你 Pro／Max 月費，**冇額外收費**（但計入你嘅用量上限） |
