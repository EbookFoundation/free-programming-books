# Feedback for PR #11955

## Issues Found

Thank you for your contribution! However, there are several formatting issues that need to be fixed before this PR can be merged:

### 1. ❌ **Incorrect Markdown Format**

The added line doesn't follow the required markdown format:

**Current:**
```markdown
* Sách 2 https://cafedev.vn/review-va-chia-se-sach-ve-python-cuc-hay-cho-ace/
```

**Required format:**
```markdown
* [Book Title](URL) - Author Name
```

### 2. ❌ **Missing Book Information**

- **Title**: "Sách 2" (Book 2) appears to be a placeholder. Please provide the actual book title.
- **Author**: No author information is provided.

### 3. ❌ **Wrong Link Type**

The URL points to a blog review about Python books, not to an actual free book. This repository only accepts direct links to free books, not reviews or articles about books.

### 4. ❌ **Missing Final Blank Line**

The file should end with a blank line.

## Suggested Fix

The main issue is that the link points to a blog review rather than an actual free book. Please:

1. **Find a direct link to a free book** (not a review or blog post)
2. **Use the proper markdown format:**
   ```markdown
   * [Actual Book Title](direct-link-to-book) - Author Name
   ```
3. **Ensure the book is actually free** and accessible without payment

If you cannot find a direct link to a free book, please consider withdrawing this addition.

## Example of Correct Format

Here's how the existing entry looks (correct format):
```markdown
* [Đắm chìm vào Học sâu](https://d2l.aivivn.com) - `trl.:` Nhóm dịch thuật Đắm chìm vào Học sâu (HTML)
```

Please update your PR with these fixes and let us know which specific book you'd like to add. Thank you!

---

## GitHub CLI Comment Command

To post this feedback:
```bash
gh pr comment 11955 --repo EbookFoundation/free-programming-books --body-file PR_11955_FEEDBACK.md
```