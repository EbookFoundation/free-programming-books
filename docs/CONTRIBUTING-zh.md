*[阅读本文的其他语言版本](README.md#nslations)*


## 贡献者许可协议

请遵循此[许可协议](../LICENSE)参与贡献。


## 贡献者行为准则

请同意并遵循此[行为准则](CODE_OF_CONDUCT.md)参与贡献。([translations](README.md#nslations))


## 概要

1. 仅仅因为链接“促进下载书籍”并不意味着它指向“免费”书籍。 请仅提供免费内容的链接。 确保您分享的书籍是免费的。 我们不接受“需要”有效电子邮件地址才能访问书籍的链接，但我们欢迎列出这些资源。

2. 您不需要熟悉 Git：如果您发现一些有趣的东西*尚未包含在此存储库中*，请打开一个[问题](https://github.com/EbookFoundation/free-programming-books/issues）开始讨论相关主题。
    * 如果你已经知晓Git，请Fork本仓库并提交Pull Request (PR)。

3. 这里有6种列表，请选择正确的一个：

    * *Books* ：PDF、HTML、ePub、基于一个 gitbook.io的站点、一个Git仓库等等。
    * *Courses* ：课程是一种学习材料，而不是一本书 [This is a course](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/)。
    * *Interactive Tutorials* ：一个交互式网站，它允许用户输入代码或命令并对结果进行评估。例如：[Try Haskell](http://tryhaskell.org)，[Try GitHub](http://try.github.io)。
    * *Playgrounds* : Playgrounds 可能是学习编程的在线交互式网站、游戏或桌面软件。你可以在上面编写、编译、运行或分享代码片段。Playgrounds 通常允许你 fork 代码然后在其中尽情的编写代码。
    * *Podcasts and Screencasts* ：播客和视频。
    * *Problem Sets & Competitive Programming* ：一个网站或软件，让你通过解决简单或复杂的问题来评估你的编程技能，有或没有代码审查，有或没有与其他用户对比结果。

4. 确保遵循下面的[基本准则](#基本准则)，并遵循本仓库文件的[Markdown规定格式](#规定格式)。

5. GitHub Actions 将运行测试，以确保你的列表是 **按字母顺序排列** 的，并 **遵循格式化规则**。请 **确保** 你的更改通过了该测试。

### 审查和适应过程

为了确保一致性和准确性，我们在将内容从英语版本翻译成其他语言时遵循审查和调整流程。 它的工作原理如下：

1. **参考英文文件**：我们始终参考该文件的英文版本作为信息和指南的主要来源。

2. **翻译和本地化**：译员仔细地将内容翻译成目标语言，同时牢记语言和文化的细微差别。

3. **审阅**：翻译后，文件会经过母语人士的审阅过程，以确保翻译的准确性。

4. **改编**：在某些情况下，特定术语、短语或参考文献可能需要改编以更好地适应目标受众。 译者可以灵活地进行这些调整，同时保留核心信息。

5. **质量保证**：进行最终的质量保证检查，以验证翻译的文档是否连贯、准确且适合文化。

6. **持续改进**：我们鼓励贡献者和读者提供反馈和建议，以不断改进翻译内容。

通过遵循这一流程，我们的目标是提供既忠实于原始内容又与目标受众相关的高质量翻译。
### 基本准则

* 请确保您提交的每本书确实是免费的。 如果需要，请仔细检查其状态。 如果您可以在 PR 中解释为什么您认为这本书是免费的，这对管理员会有帮助。
* 我们不接受存储在Google Drive、Dropbox、Mega、Scribd、Issuu和其他类似文件上传平台上的文件。
* 请按照字母顺序插入链接, as described [below](#alphabetical-order).
* 使用最权威来源的链接(意思是原作者的网站比编辑的网站好，比第三方网站好)。
    * 没有文件托管服务(包括(但不限于)Dropbox和谷歌驱动器链接)。
* 优先选择使用 `https` 链接，而不是 `http` 链接 -- 只要它们位于相同的域并提供相同的内容。
* 在根域上，去掉末尾的斜杠：使用 `http://example.com` 代替 `http://example.com/`。
* 总是选择最短的链接：使用 `http://example.com/dir/` 比使用 `http://example.com/dir/index.html` 更好。
    * 不要提供短链接
* 优先选择使用 "current" 链接代替有 "version" 链接：使用 `http://example.com/dir/book/current/` 比使用 `http://example.com/dir/book/v1.0.0/index.html` 更好。
* 如果一个链接存在过期的证书/自签名证书/SSL问题的任何其他类型：
    1. *replace it* ：如果可能的话，将其 *替换* 为对应的`http`(因为在移动设备上接受异常可能比较复杂)。
    2. *leave it* ：如果没有`http`版本，但仍然可以通过`https`访问链接，则在浏览器中添加异常或忽略警告。
    3. *remove it* ：上述以外删除掉它。
* 如果一个链接以多种格式存在，请添加一个单独的链接，并注明每种格式。
* 如果一个资源存在于Internet上的不同位置
    * 使用最权威来源的链接(意思是原始作者的网站比编辑的网站好，比第三方网站好)。
    * 如果它们链接到不同的版本，你认为这些版本差异很大，值得保留，那么添加一个单独的链接，并对每个版本做一个说明(参见[Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353)有助于格式化问题的讨论)。
* 相较一个比较大的提交，我们更倾向于原子提交(通过添加/删除/修改进行一次提交)。在提交PR之前没有必要压缩你的提交。(我们永远不会执行这个规则，因为这只是维护人员的方便)。
* 如果一本书比较旧，请在书名中注明出版日期。
* 包含作者的名字或适当的名字。中文版本可以用 “`等`” (“`et al.`”) 缩短作者列表。
* 如果一本书还没有完成，并且仍在编写中，则需添加 “`in process`” 符号，参见[下文](#in_process)所述。
- if a resource is restored using the [*Internet Archive's Wayback Machine*](https://web.archive.org) (or similar), add the "`archived`" notation, as described [below](#archived). The best versions to use are recent and complete.
* 如果在开始下载之前需要电子邮件地址或帐户设置，请在括号中添加合适的语言描述，例如：`(*需要*电子邮件，但不是必须的)`。


### 规定格式

* 所有列表都是`.md`文件。试着学习[Markdown](https://guides.github.com/features/mastering-markdown/)语法。它很容易上手！
* 所有的列表都以索引开始。它的作用是列出并链接所有的sections(章节/段落)或subsections(子段落/子章节)。务必遵循字母顺序排列。
* Sections(章节/段落)使用3级标题(`###`)，subsections(子段落/子章节)使用4级标题 (`####`)。

整体思想为：

* `2` ：新添加的Section与末尾链接间必须留有`2`个空行
* `1` ：标题和第一个链接之间必须留有`1`个空行的空行
* `0` ：任何两个链接之间不能留有任何空行
* `1` ：每个`.md`文件末尾必须留有`1`个空行

举例：

```text
[...]
* [一本很有用的书](http://example.com/example.html)
                                (空行)
                                (空行)
### 电子书种类标题
                                (空行)
* [Another 很有用的书](http://example.com/book.html)
* [Other 有用的书](http://example.com/other.html)
```

* 在 `]` 和 `(` 之间不要留有空格：

    ```text
    错误：* [一本很有用的书] (http://example.com/book.html)
    正确：* [一本很有用的书](http://example.com/book.html)
    ```

* 如果包括作者，请使用' - '(由单个空格(英文半角)包围的破折号)：

    ```text
    错误：* [一本很有用的书](http://example.com/book.html)- 张显宗
    正确：* [一本很有用的书](http://example.com/book.html) - 张显宗
    ```

* 在链接和电子书格式之间放一个空格：

    ```text
    错误：* [一本很有用的书](https://example.org/book.pdf)(PDF)
    正确：* [一本很有用的书](https://example.org/book.pdf) (PDF)
    ```

* 如需备注或注解，请使用英文半角括号`( )`：

    ```text
    错误：* [一本很有用的书](https://example.org/book.pdf) （繁体中文）
    正确：* [一本很有用的书](https://example.org/book.pdf) (繁体中文)
    ```

* 作者在电子书格式之前：

    ```text
    错误：* [一本很有用的书](https://example.org/book.pdf)- (PDF) 张显宗
    正确：* [一本很有用的书](https://example.org/book.pdf) - 张显宗 (PDF)
    ```

* 多重格式：

    ```text
    错误：* [一本很有用的书](http://example.com/)- 张显宗 (HTML)
    错误：* [一本很有用的书](https://downloads.example.org/book.html)- 张显宗 (download site)
    正确：* [一本很有用的书](http://example.com/) - 张显宗 (HTML) [(PDF, EPUB)](https://downloads.example.org/book.html)
    ```

* 多作者，多译者时，请使用中文 `、` 进行分隔，在译者名字后请使用英文半角括号包围的 `(翻译)`，可以用 “等” 缩短作者列表：

    ```text
    错误：* [一本很有用的书](https://example.org/book.pdf) - 张显宗，岳绮罗
    正确：* [一本很有用的书](https://example.org/book.pdf) - 张显宗、岳绮罗(翻译)
    正确：* [一本很有用的书](https://example.org/book.pdf) - 张显宗、岳绮罗、顾玄武、出尘子 等
    ```

* 在旧书的标题中包括出版年份：

    ```text
    错误：* [一本很有用的书](https://example.org/book.html) - 张显宗 - 1970
    正确：* [一本很有用的书 (1970)](https://example.org/book.html) - 张显宗
    ```

* <a id="in_process"></a>编写(翻译)中的书籍：

    ```text
    正确：* [马上出版的一本书](http://example.com/book2.html) - 张显宗 (HTML) (:construction: *编写中*)
    正确：* [马上出版的一本书](http://example.com/book2.html) - 张显宗 (HTML) (:construction: *翻译中*)
    ```

- <a id="archived"></a>Archived link:

    ```text
    正确: * [A Way-backed Interesting Book](https://web.archive.org/web/20211016123456/http://example.com/) - John Doe (HTML) *(:card_file_box: archived)*
    ```

### 按字母順序

- 当有多个以相同字母开头的标题时，按第二个排序，依此类推。例如：“aa”位于 “ab” 之前
- “onetwo” 位于 “onetwo”之前

如果您看到错误的链接，请检查 linter 错误讯息以了解应该交换哪些行。


### 笔记

虽然基础知识相对简单，但我们列出的资源却多种多样。以下是关于我们如何处理这种多样性的一些说明。


#### 元數據

我們的清單提供了一組最小的元資料：標題、URL、創建者、平台和存取註釋。


##### 標題

- 沒有發明的標題。我們嘗試從資源本身取得標題；告誡撰稿人不要發明標題或在編輯中使用它們，如果可以避免的話。較舊的作品除外；如果它們主要具有歷史意義，標題後面括號中的年份可以幫助使用者知道它們是否感興趣。
- 沒有全大寫標題。通常標題大小寫是合適的，但如有疑問，請使用來源中的大寫
- 沒有表情符號。


##### 網址

- 我們不允許使用縮短的網址。
- 必須從網址中刪除追蹤程式碼。
- 國際網址應進行轉義。瀏覽器列通常會將這些內容呈現為 Unicode，但請使用複製和貼上。
- 安全性 (`https`) URL 始終優先於已實作 HTTPS 的非安全性 (`http`)網址。
- 我們不喜歡網址指向不託管所列資源的網頁，而是指向其他地方。


##### 創作者

- 我們希望在適當的情況下讚揚免費資源的創建者，包括翻譯人員！
- 翻譯作品，應註明原作者。我們建議使用 [MARC relators](https://loc.gov/marc/relators/relaterm.html) 來表彰作者以外的創作者，如下例所示：

    ```markdown
    * [一本翻譯書](http://example.com/book-zh.html) - John Doe，`trl.:` 翻譯者麥克
    ```
   這裡，註解「trl.:」使用「翻譯器」的 MARC 相關程式碼。
- 使用逗號「,」來分隔作者清單中的每個項目。
- 您可以使用「`et al.`」來縮短作者清單。
- 我們不允許創作者連結。
- 對於編譯或混音作品，「創作者」可能需要描述。例如，「Go​​alKicker」或「RIP Tutorial」書籍被標記為「`Compiled from StackOverflow Documentation`」。


##### 平台及接入註意事項

- 培訓班。特別是對於我們的課程清單來說，平台是資源描述的重要組成部分。這是因為課程平台具有不同的可供性和可訪問性模式。雖然我們通常不會列出需要註冊的書籍，但許多課程平台都有一些功能，如果沒有某種帳戶就無法使用。範例課程平台包括 Coursera、EdX、Udacity 和 Udemy。當課程依賴平台時，平台名稱應列在括號中。
- Youtube.我們有許多包含 YouTube 播放清單的課程。我們不會將 YouTube 列為平台，而是嘗試列出 YouTube 創作者，這通常是一個子平台。
- YouTube影片。我們通常不會連結到單一 YouTube 視頻，除非它們的長度超過一個小時並且結構類似於課程或教程。
- Leanpub。 Leanpub 託管具有多種存取模式的書籍。有時一本書無需註冊即可閱讀；有時一本書需要 Leanpub 帳戶才能免費存取。考慮到書籍的品質以及 Leanpub 存取模型的混合性和流動性，我們允許使用存取註釋「*（Leanpub 帳戶或請求的有效電子郵件）*」列出後者。

#### 流派

決定資源屬於哪個清單的第一條規則是查看資源如何描述自己。如果它稱自己為一本書，那麼也許它就是一本書。


##### 我們未列出的流派

由於互聯網非常龐大，因此我們不將以下內容包括在列表中：

- 部落格
- 部落格文章
- 文章
- 網站（那些託管我們列出的大量項目的網站除外）。
- 不是課程或截圖影片的影片。
- 書籍章節
- 書中的預告片樣本
- IRC 或 Telegram 頻道
- Slack或郵件列表

我們的競爭性節目清單對這些例外情況沒有那麼嚴格。 repo的範圍由社區決定；如果您想建議更改或新增範圍，請使用問題提出建議。


##### 書籍與其他東西

我們對書本性並不那麼挑剔。以下是一些表示資源是一本書的屬性：

- 它有一個 ISBN（國際標準書號）
- 它有一個目錄
- 提供可下載版本，尤其是 ePub 檔案。
- 它有版本
- 它不依賴互動內容或視頻
- 它試圖全面涵蓋一個主題
- 它是獨立的

我們列出的許多書籍不具備這些屬性；這可能取決於上下文。


##### Books vs. Courses

Sometimes these can be hard to distinguish!

Courses often have associated textbooks, which we would list in our books lists. Courses have lectures, exercises, tests, notes or other didactic aids. A single lecture or video by itself is not a course. A powerpoint is not a course.


##### Interactive Tutorials vs. Other stuff

If you can print it out and retain its essence, it's not an Interactive Tutorial.


### Automation

- Formatting rules enforcement is automated via [GitHub Actions](https://github.com/features/actions) using [fpb-lint](https://github.com/vhf/free-programming-books-lint) (see [`.github/workflows/fpb-lint.yml`](../.github/workflows/fpb-lint.yml))
- URL validation uses [awesome_bot](https://github.com/dkhamsing/awesome_bot)
- To trigger URL validation, push a commit that includes a commit message containing `check_urls=file_to_check`:

    ```properties
    check_urls=free-programming-books.md free-programming-books-zh.md
    ```

- You may specify more than one file to check, using a single space to separate each entry.
- If you specify more than one file, results of the build are based on the result of the last file checked. You should be aware that you may get passing green builds due to this so be sure to inspect the build log at the end of the Pull Request by clicking on "Show all checks" -> "Details".
