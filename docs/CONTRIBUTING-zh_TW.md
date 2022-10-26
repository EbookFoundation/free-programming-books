*[閱讀其他語言版本的文件](README.md#nslations)*


## 貢獻者許可協議

請遵循此 [許可協議](../LICENSE) 參與貢獻。


## 貢獻者行為準則

請同意並遵循此 [行為準則](CODE_OF_CONDUCT.md) 參與貢獻。([translations](README.md#nslations))


## 概要

1. "一個可以輕易下載一本書的連結" 並不代表它導向的就是 *免費* 書籍。 請只提供免費內容。 確信你所提供的書籍是免費的。我們不接受導向 *需要* 工作電子郵件地址才能獲取書籍頁面的連結，但我們歡迎有需求這些連結的列表。

2. 你不需要會 Git：如果你發現了一些有趣的東西 *尚未出現在此 repo* 中，請開一個 [Issue](https://github.com/EbookFoundation/free-programming-books/issues) 進行主題討論。
    * 如果你已經知道 Git，請 Fork 此 repo 並提交 Pull Request (PR)。

3. 這裡有六種列表，請選擇正確的一項：

    * *Books* ：PDF、HTML、ePub、基於 gitbook.io 的網站、Git 的 repo 等。
    * *Courses* ：課程是一種學習素材，而不是一本書 [This is a course](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/)。
    * *Interactive Tutorials* ：一個互動式網站，允許用戶輸入程式碼或指令並執行結果。例如：[Try Haskell](http://tryhaskell.org)，[Try GitHub](http://try.github.io)。
    * *Playgrounds* : Playgrounds 是學習程式設計的線上互動式網站、遊戲或桌面軟體。你可以在上面編寫、編譯、運行或分享程式碼片段。 Playgrounds 通常允許你 fork 程式碼然後在其中盡情的編寫程式碼。
    * *Podcasts and Screencasts* ：Podcast 和影音。
    * *Problem Sets & Competitive Programming* ：一個網站或軟體，讓你透過解決簡單或複雜的問題來評估你的程式技能，可能有程式碼檢查，或與其他用戶比對结果。

4. 確保遵循下方的 [基本準則](#基本準則)，並遵循此 repo 文件的 [Markdown 規定格式](#規定格式)。

5. GitHub Actions 將運行測試，以確保你的列表是 **按字母顺序排列** 的，並 **遵循格式化規則**。請 **確保** 你的更改通過該測試。


### 基本準則

* 確保你提交的每一本書都是免費的。如有需要請 Double-check。如果你在 PR 中註明為什麼你認為這本書是免費的，這對管理員是很有幫助的。
* 我們不接受儲存在 Google Drive、Dropbox、Mega、Scribd、Issuu 和其他類似文件上傳平台上的文件。
* 請按照字母順序插入連結, 如 [下方敘述](#alphabetical-order).
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
- if a resource is restored using the [*Internet Archive's Wayback Machine*](https://web.archive.org) (or similar), add the "`archived`" notation, as described [below](#archived). The best versions to use are recent and complete.
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
    正確：* [即將出版的一本書](http://example.com/book2.html) - 張顯宗 (HTML) (:construction: *編寫中*)
    正確：* [即將出版的一本書](http://example.com/book2.html) - 張顯宗 (HTML) (:construction: *翻譯中*)
    ```

- <a id="archived"></a>Archived link:

    ```text
    正確: * [A Way-backed Interesting Book](https://web.archive.org/web/20211016123456/http://example.com/) - John Doe (HTML) *(:card_file_box: archived)*
    ```

<!----><a id="alphabetical-order"></a>
### 依照字母排序

- 當出現多個相同字母開頭的標題時，則照第二個字母排序，以此類推。例如：`aa` 排在 `ab` 前面
- `one two` 排在 `onetwo` 前面

如果你看到錯誤的連結，請檢查 linter 的錯誤訊息來找到哪一行順序需要交換


### Notes

While the basics are relatively simple, there is a great diversity in the resources we list. Here are some notes on how we deal with this diversity.


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

- 規定格式驗證是由 [GitHub Actions](https://docs.github.com/en/actions) 自動化進行，使用 [fpb-lint](https://github.com/vhf/free-programming-books-lint) 套件 (參閱 [`.github/workflows/fpb-lint.yml`](../.github/workflows/fpb-lint.yml))。
- 使用 [awesome_bot](https://github.com/dkhamsing/awesome_bot) 進行連結驗證。
- 可以藉由提交一個內容包含`check_urls=file_to_check`來觸發連結驗證:

    ```properties
    check_urls=free-programming-books.md free-programming-books-zh.md
    ```

- 您可以以一個空白區隔出想要進行驗證的檔案名稱來一次驗證多個檔案。
- 如果您一次驗證多個檔案，自動化測試的結果會是基於最後一個驗證的檔案。您的測試可能會因此通過，因此請詳加確認測試日誌。可以在 Pull Request 結果中點選"Show all checks" -> "Details" 來查看。
