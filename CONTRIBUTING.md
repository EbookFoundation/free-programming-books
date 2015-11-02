## Contributor license agreement
By contributing you agree to the [LICENSE](https://github.com/vhf/free-programming-books/blob/master/LICENSE) of this repository.

## Free, Git, and Files
1. First of all, what you want to add should be free. Don't confuse "an easy link to download a book" with "a free book".
2. If you don't know how to work with git or github, simply refer to our wiki [Contribution](https://github.com/vhf/free-programming-books/wiki/Contribution).
3. We have 5 kinds of lists. Choose the right one:
    
    - **Books** : PDF, HTML, ePub, a gitbook.io based site, a Git repo, etc.
    - **Courses** : A course is a learning material which is not a book and where there is no interactive tool embeded in the site. [This is a course](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - **Interactive Tutorials** : An interactive website which lets the user type code or commands and evaluates the result (by "evaluate" we don't mean "grade"). e.g.: [Try Haskell](http://tryhaskell.org), [Try Github](http://try.github.io).
    - **JavaScript Resources** : Any resources teaching a JavaScript framework or library.
    - **Problem Sets & Competitive Programming** : A website or software which lets you assess your programming skills by solving simple or complex problems, with or without code review, with or without comparing the results with other users.

4. Make sure to correctly [format](#formatting) your modifications.
5. Read the guidelines below:

### Actual guidelines
- make sure a book is free. Double-check if needed.
- insert your links in alphabetical order. If you see a misplaced link, please reorder it and submit a PR
- use the link with the most authoritative source (meaning author's website is better than editor's website is better than third party website)
    + no file hosting services (this includes Dropbox and Google Drive links)
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
    + if they link to different editions and you judge these editions are different enough to be worth keeping them, add a separate link with a note about each edition
- prefer atomic commits (one commit by addition/deletion/modification) over bigger commits. No need to squash your commits before submitting a PR. (We will never enforce this rule as it's just a matter of convenience for the maintainers)

### Formatting
- All lists are `.md` files. Try to learn Github's Markdown syntax. It's simple!
- All the lists start with an Index. The idea is to list and link all sections and subsections there. Keep it in alphabetical order.
- Sections are using level 3 headings (`###`), and subsections are level 4 headings (`####`).

The idea is to have
- `2` empty lines between last link and new section
- `1` empty line between heading & first link of its section
- `0` empty line between two links
- `1` empty line at the end of each `.md` file

Example:

    [...]
    - [Essential Pascal Version 1 and 2](http://www.marcocantu.com/epascal/)


    ### DTrace

    - [IllumOS Dynamic Tracing Guide](http://dtrace.org/guide/preface.html)
    - [Some Other Book](http://so.me/other/book.html)

- Don't put spaces between `]` and `(`

    BAD : * [IllumOS Dynamic Tracing Guide] (http://dtrace.org/guide/preface.html)(PDF)
    GOOD: * [IllumOS Dynamic Tracing Guide](http://dtrace.org/guide/preface.html) (PDF)

- Put a single space between the link and its format

    BAD : * [IllumOS Dynamic Tracing Guide](http://dtrace.org/guide/preface.html)(PDF)
    GOOD: * [IllumOS Dynamic Tracing Guide](http://dtrace.org/guide/preface.html) (PDF)

- If you wish to mention the author, use ` - ` (a dash surrounded by single spaces)

    BAD : * [IllumOS Dynamic Tracing Guide](http://dtrace.org/guide/preface.html)- Robert
    GOOD: * [IllumOS Dynamic Tracing Guide](http://dtrace.org/guide/preface.html) - Robert
