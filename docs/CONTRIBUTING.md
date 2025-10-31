# How to contribute to Free Programming Books

First off, thank you for considering contributing to Free Programming Books. It's people like you that make Free Programming Books such a great resource.

Following these guidelines helps to communicate that you respect the developers' time managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [admin@ebookfoundation.org](mailto:admin@ebookfoundation.org).

## What should I know before I get started?

Free Programming Books is an open source project – it's not a website or a web application. It's a collection of resources including documents, ebooks, and other learning materials compiled and organized in repositories.

### This community is built on these core principles:

- **Open and collaborative**: We respect all contributions from the community
- **No gatekeeping**: We try to keep the barrier to entry as low as possible
- **Non-commercial**: Free Programming Books does not exist to make money
- **Inclusive**: We do not discriminate based on experience, background, or identity

## How can I contribute?

You can contribute by:

- **Adding a book**: If you know of a free programming book, course, interactive tutorial, or other resource that is missing from our lists, please contribute it.
- **Improving documentation**: If you see errors in the documentation, unclear explanations, or missing information, please fix it.
- **Organizing and categorizing**: If you see that books aren't properly organized or categorized, please improve the organization.
- **Translating**: If you speak another language, you can help translate the documentation and lists into that language.
- **Reporting issues**: If you notice something wrong or think of a way to improve the project, please open an issue.

### Guidelines

1. Each list should be in a README file named after the category (e.g. `free-programming-books.md`).
2. Files should be organized into appropriate directories. Generally, a good set of directories is:
   - `books/` - for books
   - `courses/` - for courses
   - `interactive-tutorials/` - for interactive tutorials
   - `podcasts/` - for podcasts
   - `problem-sets-competitive-programming/` - for competitive programming resources
   - `programming-playgrounds/` - for programming playgrounds
3. Each entry must have:
   - A clear title
   - A link to the resource
   - The author name (if applicable)
   - The license type
4. Entries must be in alphabetical order by title (case insensitive)
5. Each entry must follow this format:

```
* [Book Title](http://example.com) - Author Name, Author Name - (CC License)
```

## What we're looking for

- We only accept **CC licensed** books; make sure that it is CC licensed if you add a book.
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

```
* [Book Name](book_url) - Author Name, ..., Author Name - (CC) License
```

_Please note that we've made significant efforts to notice entries that are not properly formatted are not added. If your PR gets rejected, it might be a matter of formatting._

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

```

**GOOD**

```html

```

---

**BAD**

```html

```

**GOOD**

```html

```

---

**BAD**

```html

```

**GOOD**

```html

```

## Pull Request Process

1. Fork the repository.
2. Create your feature branch (`git checkout -b my-new-feature`).
3. Make your changes.
4. Commit your changes (`git commit -am 'Add some feature'`).
5. Push to the branch (`git push origin my-new-feature`).
6. Create a new Pull Request.
7. Before you submit your PR, make sure your changes follow the project's style guidelines, especially where formatting and code style are concerned.
8. All pull requests must be signed off. The contributor must agree to the [Contributor License Agreement](../LICENSE) and [Code of Conduct](CODE_OF_CONDUCT.md).

## Resources

- [GitHub Help - Fork a Repository](https://help.github.com/articles/fork-a-repository/)
- [GitHub Help - Using Pull Requests](https://help.github.com/articles/about-pull-requests/)
- [GitHub Help - Merging a Pull Request](https://help.github.com/articles/merging-a-pull-request/)

Thanks for helping us improve!
