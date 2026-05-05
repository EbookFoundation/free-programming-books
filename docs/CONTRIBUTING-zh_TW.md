*[閱讀其他語言版本的文件](README.md#translations)*


## 貢獻者許可協議

請遵循此 [許可協議](../LICENSE) 參與貢獻。


## 貢獻者行為準則

請同意並遵循此 [行為準則](CODE_OF_CONDUCT.md) 參與貢獻。([翻譯](README.md#translations))


## 概要

1. "一個可以輕易下載一本書的連結" 並不代表它導向的就是 *免費* 書籍。 請只提供免費內容。 確信你所提供的書籍是免費的。我們不接受導向 *需要* 工作電子郵件地址才能獲取書籍頁面的連結，但我們歡迎有需求這些連結的列表。

2. 你不需要會 Git：如果你發現了一些有趣的東西 *尚未出現在此 repo* 中，請開一個 [Issue](https://github.com/EbookFoundation/free-programming-books/issues) 進行主題討論。
    * 如果你已經知道 Git，請 Fork 此 repo 並提交 Pull Request (PR)。

3. 這裡有六種列表，請選擇正確的一項：

    * *Books* ：PDF、HTML、ePub、基於 gitbook.io 的網站、Git 的 repo 等。
    * *Courses* ：課程是一種學習素材，而不是一本書 [This is a course](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/)。
    * *Interactive Tutorials* ：一個互動式網站，允許使用者輸入程式碼或指令並執行結果。例如：[Try Haskell](http://tryhaskell.org)，[Try Git](https://learngitbranching.js.org)。
    * *Playgrounds* : Playgrounds 是學習程式設計的線上互動式網站、遊戲或桌面軟體。你可以在上面編寫、編譯、運行或分享程式碼片段。 Playgrounds 通常允許你 fork 程式碼然後在其中盡情的編寫程式碼。
    * *Podcasts and Screencasts* ：Podcast 和影音。
    * *Problem Sets & Competitive Programming* ：一個網站或軟體，讓你透過解決簡單或複雜的問題來評估你的程式技能，可能有程式碼檢查，或與其他用戶比對结果。

4. 確保遵循下方的 [基本準則](#基本準則)，並遵循此 repo 文件的 [Markdown 規定格式](#規定格式)。

5. GitHub Actions 將運行測試，以確保你的列表是 **按字母顺序排列** 的，並 **遵循格式化規則**。請 **確保** 你的更改通過該測試。


### 基本準則

* 確保你提交的每一本書都是免費的。如有需要請 Double-check。如果你在 PR 中註明為什麼你認為這本書是免費的，這對管理員是很有幫助的。
* 我們不接受儲存在 Google Drive、Dropbox、Mega、Scribd、Issuu 和其他類似文件上傳平台上的文件。
* 請按照[下方敘述](#依照字母排序)的字母順序插入連結。
* 使用最權威來源的連結(意思是原作者的網站比編輯的網站好，比第三方網站好)。
    * 沒有文件託管服務(包括(但不限於) Dropbox 和 Google Drive 連結)。
* 優先選擇使用 `https` 連結，而不是 `http` 連結 -- 只要它們位於相同的網域並提供相同的内容。
* 在網域根目錄上，去掉尾末的斜槓：使用 `http://example.com` 代替 `http://example.com/`。
* 優先選擇最短的連結：使用 `http://example.com/dir/` 比使用 `http://example.com/dir/index.html` 更好。
    * 不要提供短連結
* 優先選擇使用 "current" 連結代替有 "version" 連結：使用 `http://example.com/dir/book/current/` 比使用 `http://example.com/dir/book/v1.0.0/index.html` 更好。
* 如果一個連結存在過期的證書/自簽名證書/SSL問題的任何其他類型：
    1. *replace it* ：如果可能的話，將其 *替換* 為對應的 `http` (因為在移動設備上接受異常可能比較複雜)。
    2. *leave it* ：如果沒有`http`版本，但仍然可以通過`https`造訪連結，則在瀏覽器中添加異常或忽略警告。
    3. *remove it* ：上述狀況以外則刪除掉它。
* 如果一個連結以多種格式存在，請添加一個單獨的連結，並註明每種格式。
* 如果一個資源存在於Internet上的不同位置
    * 使用最權威來源的連結(意思是原始作者的網站比編輯的網站好，比第三方網站好)。
    * 如果它們連結到不同的版本，你認為這些版本差異很大，值得保留，那麼添加一個單獨的連結，並對每個版本做說明(參考 [Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353) 有助於格式化問題的討論)。
* 相較一個比較大的提交，我們更傾向於原子提交(通過添加/删除/修改進行一次提交)。在提交PR之前没有必要壓縮你的提交。(為了維護人員的方便，我們永遠不會執行這個規則)。
* 如果一本書比較舊，請在書名中註明出版日期。
* 包含作者的名字或適當的名字。中文版本可以用 “`等`” (“`et al.`”) 縮短作者列表。
* 如果一本書還没有完成，並且仍在編寫中，則需添加 “`in process`” 符號，參考 [下文](#in_process) 所述。
* 如果資源是透過 [*Internet Archive 的 Wayback Machine*](https://web.archive.org)（或類似服務）還原的，請依照[下文](#archived)所述新增 “`archived`” 標記。最好使用較新且完整的封存版本。
* 如果在開始下載之前需要電子郵件地址或帳户設置，請在括號中添加合適的語言描述，例如：`(*需要* 電子郵件，但不是必需的)`。


### 規定格式

* 所有列表都是 `.md` 文件。試着學習 [Markdown](https://guides.github.com/features/mastering-markdown/) 語法。它很容易上手！
* 所有的列表都以索引開始。它的作用是列出並連結所有的 sections (章節/段落)或 subsections (子段落/子章節)。務必遵循字母順序排列。
* Sections (章節/段落)使用3級標題(`###`)，subsections (子段落/子章節)使用4級標題 (`####`)。

整體思維為：

* `2` ：新添加的 Section 與末尾連結間必需留有 `2` 個空行
* `1` ：標題和第一個連結之間必需留有 `1` 個空行的空行
* `0` ：任何兩個連結之間不能留有任何空行
* `1` ：每個 `.md` 文件末尾必需留有 `1` 個空行

舉例：

```text
[...]
* [一本很有用的書](http://example.com/example.html)
                                (空行)
                                (空行)
### 電子書種類標題
                                (空行)
* [Another 很有用的書](http://example.com/book.html)
* [Other 有用的書](http://example.com/other.html)
```

* 在 `]` 和 `(` 之間不要留有空格：

    ```text
    錯誤：* [一本很有用的書] (http://example.com/book.html)
    正確：* [一本很有用的書](http://example.com/book.html)
    ```

* 如果包括作者，請使用' - '(由單個空格(英文半型)包圍的破折號)：

    ```text
    錯誤：* [一本很有用的書](http://example.com/book.html)- 張顯宗
    正確：* [一本很有用的書](http://example.com/book.html) - 張顯宗
    ```

* 在連結和電子書格式之間放一個空格：

    ```text
    錯誤：* [一本很有用的書](https://example.org/book.pdf)(PDF)
    正確：* [一本很有用的書](https://example.org/book.pdf) (PDF)
    ```

* 如需備注或注解，請使用英文半型括號`( )`：

    ```text
    錯誤：* [一本很有用的書](https://example.org/book.pdf) （繁體中文）
    正確：* [一本很有用的書](https://example.org/book.pdf) (繁體中文)
    ```

* 作者在電子書格式之前：

    ```text
    錯誤：* [一本很有用的書](https://example.org/book.pdf)- (PDF) 張顯宗
    正確：* [一本很有用的書](https://example.org/book.pdf) - 張顯宗 (PDF)
    ```

* 多重格式：

    ```text
    錯誤：* [一本很有用的書](http://example.com/)- 張顯宗 (HTML)
    錯誤：* [一本很有用的書](https://downloads.example.org/book.html)- 張顯宗 (download site)
    正確：* [一本很有用的書](http://example.com/) - 張顯宗 (HTML) [(PDF, EPUB)](https://downloads.example.org/book.html)
    ```

* 多作者，多譯者時，請使用中文 `、` 進行分隔，在譯者名字後請使用英文半型括號包圍的 `(翻譯)`，可以用 “等” 縮短作者列表：

    ```text
    錯誤：* [一本很有用的書](https://example.org/book.pdf) - 張顯宗，岳綺羅
    正確：* [一本很有用的書](https://example.org/book.pdf) - 張顯宗、岳綺羅(翻譯)
    正確：* [一本很有用的書](https://example.org/book.pdf) - 張顯宗、岳綺羅、顧玄武、出塵子 等
    ```

* 在舊書的標題中包括出版年份：

    ```text
    錯誤：* [一本很有用的書](https://example.org/book.html) - 張顯宗 - 1970
    正確：* [一本很有用的書 (1970)](https://example.org/book.html) - 張顯宗
    ```

* <a id="in_process"></a>編寫(翻譯)中的書籍：

    ```text
    正確：* [即將出版的一本書](http://example.com/book2.html) - 張顯宗 (HTML) *( :construction: 編寫中)*
    正確：* [即將出版的一本書](http://example.com/book2.html) - 張顯宗 (HTML) *( :construction: 翻譯中)*
    ```

- <a id="archived"></a>封存連結：

    ```text
    正確：* [一本透過 Wayback Machine 保存的有趣書籍](https://web.archive.org/web/20211016123456/http://example.com/) - John Doe (HTML) *( :card_file_box: archived)*
    ```

- <a id="license"></a>免費授權條款（雖然我們會收錄「保留所有權利」但可免費閱讀的資源，但我們鼓勵使用自由授權條款，例如 Creative Commons）：

    ```text
    正確：* [一本很有用的書](https://example.org/book.pdf) - Jane Roe (PDF) (CC BY-SA)
    ```

    支援的授權條款（不寫版本號）：

    - `CC BY` “Creative Commons attribution”
    - `CC BY-NC` “Creative Commons non-commercial”
    - `CC BY-SA` “Creative Commons share-alike”
    - `CC BY-NC-SA` “Creative Commons non-commercial, share-alike”
    - `CC BY-ND` “Creative Commons no-derivatives”
    - `CC BY-NC-ND` “Creative Commons non-commercial, no-derivatives”
    - `GFDL` “Gnu Free Documentation License”

#### 新增授權說明（分步）

當資源以自由/開放授權條款發布時，請在格式說明之後用括號新增簡短的授權說明。請按以下步驟操作：

1. 在資源頁面確認授權條款。
   - 查看網站頁尾、“About” 頁面或 LICENSE/Legal 區段。
   - 只為自由/開放內容授權新增授權說明（見上方支援列表）。不要新增 “All Rights Reserved” 之類的說明。
2. 將授權名稱規範化為不含版本號的受支援短代碼。
   - 範例：“Creative Commons Attribution 4.0” → `CC BY`；“CC BY-SA 3.0” → `CC BY-SA`；“GNU Free Documentation License” → `GFDL`。
3. 將授權放在格式說明之後、其他備註之前。
   - 單一格式：
     ```markdown
     * [一本很有用的書](https://example.org/book.pdf) - Jane Roe (PDF) (CC BY-SA)
     ```
   - 多種格式：
     ```markdown
     * [很有用的指南](https://example.org/) - Jane Roe (HTML, PDF) (CC BY)
     ```
   - 帶有其他備註（例如 archived 或 in process）：
     ```markdown
     * [老但經典的書](https://web.archive.org/web/20211016123456/http://example.com/) - John Doe (HTML) (CC BY) *( :card_file_box: archived)*
     ```
4. 如果不同版本/格式使用不同授權，請將它們列為單獨條目，並分別註明正確授權。
5. 如果不確定，請在 PR 中留言說明您為什麼認為該資源使用自由授權，以及您在哪裡找到了授權資訊。

<!----><a id="alphabetical-order"></a>
### 依照字母排序

- 當出現多個相同字母開頭的標題時，則照第二個字母排序，以此類推。例如：`aa` 排在 `ab` 前面
- `one two` 排在 `onetwo` 前面

如果你看到錯誤的連結，請檢查 linter 的錯誤訊息來找到哪一行順序需要交換


### 注意事項

雖然基本規則相對簡單，但我們列出的資源非常多樣。以下說明我們如何處理這些差異。


#### 中繼資料

我們的清單提供一組最少必要的中繼資料：標題、URL、創作者、平台和存取註記。


##### 標題

- 不要自創標題。我們會盡量使用資源本身的標題；如果可以避免，強烈建議貢獻者不要自創標題，也不要用編輯性的方式改寫標題。較舊的作品是例外；如果它們主要具有歷史價值，在標題後以括號附上年份，可以幫助使用者判斷是否感興趣。
- 不要使用全大寫標題。通常使用標題式大小寫是合適的；如有疑問，請使用來源本身的大小寫格式。
- 不要使用表情符號。


##### URL

- 我們不允許使用短網址。
- 必須移除 URL 中的追蹤碼。
- 國際化 URL 應該被轉義。瀏覽器網址列通常會將其渲染成 Unicode，但請使用複製貼上。
- 在支援 HTTPS 的網站上，安全的 (`https`) URL 永遠優先於不安全的 (`http`) URL。
- 我們不喜歡 URL 指向未直接託管所列資源、而只是再導向其他地方的網頁。


##### 創作者

- 我們希望在適當情況下標註免費資源的創作者，包括譯者！
- 對於翻譯作品，應標註原作者。我們建議使用 [MARC relators](https://loc.gov/marc/relators/relaterm.html) 來標註作者以外的創作者，如下例所示：

    ```markdown
    * [一本譯作](http://example.com/book-zh.html) - John Doe, `trl.:` Mike The Translator
    ```

    這裡的 `trl.:` 註記使用的是 MARC 中表示「譯者」的關係代碼。
- 使用逗號 `,` 分隔作者列表中的每個項目。
- 您可以使用「`et al.`」縮短作者列表。
- 我們不允許為創作者提供連結。
- 對於彙編或混合作品，「創作者」可能需要描述。例如，GoalKicker 或 RIP Tutorial 書籍會標註為「`Compiled from StackOverflow documentation`」。
- 我們不會在創作者姓名中包含 “Prof.” 或 “Dr.” 等敬稱。


##### 有時限的課程和試用

- 我們不會列出需要在六個月後移除的內容。
- 如果課程有有限的報名期限或持續時間，我們不會列出它。
- 我們不能列出只在有限時間內免費的資源。


##### 平台與存取註記

- 課程。尤其是對於課程列表，平台是資源描述的重要部分。這是因為不同課程平台有不同功能和存取模式。雖然我們通常不會列出需要註冊的書籍，但許多課程平台若沒有某種帳戶就無法使用部分功能。課程平台的例子包括 Coursera、EdX、Udacity 和 Udemy。當課程依賴某個平台時，應在括號中列出平台名稱。
- YouTube。我們有許多由 YouTube 播放清單組成的課程。我們不會將 YouTube 列為平台，而是嘗試列出 YouTube 創作者，這通常是子平台。
- YouTube 影片。除非單一 YouTube 影片超過一小時，且結構類似課程或教學，否則我們通常不會連結到單一 YouTube 影片。如果是這種情況，請務必在 PR 描述中說明。
- 不要使用縮短連結（例如 youtu.be/xxxx）！
- Leanpub。Leanpub 託管的書籍有多種存取模式。有時一本書無需註冊即可閱讀；有時則需要 Leanpub 帳戶才能免費存取。考量書籍品質，以及 Leanpub 存取模式的混合性和流動性，我們允許用存取註記 `*(Leanpub account or valid email requested)*` 列出後者。


#### 類型

決定資源屬於哪個清單的第一條規則，是查看資源如何描述自己。如果它稱自己為一本書，那麼也許它就是一本書。


##### 我們未列出的類型

由於網際網路非常龐大，因此我們不在列表中包含：

- 部落格
- 部落格文章
- 文章
- 網站（託管大量我們會列出項目的網站除外）。
- 不屬於課程或螢幕錄影的影片。
- 書籍章節
- 書籍的預覽樣章
- IRC 或 Telegram 頻道
- Slack 或郵件列表

我們的競賽程式設計列表對這些排除項沒有那麼嚴格。倉庫的範圍由社群決定；如果您想建議更改或新增範圍，請使用 issue 提出建議。


##### 書籍與其他內容

我們對「是否像書」並不那麼挑剔。以下是一些表示資源是一本書的屬性：

- 它有 ISBN（國際標準書號）
- 它有目錄
- 提供可下載版本，尤其是 ePub 檔案。
- 它有版本
- 它不依賴互動內容或影片
- 它試圖全面涵蓋某個主題
- 它是獨立完整的

我們列出的許多書籍不具備這些屬性；這可能取決於上下文。


##### 書籍與課程

有時兩者可能很難區分！

課程通常有相關教科書，我們會將其列在書籍列表中。課程包含講座、練習、測驗、筆記或其他教學輔助資料。單一講座或影片本身不是一門課程。PowerPoint 也不是課程。


##### 互動式教學與其他內容

如果您可以將其列印出來並保留其精髓，那它就不是互動式教學。


### Automation

- 規定格式驗證是由 [GitHub Actions](https://docs.github.com/en/actions) 自動化進行，使用 [fpb-lint](https://github.com/vhf/free-programming-books-lint) 套件 (參閱 [`.github/workflows/fpb-lint.yml`](../.github/workflows/fpb-lint.yml))。
- 使用 [awesome_bot](https://github.com/dkhamsing/awesome_bot) 進行連結驗證。
- 可以藉由提交一個內容包含`check_urls=file_to_check`來觸發連結驗證:

    ```properties
    check_urls=free-programming-books.md free-programming-books-zh.md
    ```

- 您可以以一個空白區隔出想要進行驗證的檔案名稱來一次驗證多個檔案。
- 如果您一次驗證多個檔案，自動化測試的結果會是基於最後一個驗證的檔案。您的測試可能會因此通過，因此請詳加確認測試日誌。可以在 Pull Request 結果中點選"Show all checks" -> "Details" 來查看。


### 修正 RTL/LTR linter 錯誤

如果您執行 RTL/LTR Markdown Linter（用於 `*-ar.md`、`*-he.md`、`*-fa.md`、`*-ur.md` 檔案）並看到錯誤或警告：

- RTL 文字中的 **LTR 單字**（例如 “HTML”、“JavaScript”）：在每個 LTR 片段後立即新增 `&rlm;`；
- **LTR 符號**（例如 “C#”、“C++”）：在每個 LTR 符號後立即新增 `&lrm;`；

#### 範例

**錯誤**
```html
<div dir="rtl" markdown="1">
* [كتاب الأمثلة في R](URL) - John Doe (PDF)
</div>
```
**正確**
```html
<div dir="rtl" markdown="1">
* [كتاب الأمثلة في R&rlm;](URL) - John Doe&rlm; (PDF)
</div>
```
---
**錯誤**
```html
<div dir="rtl" markdown="1">
* [Tech Podcast - بودكاست المثال](URL) – Ahmad Hasan, محمد علي
</div>
```
**正確**
```html
<div dir="rtl" markdown="1">
* [Tech Podcast - بودكاست المثال](URL) – Ahmad Hasan,&rlm; محمد علي
</div>
```
---
**錯誤**
```html
<div dir="rtl" markdown="1">
* [أساسيات C#](URL)
</div>
```
**正確**
```html
<div dir="rtl" markdown="1">
* [أساسيات C#&lrm;](URL)
</div>
```
