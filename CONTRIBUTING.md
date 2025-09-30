# Contributing to Free Programming Books

Thank you for your interest in contributing! 🎉 
This file explains how to properly add free programming books and resources to this repository.

---

## Contribution Workflow

1.  **Fork the repository, clone it locally, and create a new branch:**
    * Start by getting your local copy and creating a dedicated branch for your work.
    ```bash
    git clone git@github.com:YOUR-USERNAME/free-programming-books.git
    cd free-programming-books
    git checkout -b add-new-book
    ```

2.  **Add your contribution:**
    * Open the correct language or category file in the `books/` folder (e.g., `books/python.md`).
    * Add your new resource in **alphabetical order**.
    * Use the following Markdown format:
        * `[Book Title](http://link-to-book.com) - Author Name (Format) (License)`

    * Only add **free and legal** resources.
    * If you’re unsure whether a resource qualifies, open an **Issue** first.

3.  **Commit your changes:**
    * Save your work with a clear, descriptive message.
    ```bash
    git add .
    git commit -m "Add [Book Title] to [Language] list"
    ```

4.  **Push your branch to your fork:**
    * Upload your changes to your remote repository.
    ```bash
    git push origin add-new-book
    ```

5.  **Open a Pull Request (PR):**
    * Go to your fork on GitHub.
    * Click **“Compare & pull request”**.
        * **Base:** `EbookFoundation/free-programming-books:main`
        * **Compare:** `your branch`
    * Add a clear description of your contribution and submit.

---

## Contribution Guidelines

* Keep the list **alphabetized**.
* Ensure links point to **free and legal** resources.
* Include **author names** and **format** (PDF, HTML, ePub, etc.).
* Prefer **official sources** over third-party hosting.
* Avoid **link shorteners** (e.g., `bit.ly`).
* If a book has multiple formats, list them together:
    * `* [Book Title](http://example.com) - Author Name (PDF, HTML)`
* If a resource is in-progress or archived, add a note like:
    * `* (:construction: in process)`
    * `* (:card_file_box: archived)`

---

## Types of Resources

Use the appropriate file in `books/`:

* **Books:** PDFs, ePub, HTML, or Git repositories.
* **Courses:** Learning material that is not a book. Include platform if needed.
* **Interactive Tutorials:** Websites where users type code/commands and get feedback.
* **Playgrounds:** Online or offline coding environments, games, or software for practice.
* **Podcasts and Screencasts:** Learning content in audio/video format.
* **Problem Sets & Competitive Programming:** Practice exercises and challenges.

---

## Need Help?

If you’re unsure how to proceed or if a resource qualifies:

* Open an **Issue** first.
* Ask for guidance before submitting a Pull Request.

Happy contributing! 