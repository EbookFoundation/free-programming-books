# PR Review Tracking for free-programming-books

## Review Criteria Checklist

### Content Requirements
- [ ] Resource is genuinely free (no paywalls, required purchases)
- [ ] No file hosting services (Google Drive, Dropbox, Mega, etc.)
- [ ] Appropriate categorization (book vs course vs tutorial)
- [ ] Author names included where appropriate
- [ ] Publication date for older books

### Formatting Requirements
- [ ] Alphabetical ordering maintained
- [ ] Proper markdown syntax
- [ ] Correct spacing (2 blank lines before sections, 1 after headings, 0 between links)
- [ ] Link format: `* [Title](URL) - Author` (dash surrounded by spaces)
- [ ] HTTPS preferred over HTTP
- [ ] No trailing slashes on root domains
- [ ] No URL shorteners

### Special Notations
- [ ] `(PDF)` notation for PDF files
- [ ] `(:construction: *in process*)` for unfinished resources
- [ ] `(email address *requested*, not required)` for registration requirements
- [ ] `(archived)` for Wayback Machine links

## Current PR Reviews

### Active Reviews

#### PR #11962 - Dependabot: Update tj-actions/changed-files
- **Author**: dependabot
- **Type**: Dependencies update
- **Status**: ✅ Ready to merge
- **Review Notes**:
  - Routine GitHub Actions dependency update
  - Updates tj-actions/changed-files from v46 to v47
  - No manual intervention needed
  - Auto-merge appropriate for dependabot updates

#### PR #11955 - Vietnamese Book Addition
- **Author**: VThanh-Huy
- **Type**: Content addition
- **Status**: ❌ Needs fixes
- **Issues Found**:
  1. **Critical formatting error**: Missing proper markdown format
     - Current: `* Sách 2 https://cafedev.vn/review-va-chia-se-sach-ve-python-cuc-hay-cho-ace/`
     - Should be: `* [Title](URL) - Author`
  2. **No proper title**: Using "Sách 2" (Book 2) as placeholder
  3. **No author information**
  4. **Wrong section**: Python book added to Machine Learning section
  5. **Incorrect alphabetical order** (if kept in ML section)
  6. **Missing blank line** at end of file
  7. **Link validation**: The link is to a blog review, not the actual book
- **Action Required**:
  - Provide proper book title
  - Add author information
  - Fix markdown formatting
  - Move to Python section (needs to be created)
  - Ensure link points to actual free book, not a review

#### PR #11946 - Malayalam CONTRIBUTING.md Translation
- **Author**: Symbian-Bro
- **Type**: Translation
- **Status**: ⏳ Awaiting native speaker review
- **Review Notes**:
  - Translation of documentation
  - Requires Malayalam speaker verification
  - Check consistency with other translations

### Pending Review Queue

1. **PR #11683** - Add Go lang courses
   - Open since: Oct 25, 2024

2. **PR #11681** - Add SQL courses from Hyperskill
   - Open since: Oct 25, 2024

3. **PR #11529** - Assamese translation for HOWTO.md
   - Open since: Oct 13, 2024

4. **PR #10915** - Malay CODE_OF_CONDUCT translation
   - Open since: Oct 30, 2023

5. **PR #10909** - Malay HOWTO translation
   - Open since: Oct 30, 2023

6. **PR #9953** - Marathi translations
   - Open since: Oct 7, 2023

## Review Commands Reference

```bash
# List PRs
gh pr list --repo EbookFoundation/free-programming-books

# View PR details
gh pr view <number> --repo EbookFoundation/free-programming-books

# Check PR diff
gh pr diff <number> --repo EbookFoundation/free-programming-books

# Check out PR locally
gh pr checkout <number> --repo EbookFoundation/free-programming-books

# Run linter locally
npm test (if available)
```

## Notes

- PRs with dependency updates from dependabot are generally safe to approve after CI passes
- Content additions require careful review for:
  - Actual free availability of resources
  - Correct categorization and formatting
  - No duplicates
- Translation PRs need native speaker verification when possible

---
*Last updated: 2025-09-22*