*이 문서르 다른 언어로 보시려면: [Deutsch](CONTRIBUTING-de.md), [Français](CONTRIBUTING-fr.md), [Español](CONTRIBUTING-es.md), [Indonesia](CONTRIBUTING-id.md),[简体中文](CONTRIBUTING-zh.md), [English](CONTRIBUTING.md), [فارسی](CONTRIBUTING-fa_IR.md), [Tiếng Việt](CONTRIBUTING-vn.md), [Русский](CONTRIBUTING-ru.md).*

## 기여자 라이선스 동의서
이 프로젝트의 기여자들은 리포지토리의 [약관](https://github.com/EbookFoundation/free-programming-books/blob/master/LICENSE) 에 동의하는 것으로 간주됩니다.

## 기여자 행도 강령
이 리포지토리 기여함으로서, 모든 기여자는 이 [행동강령](https://github.com/EbookFoundation/free-programming-books/blob/master/CODE_OF_CONDUCT.md) 에 동의한 것으로 간주됩니다.

## 요약
1. "책을 쉽게 내려받을 수 있는 바로가기"는 해당 책이 무료임을 보장하지 않습니다. 이 프로젝트에 기여하기 전에 해당 바로가기가 무료임을 확인해 주십시오. 저희는 또한 작동하는 이메일을 요구하는 바로가기는 허용하지 않습니다만, 이메일을 요청하는 것들은 허용됩니다.
2. 깃에 대해 알고 있을 필요는 없습니다: 만약 당신이 조건에 부합하면서 이미 등재되지 않은 바로가기를 발견한다면, 새로운 바로가기와 함께 새로운 [이슈](https://github.com/EbookFoundation/free-programming-books/issues)를 열 수 있습니다.
    - 만약 깃 사용법으 알고 있다면, 해당 리포지토리를 Fork 하며 Pull request를 보내주세요.
3. 저희는 다섯 가지의 리스트를 제공하고 있습니다. 올바른 것을 선택해 주세요:
    - *책* : PDF, HTML, ePub, gitbook.io 기반 웹사이트, 깃 리포지토리, 등.
    - *강좌* : 여기서 강좌는 책이 아닌 교육 도구르 칭합니다. [강좌 예시](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *상호작용을 할 수 있는 강좌* : 사용자가 코드를 입력하거나 명령어를 입력하여 평가을 받을 수 있는 웹사이트를 칭합니다(평가는 채점이 아닙니다). 예시: [Try Haskell](http://tryhaskell.org), [Try Github](http://try.github.io).
    - *팟캐스트와 화면 녹화*
    - *문제집 & 경쟁 하며 배우느 프로그래밍* : 문제를 품으로서 프로그래밍 실력을 향상시키는데 도움을 주는 소프트웨어 또는 웹사이트를 칭합니다. 해당 소프트웨어 또는 웹사이트는 동료가 주체가 되는 코드 검토를 포함 할 수 있습니다.

4. 아래의 [가이드라인](#guidelines) 을 참조하고 [마크다운 규격](#formatting) 을 준수하여 주십시오.

5. 깃허브 액션이 각각의 리스트가 오름차순인지, 또하 규격이 준수되었는지 검수 할 것입니다. 각 제출이 검수를 통과하는지 확인해주십시오.

### 가이드라인
- 책이 무료인 반드시 확인 해 주십시오. 해당 책이 무료라고 생각하는 이유를 PR의 comment에 포함하는 것은 관리자들에게 큰 도움이 됩니다.
- 저희는 Google Drive, Dropbox, Mega, Scribd, Issuu 또는 유사한 파일 공유 시스템에 업로드된 파일들을 수락하지 않습니다.
- 바로가기를 오름차순으로 정렬해 주십시오. 만약 당신이 오름차순이 아닌 파일을 발견한다면, 수정후 PR을 보내주세요.
- 가능한 가장 원작자에 가까운 바로가기를 사용해주세요(작가의 웹사이트가 편집자의 웹사이트보다 낫고, 제 3자의 웹사이트보다는 편집자의 것이 낫습니다).
- 동일한 내용으 포함한다는 전 하에 `https` 주소를 `http`주소보다 우선시 해주십시오
- 루트 도메인을 사용할때는, 마지막에 붙는 /를 배제하여주십시오. (`http://example.com` <- `http://example.com/`)
- 모든 경우에 더 짧은 링크를 선호합니다: `http://example.com/dir/` 가 `http://example.com/dir/index.html`보다 낫지만, URL 단추 서비스를 사용하지 마십시오.
- 대부분의 경우에 버전이 명시된 웹사이트보다는 현행 버젼 웹사이트를 선호합니다 (`http://example.com/dir/book/current/` <- `http://example.com/dir/book/v1.0.0/index.html`)
- 만약 해당 바로가기의 인증서가 만료되었다면:
    1. `http` 형식으로 *대치 하십시오*
    2. `http` 버젼이 존재하지 않는다면, 기존의 링크를 사용하십시오. `https`형식또한 예외를 추가한다면 사용할 수 있습니다.
    3. 이외의 경우에 *제외하십시오*
- 만약 바로가기가 여러 형식으로 존재한다면, 각각을 쪽지와 함께 모두 첨부해주세요.
- 만약 자료가 여러 사이트에 분산되어 있다면, 가장 믿을 수 있는 바로가기를 첨부해주세요. 만약 각각의 바로가기가 다른 버젼으로 향한다면, 쪽지와 함께 모두 포함하십시오. (참고: [Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353) 해당문서는 규격에 대해 설명합니다.)
- 대량의 자료를 포함한 하나의 커밋보다는 작은 변화를 포함하는 여러개의 커밋이 선호됩니다.
- 만약 오래된 책이라면, 출판일을 제목과 함께 포함하세요.
- 작가(들)의 이름을 명시하십시오. "et al."을 사용하여 단축 할 수 있습니다.
- 만약 책이 아직 완결되지 않았다면, [아래](#in_process)에 명시되어 있다시피, "in progress" 표시를 추가하십시오.
- if the book is not finished, and is still being worked on, add the "in process" notation, as described [below.](#in_process)
- if an email address or account setup is requested before download is enabled, add language-appropriate notes in parentheses, e.g.: `(email address *requested*, not required)`

### Formatting
- All lists are `.md` files. Try to learn [Markdown](https://guides.github.com/features/mastering-markdown/) syntax. It's simple!
- All the lists start with an Index. The idea is to list and link all sections and subsections there. Keep it in alphabetical order.
- Sections are using level 3 headings (`###`), and subsections are level 4 headings (`####`).

반드시 포함하여야 하는 항목들:
- 마지막 바로가기와 새로운 섹션 사이의 줄바꿈 `2`회
- 머리말과 섹션의 첫 바로가기 사이의 줄바꿈 `1`회
- 두 바로가기 사이의 줄바꿈 `0`회
- `.md` 파일의 마지막에 `1`회의 줄바꿈

예시:

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
GOOD: * [Will Be An Awesome Book Soon](http://example.com/book2.html) - John Doe (HTML) (:construction: *in process*)
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

- Courses. Especially for our course lists, the platform is an important part of the resource description. This is because course platforms have different affordances and access models. While we usually won't list a book that requires a registration, many course platforms have affordances that don't work without some sort of account. Example course platforms include Coursera, EdX, Udacity, and Udemy. When a course depends on a platform, the platform name should be listed in parentheses.
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

- Formatting rules enforcement is automated via [GitHub Actions](https://github.com/features/actions) using [fpb-lint](https://github.com/vhf/free-programming-books-lint) (see [.github/workflows/fpb-lint.yml](.github/workflows/fpb-lint.yml))
- URL validation uses [awesome_bot](https://github.com/dkhamsing/awesome_bot)
- To trigger URL validation, push a commit that includes a commit message containing `check_urls=file_to_check`:

```
check_urls=free-programming-books.md free-programming-books-en.md
```

- You may specify more than one file to check, using a single space to separate each entry.
- If you specify more than one file, results of the build is based on the result of the last file checked. You should be aware that you may get passing green builds due to this so be sure to inspect the build log at the end of the pull request by clicking on "Show all checks" -> "Details".
