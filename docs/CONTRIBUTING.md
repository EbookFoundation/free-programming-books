*[Read this in other languages](README.md#translations)*

## Contributor License Agreement

By contributing, you agree to the [LICENSE](../LICENSE) of this repository.

## Contributor Code of Conduct

By contributing, you agree to respect the [Code of Conduct](CODE_OF_CONDUCT.md) of this repository. ([translations](README.md#translations))

## In a nutshell

1. "A link to easily download a book" is not always a link to a *free* book. Please only contribute free content. Make sure it's free. We do not accept links to pages that *require* working email addresses to obtain books, but we welcome listings that request them.

2. You don't have to know Git: if you found something of interest which is *not already in this repo*, please open an [Issue](https://github.com/EbookFoundation/free-programming-books/issues) with your links propositions.
   - If you know Git, please Fork the repo and send Pull Requests (PR).

3. We have 6 kinds of lists. Choose the right one:
   - *Books* : PDF, HTML, ePub, a gitbook.io based site, a Git repo, etc.
   - *Courses* : A course is a learning material which is not a book. [This is a course](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
   - *Interactive Tutorials* : An interactive website which lets the user type code or commands and evaluates the result (by "evaluate" we don't mean "grade"). e.g.: [Try Haskell](http://tryhaskell.org), [Try Git](https://learngitbranching.js.org).
   - *Playgrounds* : are online and interactive websites, games or desktop software for learning programming. Write, compile (or run), and share code snippets. Playgrounds often allow you to fork and get your hands dirty by playing with code.
   - *Podcasts and Screencasts* : Podcasts and screencasts.
   - *Problem Sets & Competitive Programming* : A website or software which lets you assess your programming skills by solving simple or complex problems, with or without code review, with or without comparing the results with other users.

4. Make sure to follow the [guidelines below](#guidelines) and respect the [Markdown formatting](#formatting) of the files.

## Guidelines

- Make sure your are not duplicating content
- HTTP links should be HTTPS when possible
- Secure (`https`) URLs are always preferred over non-secure (`http`) URLs where HTTPS has been implemented.
- in case of doubt, HTTPS links: <https://www.eff.org/https-everywhere> is a reliable ressource
- We only accept CC licensed books; make sure that it is CC licensed if you add a book.
  - Creative Commons licenses are not all the same, please be careful. We prefer licenses that grant permission for commercial use.
  - We also accept Public Domain licenses
  - **And what about other licenses?** See below:

### License specifier `(cc) free`

The books list specifies a license via a license specifier.

1. `(cc-by)` Creative Commons: Attribution
2. `(cc-by-sa)` Creative Commons: Attribution-ShareAlike
3. `(cc-by-nc-sa)` Creative Commons: Attribution-NonCommercial-ShareAlike
4. `(cc-by-nd)` Creative Commons: Attribution-NoDerivs
5. `(cc-by-nc)` Creative Commons: Attribution-NonCommercial
6. `(cc0)` Public Domain
7. `(PD)` Public Domain
8. `(all rights reserved - free to read online)` - when ASIN is provided - ASIN is needed for book identification in the book store by the crawler, even if the book itself is not available.
9. `(GFDL)` 'GNU Free Documentation License'
   - Some books in our list under (GFDL) might have the 'GNU Free Documentation License' term; we're cleaning this up gradually using this guideline

**IMPORTANT**: We do not accept content with only book identification and no license.

## Guidelines for Lists

- Ensure no duplicates
- Alphabetical order – check the A-Z
- Format each entry like this:

        * [Book Name](book_url) - Author Name, ..., Author Name - (CC) License

_Please note that we've made significant efforts to notice entries that are not properly formated are not added. If your PR gets rejected, it might be a matter of formatting._

### FORMATTING

- Check the list is ordered alphabetically by title from A→Z or Z→A
- The list must be in Markdown format. View source for formatting
- All entries must end with a period (.)
- No ALLCAPS titles. Usually title case is appropriate, but when in doubt use the capitalization from the source.
- All links in the lists must be working.
- Make sure to check all links using the integrated link validation tool (details below).

#### Link validation

Link validation is done by automated CI (GitHub Actions / Checks) tool called `check-urls`.

You can also check links manually by looking at the files.

##### Check all links in all files

If you specify more than one file, results of the build are based on the result of the last file checked. You should be aware that you may get passing green builds due to this so be sure to inspect the build log at the end of the Pull Request by clicking on "Show all checks" -> "Details".

### Fixing RTL/LTR linter errors

If you run the RTL/LTR Markdown Linter (on `*-ar.md`, `*-he.md`, `*-fa_IR.md`, `*-ur.md` files) and see errors or warnings:
- **LTR words** (e.g. "HTML", "JavaScript") in RTL text: append `‏` immediately after each LTR segment;
- **LTR symbols** (e.g. "C#", "C++"): append `‎` immediately after each LTR symbol;

#### Examples

**BAD**
```html
<div dir="rtl" markdown="1">
* [كتاب الأمثلة في R](URL) - John Doe (PDF)
</div>
```

**GOOD**
```html
<div dir="rtl" markdown="1">
* [كتاب الأمثلة في R‏](URL) - John Doe‏ (PDF)
</div>
```

---

**BAD**
```html
<div dir="rtl" markdown="1">
* [Tech Podcast - بودكاست المثال](URL) – Ahmad Hasan, محمد علي
</div>
```

**GOOD**
```html
<div dir="rtl" markdown="1">
* [Tech Podcast - بودكاست المثال](URL) – Ahmad Hasan,‏ محمد علي
</div>
```

---

**BAD**
```html
<div dir="rtl" markdown="1">
* [أساسيات C#](URL)
</div>
```

**GOOD**
```html
<div dir="rtl" markdown="1">
* [أساسيات C#‎](URL)
</div>
```
