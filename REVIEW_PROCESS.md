# PR Review Process Guide

## Quick Start Review Process

### 1. Initial Assessment
```bash
# Get overview of open PRs
gh pr list --repo EbookFoundation/free-programming-books --limit 20

# View specific PR
gh pr view <PR_NUMBER> --repo EbookFoundation/free-programming-books
```

### 2. Detailed Review Steps

#### For Content Additions (Books/Courses/Resources)

1. **Check the diff**:
   ```bash
   gh pr diff <PR_NUMBER> --repo EbookFoundation/free-programming-books
   ```

2. **Verify resource is free**:
   - Visit the linked resource
   - Ensure no paywall or required purchase
   - Check for registration requirements (note if email required)

3. **Check formatting**:
   - Alphabetical order within section
   - Proper markdown: `* [Title](URL) - Author Name`
   - Correct spacing between sections
   - HTTPS links preferred

4. **Search for duplicates**:
   ```bash
   # Check out PR locally
   gh pr checkout <PR_NUMBER> --repo EbookFoundation/free-programming-books

   # Search for potential duplicates
   grep -i "keyword" books/*.md courses/*.md
   ```

#### For Dependency Updates

1. **Review changes**:
   - Check version bump is reasonable
   - Review changelog/release notes
   - Ensure CI passes

2. **For GitHub Actions updates**:
   - Verify action is from trusted source
   - Check for breaking changes

#### For Translations

1. **Structural check**:
   - Compare with English version for structure
   - Ensure all sections are present
   - Check markdown formatting preserved

2. **Language verification**:
   - Request native speaker review if available
   - Use online translation tools for basic verification

## Common Issues and Fixes

### Linter Errors

Most common linting issues:

1. **Alphabetical ordering**:
   - Resources must be in alphabetical order within sections
   - Case-insensitive sorting

2. **Spacing issues**:
   ```markdown
   WRONG:
   * [Book A](url)
   * [Book B](url)
   ### Section

   CORRECT:
   * [Book A](url)
   * [Book B](url)


   ### Section
   ```

3. **Format issues**:
   ```markdown
   WRONG:
   * [Book](url)- Author
   * [Book] (url) - Author

   CORRECT:
   * [Book](url) - Author
   ```

### Testing Locally

If the repo has tests:
```bash
# Check out the PR
gh pr checkout <PR_NUMBER> --repo EbookFoundation/free-programming-books

# Install dependencies (if package.json exists)
npm install

# Run tests
npm test
```

## Review Response Templates

### Approval
```markdown
LGTM! This PR follows all contribution guidelines:
- ✅ Resource is free and accessible
- ✅ Properly formatted and alphabetically ordered
- ✅ No duplicates found
- ✅ Appropriate categorization

Ready to merge.
```

### Requesting Changes
```markdown
Thank you for your contribution! A few formatting issues need to be fixed:

1. **Alphabetical ordering**: [Specific item] should come before [other item]
2. **Spacing**: Please add 2 blank lines before the ### Section heading
3. **Format**: Please use `* [Title](URL) - Author` format

Please run `npm test` locally to catch these issues before pushing.
```

### Needs Verification
```markdown
Thanks for the contribution! Before approval, could you please:

1. Confirm this resource is completely free (I see a "Premium" section on the site)
2. Add author name: `* [Title](URL) - Author Name`
3. Is this a book or a course? It should go in the appropriate file

Looking forward to your updates!
```

## Decision Tree

```
Is it a dependency update?
├── Yes → Check version bump → CI passing? → Approve
└── No → Is it content addition?
    ├── Yes → Check if free → Check format → Check duplicates → Test → Review
    └── No → Is it a translation?
        ├── Yes → Check structure → Request native review
        └── No → Is it a fix/improvement?
            └── Yes → Verify fix works → Test → Review
```

## Useful GitHub CLI Commands

```bash
# List PRs with specific labels
gh pr list --repo EbookFoundation/free-programming-books --label "help wanted"

# List PRs from specific author
gh pr list --repo EbookFoundation/free-programming-books --author username

# Add comment to PR
gh pr comment <PR_NUMBER> --repo EbookFoundation/free-programming-books --body "Your comment here"

# Check PR status checks
gh pr checks <PR_NUMBER> --repo EbookFoundation/free-programming-books

# View files changed in PR
gh pr view <PR_NUMBER> --repo EbookFoundation/free-programming-books --json files
```

## Priority Order

1. **High Priority**:
   - PRs fixing broken links
   - PRs with many approvals waiting for merge
   - Simple formatting fixes

2. **Medium Priority**:
   - New content additions
   - Dependency updates
   - Documentation improvements

3. **Low Priority**:
   - Large restructuring PRs
   - Controversial additions
   - PRs missing information

---
*Use PR_REVIEWS.md to track specific PR review status*