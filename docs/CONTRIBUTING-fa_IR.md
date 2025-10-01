*[این متن را در زبان‌های دیگر بخوانید](README.md#translations)*


<div dir="rtl" markdown="1">

## توافقنامه‌ی مجوز همکاری

مشارکت در این مخزن به معنی موافقت شما با مجوز [LICENSE](../LICENSE) این مخزن است.


## مرام‌نامه‌ی همکار

مشارکت در این پروژه به معنی موافقت با احترام به [مرام‌نامه‌ی](CODE_OF_CONDUCT-fa_IR.md) این مخزن است. ([translations](README.md#translations))


## به طور خلاصه

1. "لینکی برای دانلود ساده‌ی یک کتاب" همیشه به معنی لینکی به یک کتاب *رایگان* نیست. لطفا فقط محتوای رایگان را قرار دهید. مطمئن شوید که این محتوا رایگان است. ما لینک‌هایی را که وارد کردن ایمیل کاری را برای دانلود کتاب *اجباری* کرده‌اند نمی‌پذیریم اما اگر بدون اجبار، این ایمیل را بخواهند، در این مخزن فهرستشان می‌کنیم.

2. نیاز نیست گیت بلد باشید: اگر چیز جذابی پیدا کردید که *در این مخزن وجود ندارد*، یک [Issue](https://github.com/EbookFoundation/free-programming-books/issues) با نوشتن لینک‌ها درست کنید.
    * اگر Git را می شناسید، لطفاً مخزن را Fork کنید و درخواست های کششی (PR) ارسال کنید.

3. ما شش نوع فهرست داریم. فهرست درست را انتخاب کنید:

    * *کتاب‌ها* : PDF، HTML، ePub، سایت بر اساس gitbook.io، یک مخزن گیت و غیره.
    * *دوره‌ها* : دوره محتوایی آموزشی است که کتاب نیست. مثلا [این یک دوره است](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    * *آموزش‌های تعاملی* : وبسایتی تعاملی که به کاربر اجازه‌ی تایپ کد یا دستور می‌دهد و نتیجه را ارزیابی می‌کند (منظور ما از "ارزیابی"، "نمره‌دهی" نیست). مثلا: [Try Haskell](http://tryhaskell.org), [Try GitHub](http://try.github.io).
    - *Playgrounds* : are online and interactive websites, games or desktop software for learning programming. Write, compile (or run), and share code snippets. Playgrounds often allow you to fork and get your hands dirty by playing with code.
    * *پادکست‌ها و اسکرین‌کست‌ها*
    * *مجموعه مشکلات و برنامه‌نویسی رقابتی* : وبسایت یا نرم‌افزاری که به شما امکان بررسی مهارت‌های برنامه‌نویسی را با کمک حل مشکلات ساده یا پیچیده، با یا بدون بررسی کد، با یا بدون مقایسه‌ی نتایج با کاربران دیگر می‌دهد.

4. مطمئن شوید که از [راهنماها](#guidelines) پیروی می‌کنید و طبق [فرمت‌بندی مارک‌داون](#formatting) می‌نویسید.

5. GitHub Actions تست‌هایی را اجرا می‌کند که مطمئن شود **فهرست شما الفبایی است** و **قوانین فرمت‌بندی رعایت شده است**. **مطمئن شوید که** تغییرات شما تست‌ها را با موفقیت گذرانده است.


<!----><a id="guidelines"></a>
### راهنماها

* مطمئن شوید که یک کتاب رایگان است. اگر لازم بود، دوباره هم بررسی کنید. اگر درباره‌ی علت این که فکر می‌کنید کتاب رایگان است در پول‌ریکوئست (PR)، کامنت بگذارید، به ادمین‌ها کمک کرده‌اید.
* ما فایل‌هایی را قبول نمی‌کنیم که روی گوگل‌درایو، دراپ‌باکس، مگا، اسکریبد، ایسیو یا پلتفرم‌های آپلود فایل مشابه قرار دارند
* لینک‌های خود را به ترتیب الفبایی وارد کنید, همان طور که در [زیر](#ترتیب-الفبایی) توضیح داده شده است.
* از لینک معتبرترین منبع استفاده کنید (این یعنی وبسایت نویسنده بهتر از وبسایت ویراستار و وبسایت ویراستار بهتر از وبسایت سوم شخص است)
    * از سرویس‌های اشتراک‌گذاری فایل استفاده نکنید (این سرویس‌ها شامل (و نه محدود به) لینک‌های دراپ‌باکس و گوگل‌درایو است)
* همیشه یک لینک `https` به یک لینک `http` ترجیح داده می‌شود -- تا وقتی که هر دو لینک دامنه‌ی یکسانی داشته باشند و محتوای یکسانی نمایش دهند.
* در دامنه‌های اصلی، از گذاشتن / خودداری کنید: `http://example.com` به جای `http://example.com/`
* همیشه کوتاه‌ترین لینک ترجیح داده می‌شود: `http://example.com/dir/` بهتر است از `http://example.com/dir/index.html`
    * از لینک‌های کوتاه‌ساز استفاده نکنید.
* معمولا لینک "فعلی" بهتر از لینک "نسخه‌ها" است: `http://example.com/dir/book/current/` بهتر است از `http://example.com/dir/book/v1.0.0/index.html`
* اگر لینکی مشکل certificate/self-signed certificate/SSL از هر نوع دیگری داشت:
    1. با همتای `http` همان لینک *جایگزینش کنید* (چون پذیرش استثناقائل شدن برای آن وبسایت در دستگاه‌های موبایل سخت است).
    2. اگر نسخه‌ی `http` ندارد اما همچنان با `https` و اضافه کردن استثناقائل‌شدن برای آن وبسایت در مرورگر یا نادیده گرفتن هشدار قابل دسترس است، *به همان حالت بگذاریدش*
    3. در غیر این صورت *حذفش کنید*
* اگر لینکی در چندین فرمت وجود داشت، لینکی جدا با یادداشتی درباره‌ی هر فرمت قرار دهید.
* اگر منبعی در جاهای دیگری از اینترنت وجود دارد
    * از لینک معتبرترین منبع استفاده کنید (این یعنی وبسایت نویسنده بهتر از وبسایت ویراستار و وبسایت ویراستار بهتر از وبسایت سوم شخص است)
    * اگر به ویرایش‌های مختلف لینک شده است و شما معتقدید این ویرایش‌ها به حد کافی متفاوت هستند که هر دو نگه داشته شوند، یک لینک جدا با یادداشتی درباره‌ی هر ویرایش بنویسید (برای مشارکت در فرمت‌بندی [Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353) را ببینید).
* کامیت‌های تکی (یک کامیت اضافه کردن/ حذف کردن/ تغییر دادن) بهتر از کامیت‌های بزرگ هستند. نیاز نیست کامیت‌های خود را قبل از ثبت یک پی‌آر خرد کنید (ما به دنبال اجباری کردن این قانون نیستیم چون این قانون فقط به خاطر راحتی نگه‌دارندگان مخزن است)
* اگر کتاب قدیمی است، تاریخ انتشار را در کنار عنوان بنویسید.
* نام نویسنده یا نویسندگان را در صورت امکان بنویسید. می‌توانید فهرست نویسندگان را با "و همکاران" (به انگلیسی: "`et al.`") کوتاه کنید.
* اگر کتاب هنوز تمام نشده است و هنوز روی آن کار می‌شود، عبارت "`in process`" را همان طور که در [پایین صفحه](#in_process) آمده به آن اضافه کنید.
- if a resource is restored using the [*Internet Archive's Wayback Machine*](https://web.archive.org) (or similar), add the "`archived`" notation, as described [below](#archived). The best versions to use are recent and complete.
* اگر پیش از دانلود، نشانی ایمیل یا ساخت حساب کاربری خواسته می‌شود، در پرانتز توضیح متناسبی بنویسید. مثلا: `(نشانی ایمیل *خواسته می‌شود* اما اجباری نیست)`.


<!----><a id="formatting"></a>
### فرمت‌بندی

* همه فهرست‌ها فایل‌های ".md" هستند. سعی کنید دستور زبان [Markdown](https://guides.github.com/features/mastering-markdown/) را یاد بگیرید. ساده است!
* همه فهرست‌ها با یک فهرست محتوایی شروع می‌شود. ایده این است که همه بخش‌ها و زیربخش‌ها در این فهرست محتوایی لیست و لینک شوند. این فهرست محتوایی را به ترتیب الفبایی قرار دهید.
* بخش‌ها از تیترهای سطح 3 (`###`) استفاده می‌کنند و زیربخش‌ها از تیترهای سطح 4 (`###`).

ایده این است که این موارد رعایت شوند:

* `2` خط خالی بین آخرین لینک و بخش جدید
* `1` خط خالی بین تیتر و لینک اول همان بخش
* `0` خط خالی بین دو لینک
* `1` خط خالی در آخر هر فایل `.md`

مثال:

```text
[...]
* [یک کتاب عالی](http://example.com/example.html)
                                (خط خالی)
                                (خط خالی)
### مثال
                                (خط خالی)
* [یک کتاب عالی دیگر](http://example.com/book.html)
* [یک کتاب دیگر](http://example.com/other.html)
```

* بین `]` و `(` space نگذارید:

    ```text
    بد : * [یک کتاب عالی دیگر] (http://example.com/book.html)
    خوب: * [یک کتاب عالی دیگر](http://example.com/book.html)
    ```

* اگر اسم نویسنده را اضافه می‌کنید، از ` - ` استفاده کنید (یک dash با دو single space):

    ```text
    بد : * [یک کتاب عالی دیگر](http://example.com/book.html)- نام نویسنده
    خوب: * [یک کتاب عالی دیگر](http://example.com/book.html) - نام نویسنده
    ```

* یک single space بین لینک و فرمت قرار دهید:

    ```text
    بد : * [یک کتاب خیلی عالی](https://example.org/book.pdf)(PDF)
    خوب: * [یک کتاب خیلی عالی](https://example.org/book.pdf) (PDF)
    ```

* نویسنده قبل از فرمت می‌آید:

    ```text
    بد : * [یک کتاب خیلی عالی](https://example.org/book.pdf)- (PDF) نام نویسنده
    خوب: * [یک کتاب خیلی عالی](https://example.org/book.pdf) - یک نویسنده دیگر (PDF)
    ```

* چند فرمتی‌ها:

    ```text
    بد : * [یک کتاب عالی دیگر](http://example.com/)- نام نویسنده (HTML)
    بد : * [یک کتاب عالی دیگر](https://downloads.example.org/book.html)- نام نویسنده (download site)
    خوب: * [یک کتاب عالی دیگر](http://example.com/) - نام نویسنده (HTML) [(PDF, EPUB)](https://downloads.example.org/book.html)
    ```

* سال انتشار برای کتاب‌های قدیمی را در عنوان ینویسید:

    ```text
    بد : * [یک کتاب خیلی عالی](https://example.org/book.html) - نام نویسنده - 1970
    خوب: * [یک کتاب خیلی عالی (1970)](https://example.org/book.html) - نام نویسنده
    ```

* <a id="in_process"></a>کتاب‌های در دست تالیف:

    ```text
    خوب: * [کتابی که عالی خواهدشد](http://example.com/book2.html) - نام نویسنده (HTML) *( :construction: in process)*
    ```

- <a id="archived"></a>Archived link:

    ```text
    خوب: * [A Way-backed Interesting Book](https://web.archive.org/web/20211016123456/http://example.com/) - John Doe (HTML) *( :card_file_box: archived)*
    ```

### ترتیب الفبایی

- وقتی چند عنوان با حرف یکسانی شروع می‌شوند، آنها را به ترتیب حرف دوم مرتب کنید و به همین ترتیب برای حرف‌های بعدی. مثلا `aa` قبل از `ab` می‌آید.
- همچنین `one two` قبل از `onetwo` می‌آید.

اگر لینکی را در جای نادرست دیدید، پیام خطای linter را ببینید تا بفهمید کدام خط‌ها باید جابجا شوند.


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
    * [A Translated Book](http://example.com/book-fa_IR.html) - John Doe, `trl.:` Mike The Translator
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


### خودکارسازی

* قوانین فرمت‌بندی از طریق [GitHub Actions](https://docs.github.com/en/actions) با استفاده از [fpb-lint](https://github.com/vhf/free-programming-books-lint) بررسی می‌شوند ([`.github/workflows/fpb-lint.yml`](../.github/workflows/fpb-lint.yml) را ببینید)
* اعتبارسنجی لینک‌ها با استفاده از [awesome_bot](https://github.com/dkhamsing/awesome_bot) انجام می‌شود.
* برای اجرای اعتبارسنجی لینک‌ها، کامیتی پوش کنید که در بدنه‌ی آن `check_urls=file_to_check` نوشته شده باشد:

    ```properties
    check_urls=free-programming-books.md free-programming-books-fa_IR.md
    ```

* با استفاده از single space برای جدا کردن هر ورودی، می‌توانید بیشتر از یک فایل را برای بررسی مشخص کنید.
* اگر بیش از یک فایل را مشخص کردید، نتایج بیلد بر اساس نتیجه آخرین فایل بررسی‌شده خواهد بود. دقت کنید که ممکن است به همین علت، نتیجه سبز را ببینید. پس برای اطمینان لاگ بیلد را با کلیک روی "Show all checks" -> "Details" در پایان پول ریکوئست (PR) ببینید.

</div>
