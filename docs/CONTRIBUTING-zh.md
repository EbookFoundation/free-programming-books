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

- 當有多個以相同字母開頭的標題時，按第二個排序，依此類推。例如：“aa”位於 “ab” 之前
- “onetwo” 位於 “onetwo”之前

如果您看到錯誤的鏈接，請檢查 linter 錯誤訊息以了解應該交換哪些行。


### 筆記

雖然基礎知識相對簡單，但我們列出的資源卻多種多樣。以下是關於我們如何處理這種多樣性的一些說明。


#### Metadata

Our lists provide a minimal set of metadata: titles, URLs, creators, platforms, and access notes.


##### Titles

- No invented titles. We try to take titles from the resources themselves; contributors are admonished not to invent titles or use them editorially if this can be avoided. An exception is for older works; if they are primarily of historical interest, a year in parentheses appended to the title helps users know if they are of interest.
- No ALLCAPS titles. Usually title case is appropriate, but when doubt use the capitalization from the source
- No emojis.


##### URLs

- We don't permit shortened URLs.
- Tracking codes must be removed from the URL.
- International URLs should be escaped. Browser bars typically render these to Unicode, but use copy and paste, please.
- Secure (`https`) URLs are always preferred over non-secure (`http`) urls where HTTPS has been implemented.
- We don't like URLs that point to webpages that don't host the listed resource, but instead point elsewhere.


##### Creators

- We want to credit the creators of free resources where appropriate, including translators!
- For translated works the original author should be credited. We recommend using [MARC relators](https://loc.gov/marc/relators/relaterm.html) to credit creators other than authors, as in this example:

    ```markdown
    * [A Translated Book](http://example.com/book-zh.html) - John Doe, `trl.:` Mike The Translator
    ```

    here, the annotation `trl.:` uses the MARC relator code for "translator".
- Use a comma `,` to delimit each item in the author list.
- You can shorten author lists with "`et al.`".
- We do not permit links for Creators.
- For compilation or remixed works, the "creator" may need a description. For example, "GoalKicker" or "RIP Tutorial" books are credited as "`Compiled from StackOverflow documentation`".


##### Platforms and Access Notes

- Courses. Especially for our course lists, the platform is an important part of the resource description. This is because course platforms have different affordances and access models. While we usually won't list a book that requires a registration, many course platforms have affordances that don't work without some sort of account. Example course platforms include Coursera, EdX, Udacity, and Udemy. When a course depends on a platform, the platform name should be listed in parentheses.
- YouTube. We have many courses which consist of YouTube playlists. We do not list YouTube as a platform, we try to list the YouTube creator, which is often a sub-platform.
- YouTube videos. We usually don't link to individual YouTube videos unless they are more than an hour long and are structured like a course or a tutorial.
- Leanpub. Leanpub hosts books with a variety of access models. Sometimes a book can be read without registration; sometimes a book requires a Leanpub account for free access. Given quality of the books and the mixture and fluidity of Leanpub access models, we permit listing of the latter with the access note `*(Leanpub account or valid email requested)*`.


#### Genres

The first rule in deciding which list a resource belongs in is to see how the resource describes itself. If it calls itself a book, then maybe it's a book.


##### Genres we don't list

Because the Internet is vast, we don't include in our lists:

- blogs
- blog posts
- articles
- websites (except for those that host LOTS of items that we list).
- videos that aren't courses or screencasts.
- book chapters
- teaser samples from books
- IRC or Telegram channels
- Slacks or mailing lists

Our competitive programming lists are not as strict about these exclusions. The scope of the repo is determined by the community; if you want to suggest a change or addition to the scope, please use an issue to make the suggestion.


##### Books vs. Other Stuff

We're not that fussy about book-ness. Here are some attributes that signify that a resource is a book:

- it has an ISBN (International Standard Book Number)
- it has a Table of Contents
- a downloadable version is offered, especially ePub files.
- it has editions
- it doesn't depend on interactive content or videos
- it tries to comprehensively cover a topic
- it's self-contained

There are lots of books that we list that don't have these attributes; it can depend on context.


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
