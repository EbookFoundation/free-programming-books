# Instructions for Creating GitHub Pull Request

## Step 1: Push the branch to GitHub
```bash
git push origin hacko
```

## Step 2: Create Pull Request on GitHub
1. Go to your fork: https://github.com/monu808/free-programming-books
2. Click "Compare & pull request" button
3. Set the base repository to: `EbookFoundation/free-programming-books`
4. Set the base branch to: `main`
5. Set your branch to: `hacko`

## Step 3: PR Title
```
Fix TailwindCSS index entry formatting issue
```

## Step 4: PR Description
Copy the content from `GITHUB_PR_DESCRIPTION.md` into the PR description box.

## Step 5: Additional Labels to Request
- `good first issue`
- `hacktoberfest`
- `documentation`
- `enhancement`

## Notes
- The original repository is: https://github.com/EbookFoundation/free-programming-books
- Your fork is: https://github.com/monu808/free-programming-books
- Branch name: `hacko`
- This fixes a legitimate formatting issue perfect for Hacktoberfest 2025

## What the PR Fixes
- Converts external link in index to proper internal anchor
- Adds missing TailwindCSS section under HTML and CSS
- Follows formatting guidelines in CONTRIBUTING.md
- Improves navigation and user experience