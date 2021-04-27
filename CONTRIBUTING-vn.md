*Đọc bằng ngôn ngữ khác: [English](CONTRIBUTING.md)、[简体中文](CONTRIBUTING-zh.md)、[繁體中文](CONTRIBUTING-zh-TW.md)、[فارسی](CONTRIBUTING-fa_IR.md).*

## Giấy Phép Thỏa Thuận Cộng Tác Viên
Bằng cách đóng góp, bạn đồng ý với [LICENSE (Giấy Phép)](https://github.com/EbookFoundation/free-programming-books/blob/master/LICENSE) của kho lưu trữ này.

## Quy Tắc Ứng Xử của Cộng Tác Viên
Bằng cách đóng góp, bạn đồng ý tôn trọng [Quy Tắc Ứng Xử](https://github.com/EbookFoundation/free-programming-books/blob/master/CODE_OF_CONDUCT.md) của kho lưu trữ này.

## Tóm Tắt
1. "Một đường dẫn để tải một cuốn sách" không có nghĩa nó là một cuốn sách *miễn phí*. Vui lòng chỉ đóng góp nội dung miễn phí. Đảm bảo rằng nó là miễn phí. Chúng tôi không chấp nhận các đường dẫn đến các trang có *yêu cầu* nhập địa chỉ email để nhận sách.
2. Bạn không cần phải biết về Git: nếu bạn tìm được thứ gì đó thú vị *và chưa có trong kho lưu trữ này*, vui lòng mở một [Issue](https://github.com/EbookFoundation/free-programming-books/issues) với các đề xuất mà bạn muốn đóng góp.
    - Nếu bạn biết Git, vui lòng Fork Repo và gửi Pull Requests.
3. Chúng tôi có 5 loại tài liệu, bạn có thể chọn một trong những cái dưới đây:

    - *Sách* : PDF, HTML, ePub, một trang web dựa trên gitbook.io, a Git repo, vv.
    - *Khóa Học* : Một khóa học là một tài liệu học tập, không phải là sách. [Đây là một khóa học](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *Hướng Dẫn Tương Tác* : Một trang web cho phép người dùng gõ Code và chạy chương trình dựa trên kết quả và đánh giá. Ví dụ: [Try Haskell](http://tryhaskell.org), [Try Github](http://try.github.io).
    - *Podcasts and Screencasts* : Podcasts và screencasts.
    - *Đặt Vấn Đề & Cuộc Thi Lập Trình* : Trang web hoặc phần mềm cho phép bạn đánh giá kỹ năng lập trình của mình bằng cách giải quyết các vấn đề đơn giản hoặc phức tạp, có hoặc không có đánh giá Code, có hoặc không so sánh kết quả với những người khác.

4. Đảm bảo tuân thủ theo [những nguyên tắc bên dưới](#guidelines) và tôn trọng những [định dạng Markdown](#formatting) của files.

5. Travis CI sẽ chạy các test để đảm bảo danh sách của bạn được sắp xếp theo thứ tự bảng chữ cái và các quy tắc định dạng được tuân thủ. Đảm bảo kiểm tra xem các thay đổi của bạn có vượt qua bài test hay không.

### Những Nguyên Tắc
- đảm bảo rằng một cuốn sách là miễn phí. Kiểm tra kỹ nếu cần. Nó sẽ giúp ích cho các quản trị viên nếu bạn nhận xét trong phần PR về lý do tại sao bạn cho rằng cuốn sách là miễn phí.
- chúng tôi không chấp nhận các tệp được lưu trữ trên google drive, dropbox, mega, scribd, issu và các nền tảng tải lên tệp tương tự khác.
- chèn các đường dẫn của bạn theo thứ tự bảng chữ cái. Nếu bạn thấy một đường dẫn bị đặt sai vị trí, vui lòng sắp xếp lại nó và gửi một bài PR.
- sử dụng đường dẫn với nguồn có thẩm quyền nhất (có nghĩa là trang web của tác giả tốt hơn trang web của người biên tập tốt hơn trang web của bên thứ ba)
    + không có dịch vụ lưu trữ tệp (điều này bao gồm (nhưng không giới hạn) đường dẫn Dropbox và Google Drive)
- đường dẫn `https` tốt hơn đường dẫn `http` - miễn là chúng ở trên cùng một domain và phân phát cùng một nội dung.
- trên các miền gốc, bỏ dấu gạch chéo sau: `http://example.com` thay vì `http://example.com/`
- luôn thích đường dẫn ngắn: `http://example.com/dir/` tốt hơn là `http://example.com/dir/index.html`
    + không sử dụng rút gọn link
- thường thích những đường dẫn "mới nhất" hơn đường dẫn "phiên bản": `http://example.com/dir/book/current/` tốt hơn `http://example.com/dir/book/v1.0.0/index.html`
- if a link has an expired certificate/self-signed certificate/SSL issue of any other kind:
  1. *replace it* with its `http` counterpart if possible (because accepting exceptions can be complicated on mobile devices)
  2. *leave it* if no `http` version but link still accessible through `https` by adding an exception to the browser or ignoring the warning
  3. *remove it* otherwise
- if a link exists in multiple format, add a separate link with a note about each format
- if a resource exists at different places on the Internet
    + use the link with the most authoritative source (meaning author's website is better than editor's website is better than third party website)
    + if they link to different editions and you judge these editions are different enough to be worth keeping them, add a separate link with a note about each edition (see [Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353) to contribute to the discussion on formatting.)
- prefer atomic commits (one commit by addition/deletion/modification) over bigger commits. No need to squash your commits before submitting a PR. (We will never enforce this rule as it's just a matter of convenience for the maintainers)
- if the book is older, include the publication date with the title.
- include the author name or names where appropriate. You can shorten author lists with "et al."
- if the book is not finished, and is still being worked on, add the "in process" notation, as described [below.](#in_process)
- if an email address or account setup is requested before download is enabled, add language-appropriate notes in parentheses, e.g.: `(email address *requested*, not required)`

### Formatting
- All lists are `.md` files. Try to learn [Markdown](https://guides.github.com/features/mastering-markdown/) syntax. It's simple!
- All the lists start with an Index. The idea is to list and link all sections and subsections there. Keep it in alphabetical order.
- Sections are using level 3 headings (`###`), and subsections are level 4 headings (`####`).

The idea is to have
- `2` empty lines between last link and new section
- `1` empty line between heading & first link of its section
- `0` empty line between two links
- `1` empty line at the end of each `.md` file

Example:

    [...]
    * [An Awesome Book](http://example.com/example.html)
                                    (blank line)
                                    (blank line)
    ### Example
                                    (blank line)
    * [Another Awesome Book](http://example.com/book.html)
    * [Some Other Book](http://example.com/other.html)

- Don't put spaces between `]` and `(`:

```
BAD : * [Another Awesome Book] (http://example.com/book.html)
GOOD: * [Another Awesome Book](http://example.com/book.html)
```

- If you include the author, use ` - ` (a dash surrounded by single spaces):

```
BAD : * [Another Awesome Book](http://example.com/book.html)- John Doe
GOOD: * [Another Awesome Book](http://example.com/book.html) - John Doe
```

- Put a single space between the link and its format:

```
BAD : * [A Very Awesome Book](https://example.org/book.pdf)(PDF)
GOOD: * [A Very Awesome Book](https://example.org/book.pdf) (PDF)
```

- Author comes before format:

```
BAD : * [A Very Awesome Book](https://example.org/book.pdf)- (PDF) Jane Roe
GOOD: * [A Very Awesome Book](https://example.org/book.pdf) - Jane Roe (PDF)
```

- Multiple formats:

```
BAD : * [Another Awesome Book](http://example.com/)- John Doe (HTML)
BAD : * [Another Awesome Book](https://downloads.example.org/book.html)- John Doe (download site)
GOOD: * [Another Awesome Book](http://example.com/) - John Doe (HTML) [(PDF, EPUB)](https://downloads.example.org/book.html)
```

- Include publication year in title for older books:

```
BAD : * [A Very Awesome Book](https://example.org/book.html) - Jane Roe - 1970
GOOD: * [A Very Awesome Book (1970)](https://example.org/book.html) - Jane Roe
```

<a name="in_process"></a>
- In-process books:

```
GOOD: * [Will Be Awesome Soon Book](http://example.com/book2.html) - John Doe (HTML) (:construction: *in process*)
```

### Notes

While the basics are relatively simple, there is a great diversity in the resources we list. Here are some notes on how we deal with this diversity.

#### Metadata

Our lists provide a minimal set of metadata: titles, URLs, creators, platforms, and access notes.

##### Titles

- No invented titles. We try to take titles from the resources themselves; contributors are admonished not to invent titles or use them editorially if this can be avoided. An exception is for older works; if they are primarily of historical interest, a year in parentheses appended to the title helps users know if they are of interest.
- No ALLCAPS titles. Usually title case is appropriate, but when doubt use the captitalization from the source

##### URLs

- We don't permit shortened URLs.
- Tracking codes must be removed from the URL.
- International URLs should be escaped. Browser bars typically render these to Unicode, but use copy and paste, please.
- Secure (https) URLs are always preferred over non-secure (http) urls where https has been implemented.
- We don't like URLs that point to webpages that don't host the listed resource, but instead point elsewhere.

##### Creators

- We want to credit the creators of free resources where appropriate, including translators!
- For translated works the original author should be credited.
- We do not permit links for Creators.
- For compilation or remixed works, the "creator" may need a description. For example, "GoalKicker" books are credited as "Compiled from StackOverflow documentation"

##### Platforms and Access Notes

- Courses. Especially for our course lists, the platform is an important part of the resource description. This is because course platforms have different affordances and access models. While we usually won't list a book that requires a registration, many course platforms have affordances that don't work without some sort of account. Example course platforms include Coursera, EdX, Udacity , and Udemy. When a course depends on a platform, the platform name should be listed in parentheses.
- YouTube. We have many courses which consist of YouTube playlists. We do not list Youtube as a platform, we try to list the Youtube creator, which is often a sub-platform.
- YouTube videos. We usually don't link to individual YouTube videos unless they are more than an hour long and are structured like a course or a tutorial.
- Leanpub. Leanpub hosts books with a variety of access models. Sometimes a book can be read without registration; sometimes a book requires a Leanpub account for free access. Given quality of the books and the mixture and fluidity of Leanpub access models, we permit listing of the latter with the access note *(Leanpub account or valid email requested)*

#### Genres

The first rule in deciding which list a resource belongs in is to see how the resource describes itself. If it calls itself a book, then maybe it's a book.

##### Genres we don't list

Because the Internet is vast, we don't include in our lists:

- blogs
- blog posts
- articles
- websites (except for those that host LOTS of items that we list.)
- videos that aren't courses or screencasts.
- book chapters
- teaser samples from books
- IRC or Telegram channels
- Slacks or mailing lists

Our competitive programming lists are not as strict about these exclusions. The scope of the repo is determined by the community; if you want to suggest a change or addition to the scope, please use an issue to make the suggestion.


##### Books vs. Other Stuff

We're not that fussy about book-ness. Here are some attributes that signify that a resource is a book:

- it has an ISBN
- it has a Table of Contents
- a downloaded version, especially ePub, is offered
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

- Formatting rules enforcement is automated via [Travis CI](https://travis-ci.com) using [fpb-lint](https://github.com/vhf/free-programming-books-lint) (see [.travis.yml](.travis.yml))
- URL validation uses [awesome_bot](https://github.com/dkhamsing/awesome_bot)
- To trigger URL validation, push a commit that includes a commit message containing `check_urls=file_to_check`:

```
check_urls=free-programming-books.md free-programming-books-en.md
```

- You may specify more than one file to check, using a single space to separate each entry.
- If you specify more than one file, results of the build is based on the result of the last file checked. You should be aware that you may get passing green builds due to this so be sure to inspect the build log at the end of the pull request by clicking on "Show all checks" -> "Details".
