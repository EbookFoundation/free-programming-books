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

### 按字母顺序

- 当有多个以相同字母开头的标题时，按第二个排序，依此类推。例如：“aa”位于 “ab” 之前
- “onetwo” 位于 “onetwo”之前

如果您看到错误的链接，请检查 linter 错误讯息以了解应该交换哪些行。


### 笔记

虽然基础知识相对简单，但我们列出的资源却多种多样。以下是关于我们如何处理这种多样性的一些说明。


#### 元数据

我们的清单提供了一组最小的元资料：标题、URL、创建者、平台和存取注释。


##### 标题

- 不要创作标题。我们尽量从资源本身获取标题；强烈建议贡献者不要创作标题，或者在可以避免的情况下不要编辑它们原始标题。对于较旧的作品有一个例外；如果它们主要具有历史价值，将年份括在标题后的括号内可以帮助用户了解它们是否有兴趣。
- 不要使用全大写标题。常规的标题大小写是合适的，但如有疑问，请使用来源的大小写格式。
- 不要使用表情符号


##### 网址

- 我们不允许使用短链。
- 必须从网址中删除追踪代码。
- 网址应该进行转义。浏览器地址栏的网址通常已被转义，可以去那里拷贝。
- 在支持 HTTPS 的网站，安全的（https）URL总是优于非安全的（http）URL。
- 我们不喜欢网址指向不托管所列资源的网页，而是指向其他地方。


##### 创作者

- 我们希望在适当的情况下赞扬免费资源的创建者，包括翻译人员！
- 翻译作品，应注明原作者。我们建议使用 [MARC relators](https://loc.gov/marc/relators/relaterm.html) 来表彰作者以外的创作者，如下例所示：

    ```markdown
    * [译作](http://example.com/book-zh.html) - John Doe，`trl.:` 译者麦克
    ```
    这里，注解「trl.:」使用「翻译器」的 MARC 相关程式码。
- 使用逗号「，」来分隔作者清单中的每个项目。
- 您可以使用「`et al.`」来缩短作者清单。
- 我们不允许为创作者提供链接。
- 对于编译或混音作品，「创作者」可能需要描述。例如，「Go​​alKicker」或「RIP Tutorial」书籍被标记为「`Compiled from StackOverflow Documentation`」。


##### 平台及接入注意事项

- 课程。尤其是对于我们的课程列表，平台是资源描述的重要部分。这是因为不同的课程平台有不同的功能和访问模型。尽管我们通常不会列出需要注册的书籍，但许多课程平台的功能在没有某种帐户的情况下无法工作。课程平台的例子包括 Coursera、EdX、Udacity 和 Udemy。当一个课程依赖于一个平台时，应在括号中列出平台名称。
- Youtube。我们有许多包含 YouTube 播放清单的课程。我们不会将 YouTube 列为平台，而是尝试列出 YouTube 创作者，这通常是一个子平台。
- YouTube 影片。我们通常不会链接到单一 YouTube 视频，除非它们的长度超过一个小时并且结构类似于课程或教程。
- Leanpub。Leanpub 托管具有多种存取模式的书籍。有时一本书无需注册即可阅读；有时一本书需要 Leanpub 帐户才能免费存取。考虑到书籍的品质以及 Leanpub 存取模型的混合性和流动性，我们允许使用存取注释「*（Leanpub 帐户或请求的有效电子邮件）*」列出后者。


#### 类型

决定资源属于哪个清单的第一条规则是查看资源如何描述自己。如果它称自己为一本书，那么也许它就是一本书。


##### 我们未列出的流派

由于互联网非常庞大，因此我们不将以下内容包括在列表中：

- 博客（博客网站）
- 博客文章
- 网站（那些托管我们列出的大量项目的网站除外）。
- 不属于课程或录屏的视频。
- 书籍章节
- 书籍的预览样章
- IRC 或 Telegram 频道
- Slack 或邮件列表

我们的竞争性节目清单对这些例外情况没有那么严格。 仓库的范围由社区决定；如果您想建议更改或新增范围，请使用 issue 提出建议


##### 书籍与其他东西

我们对书本性并不那么挑剔。以下是一些表示资源是一本书的属性：

- 它有一个 ISBN（国际标准书号）
- 它有一个目录
- 提供可下载版本，尤其是 ePub 档案。
- 它有版本
- 它不依赖互动内容或视频
- 它试图全面涵盖一个主题
- 它是独立的

我们列出的许多书籍不具备这些属性；这可能取决于上下文。


##### 书与课程

有时这些可能很难区分！

课程通常有相关的教科书，我们会将其列在图书列表中。课程包括讲座、练习、测试、笔记或其他教学辅助工具。单个讲座或视频本身并不是一门课程。PowerPoint不是课程。


##### 交互式教程与其他东西

如果您可以将其打印出来并保留其精髓，那么它就不是交互式教程。


### 自动化

- 格式化规则的执行是通过以下方式自动执行的 [GitHub Actions](https://github.com/features/actions) 用 [fpb-lint](https://github.com/vhf/free-programming-books-lint) (参见 [`.github/workflows/fpb-lint.yml`](../.github/workflows/fpb-lint.yml))
- URL 验证使用 [awesome_bot](https://github.com/dkhamsing/awesome_bot)
- 要触发 URL 验证，请推送包含以下内容的 commit message 的提交 `check_urls=file_to_check`:

    ```特性
    check_urls=free-programming-books.md free-programming-books-zh.md
    ```
    
- - 您可以指定多个要检查的文件，使用单个空格分隔每个条目。
- 如果您指定了多个文件，构建的结果将基于最后一个检查的文件的结果。您应该注意，由于这个原因，您可能会得到通过的绿色构建，所以请确保在拉取请求结束时检查构建日志，点击 “Show all checks”->“Details”。
