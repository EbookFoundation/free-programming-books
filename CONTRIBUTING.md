## Contributor License Agreement
By contributing you agree to the [LICENSE](https://github.com/EbookFoundation/free-programming-books/blob/master/LICENSE) of this repository.

## Contributor Code of Conduct
By contributing you agree to respect the [Code of Conduct](https://github.com/EbookFoundation/free-programming-books/blob/master/CODE_OF_CONDUCT.md) of this repository.

## In a nutshell
1. "A link to easily download a book" is not always a link to a *free* book. Please only contribute free content. Make sure it's free.
2. You don't have to know git: if you found something of interest which is *not already in this repo*, please open an issue with your links propositions.
    - If you know git, please fork the repo and send pull requests.
3. We have 5 kinds of lists. Choose the right one:

    - *Books* : PDF, HTML, ePub, a gitbook.io based site, a Git repo, etc.
    - *Courses* : A course is a learning material which is not a book and where there is no interactive tool embedded in the site. [This is a course](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *Interactive Tutorials* : An interactive website which lets the user type code or commands and evaluates the result (by "evaluate" we don't mean "grade"). e.g.: [Try Haskell](http://tryhaskell.org), [Try Github](http://try.github.io).
    - *JavaScript Resources* : Any resources teaching a JavaScript framework or library.
    - *Problem Sets & Competitive Programming* : A website or software which lets you assess your programming skills by solving simple or complex problems, with or without code review, with or without comparing the results with other users.

4. Make sure to follow the [guidelines below](#guidelines) and respect the [Markdown formatting](#formatting) of the files

5. Travis CI will run tests to make sure your lists are alphabetized and formatting rules are followed. Be sure to check that your changes pass the tests.

### Guidelines
- make sure a book is free. Double-check if needed. It helps the admins if you comment in the PR as to why you think the book is free.
- we don't accept files hosted on google drive, dropbox, mega, scribd, issuu and other similar file upload platforms
- insert your links in alphabetical order. If you see a misplaced link, please reorder it and submit a PR
- use the link with the most authoritative source (meaning author's website is better than editor's website is better than third party website)
    + no file hosting services (this includes (but is not limited to) Dropbox and Google Drive links)
- always prefer a `https` link over a `http` one -- as long as they are on the same domain and serve the same content
- on root domains, strip the trailing slash: `http://example.com` instead of `http://example.com/`
- always prefer the shortest link: `http://example.com/dir/` is better than `http://example.com/dir/index.html`
    + no URL shortener links
- usually prefer the "current" link over the "version" one: `http://example.com/dir/book/current/` is better than `http://example.com/dir/book/v1.0.0/index.html`
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

- Don't put spaces between `]` and `(`

```
BAD : * [Another Awesome Book] (http://example.com/book.html)
GOOD: * [Another Awesome Book](http://example.com/book.html)
```

- If you include the author, use ` - ` (a dash surrounded by single spaces)

```
BAD : * [Another Awesome Book](http://example.com/book.html)- John Doe
GOOD: * [Another Awesome Book](http://example.com/book.html) - John Doe
```

- Put a single space between the link and its format

```
BAD : * [A Very Awesome Book](https://example.org/book.pdf)(PDF)
GOOD: * [A Very Awesome Book](https://example.org/book.pdf) (PDF)
```

- Author comes before format:

```
BAD : * [A Very Awesome Book](https://example.org/book.pdf)- Jane Roe
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
BAD: * [A Very Awesome Book](https://example.org/book.html) - Jane Roe - 1970
GOOD: * [A Very Awesome Book (1970)](https://example.org/book.html) - Jane Roe
```

<a name="in_process"></a>
- In-process books 

```
GOOD: * [Will Be Awesome Soon Book](http://example.com/book2.html) - John Doe (HTML) (:construction: *in process*)
```
