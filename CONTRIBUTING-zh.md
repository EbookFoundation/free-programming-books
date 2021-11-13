*阅读本文的其他语言版本：[Deutsch](CONTRIBUTING-de.md), [English](CONTRIBUTING.md), [Français](CONTRIBUTING-fr.md), [Español](CONTRIBUTING-es.md), [繁體中文](CONTRIBUTING-zh_TW.md), [فارسی](CONTRIBUTING-fa_IR.md), [Tiếng Việt](CONTRIBUTING-vn.md), [Русский](CONTRIBUTING-ru.md), [Português Brasileiro](CONTRIBUTING-pt_BR.md), [한국어](CONTRIBUTING-ko.md).*


## 贡献者许可协议

请遵循此[许可协议](https://github.com/EbookFoundation/free-programming-books/blob/master/LICENSE)参与贡献。


## 贡献者行为准则

请同意并遵循此[行为准则](https://github.com/EbookFoundation/free-programming-books/blob/master/CODE_OF_CONDUCT.md)参与贡献。


## 概要

1. "一个可以轻易下载一本书的链接" 并不代表它指向的就是 *免费* 书籍。 请只提供免费内容。 确信你所提供的书籍是免费的。我们不接受指向*需要*工作电子邮件地址才能获取书籍的页面的链接，但我们欢迎有需求它们的列表。
2. 你不需要会 Git：如果你发现了一些有趣的东西 *尚未出现在本仓库* 中，请开一个[Issue](https://github.com/EbookFoundation/free-programming-books/issues)进行主题讨论。
    * 如果你已经知晓Git，请Fork本仓库并提交PR。
3. 这里有5种列表，请选择正确的一个：

    * *Books* ：PDF、HTML、ePub、基于一个 gitbook.io的站点、一个Git仓库等等。
    * *Courses* ：课程是一种学习材料，而不是一本书 [This is a course](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/)。
    * *Interactive Tutorials* ：一个交互式网站，它允许用户输入代码或命令并对结果进行评估。例如：[Try Haskell](http://tryhaskell.org)，[Try Github](http://try.github.io)。
    * *Podcasts and Screencasts* ：播客和视频。
    * *Problem Sets & Competitive Programming* ：一个网站或软件，让你通过解决简单或复杂的问题来评估你的编程技能，有或没有代码审查，有或没有与其他用户对比结果。

4. 确保遵循下面的[基本准则](#基本准则)，并遵循本仓库文件的[Markdown规定格式](#规定格式)。

5. Github Actions 将运行测试，以确保你的列表是 **按字母顺序排列** 的，并 **遵循格式化规则**。请 **确保** 你的更改通过了该测试。


### 基本准则

* 确保你提交的每一本书都是免费的。如有需要请做Double-check。如果你在PR中注明为什么你认为这本书是免费的，这将对管理员是很有帮助的。
* 我们不接受存储在Google Drive、Dropbox、Mega、Scribd、Issuu和其他类似文件上传平台上的文件。
* 请按照字母顺序插入链接。如果你看到一个错位的链接，请重新对他进行排序并提交一个PR。
* 使用最权威来源的链接(意思是原作者的网站比编辑的网站好，比第三方网站好)。
    * 没有文件托管服务(包括(但不限于)Dropbox和谷歌驱动器链接)。
* 优先选择使用 `https` 链接，而不是 `http` 链接 -- 只要它们位于相同的域并提供相同的内容。
* 在根域上，去掉末尾的斜杠：使用 `http://example.com` 代替 `http://example.com/`。
* 总是选择最短的链接：使用 `http://example.com/dir/` 比使用 `http://example.com/dir/index.html` 更好。
    * 不要提供短链接
* 优先选择使用 "current" 链接代替有 "version" 链接：使用 `http://example.com/dir/book/current/` 比使用 `http://example.com/dir/book/v1.0.0/index.html` 更好。
* 如果一个链接存在过期的证书/自签名证书/SSL问题的任何其他类型：
  1. *replace it* ：如果可能的话，将其 *替换* 为对应的`http`(因为在移动设备上接受异常可能比较复杂)。
  2. *leave it* ：如果没有http版本，但仍然可以通过https访问链接，则在浏览器中添加异常或忽略警告。
  3. *remove it* ：上述以外删除掉它。
* 如果一个链接以多种格式存在，请添加一个单独的链接，并注明每种格式。
* 如果一个资源存在于Internet上的不同位置
    * 使用最权威来源的链接(意思是原始作者的网站比编辑的网站好，比第三方网站好)。
    * 如果它们链接到不同的版本，你认为这些版本差异很大，值得保留，那么添加一个单独的链接，并对每个版本做一个说明(参见[Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353)有助于格式化问题的讨论)。
* 相较一个比较大的提交，我们更倾向于原子提交(通过添加/删除/修改进行一次提交)。在提交PR之前没有必要压缩你的提交。(我们永远不会执行这个规则，因为这只是维护人员的方便)。
* 如果一本书比较旧，请在书名中注明出版日期。
* 包含作者的名字或适当的名字。中文版本可以用 “等” 缩短作者列表。
* 如果一本书还没有完成，并且仍在编写中，则需添加 “编写中” 符号，参见[下文](#in_process)所述。
* 如果在开始下载之前需要电子邮件地址或帐户设置，请在括号中添加合适的语言描述，例如：`(*需要*电子邮件，但不是必须的)`。


### 规定格式

* 所有列表都是`.md`文件。试着学习[Markdown](https://guides.github.com/features/mastering-markdown/)语法。它很容易上手！
* 所有的列表都以索引开始。它的作用是列出并链接所有的sections(章节/段落)或subsections(子段落/子章节)。务必遵循字母顺序排列。
* Sections(章节/段落)使用3级标题(`###`)，subsections(子段落/子章节)使用4级标题 (`####`)。


#### 整体思想为：

* `2` ：新添加的Section与末尾链接间必须留有`2`个空行
* `1` ：标题和第一个链接之间必须留有`1`个空行的空行
* `0` ：任何两个链接之间不能留有任何空行
* `1` ：每个`.md`文件末尾必须留有`1`个空行


#### 举例：

```
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

```
错误：* [一本很有用的书] (http://example.com/book.html)
正确：* [一本很有用的书](http://example.com/book.html)
```

* 如果包括作者，请使用' - '(由单个空格(英文半角)包围的破折号)：

```
错误：* [一本很有用的书](http://example.com/book.html)- 张显宗
正确：* [一本很有用的书](http://example.com/book.html) - 张显宗
```

* 在链接和电子书格式之间放一个空格：

```
错误：* [一本很有用的书](https://example.org/book.pdf)(PDF)
正确：* [一本很有用的书](https://example.org/book.pdf) (PDF)
```

* 如需备注或注解，请使用英文半角括号`( )`：

```
错误：* [一本很有用的书](https://example.org/book.pdf) （繁体中文）
正确：* [一本很有用的书](https://example.org/book.pdf) (繁体中文)
```

* 作者在电子书格式之前：

```
错误：* [一本很有用的书](https://example.org/book.pdf)- (PDF) 张显宗
正确：* [一本很有用的书](https://example.org/book.pdf) - 张显宗 (PDF)
```

* 多重格式：

```
错误：* [一本很有用的书](http://example.com/)- 张显宗 (HTML)
错误：* [一本很有用的书](https://downloads.example.org/book.html)- 张显宗 (download site)
正确：* [一本很有用的书](http://example.com/) - 张显宗 (HTML) [(PDF, EPUB)](https://downloads.example.org/book.html)
```

* 多作者，多译者时，请使用中文 `、` 进行分隔，在译者名字后请使用英文半角括号包围的 `(翻译)`，可以用 “等” 缩短作者列表：

```
错误：* [一本很有用的书](https://example.org/book.pdf) - 张显宗，岳绮罗
正确：* [一本很有用的书](https://example.org/book.pdf) - 张显宗、岳绮罗(翻译)
正确：* [一本很有用的书](https://example.org/book.pdf) - 张显宗、岳绮罗、顾玄武、出尘子 等
```

* 在旧书的标题中包括出版年份：

```
错误：* [一本很有用的书](https://example.org/book.html) - 张显宗 - 1970
正确：* [一本很有用的书 (1970)](https://example.org/book.html) - 张显宗
```

<a name="in_process"></a>
* 编写(翻译)中的书籍：

```
正确：* [马上出版的一本书](http://example.com/book2.html) - 张显宗 (HTML) (:construction: *编写中*)
正确：* [马上出版的一本书](http://example.com/book2.html) - 张显宗 (HTML) (:construction: *翻译中*)
```
