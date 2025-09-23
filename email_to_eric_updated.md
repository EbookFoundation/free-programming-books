# Updated Email to Eric Hellman

Subject: AI-assisted PR reviews for free-programming-books - Results and Lessons Learned

Hi Eric,

Following up on your invitation to help review PRs for free-programming-books, I experimented with using Claude Code to systematically review all 8 open PRs. I wanted to share both the successes and the important lessons learned about AI-assisted reviews.

## What Worked Well

Claude Code successfully:
- **Analyzed 8 PRs in ~10 minutes** with systematic methodology
- **Caught real formatting issues** in PR #11955 (Vietnamese book addition):
  - Missing markdown format (`* Title URL` instead of `* [Title](URL) - Author`)
  - Placeholder title ("Sách 2" instead of actual book name)
  - Link pointing to blog review rather than actual free book
  - Missing author information
- **Identified old PRs** needing attention (3 PRs over 1 year old)
- **Created consistent feedback templates** following repo guidelines

## Critical Errors Caught by Human Review

However, I had Codex (GPT-5) double-check Claude's work, which revealed important mistakes:

1. **False positive**: Claude incorrectly claimed PR #11955 violated alphabetical order (Vietnamese alphabetical order was actually correct)

2. **Premature approval**: Claude marked 1+ year old translation PRs as "ready to merge" without checking if they still apply cleanly after repository changes

3. **Missing process requirements**: Didn't enforce the need for native speaker review on translation PRs

## Key Lessons for AI-Assisted Reviews

### What AI Does Well:
- Systematic formatting checks
- Pattern recognition across multiple PRs
- Speed and consistency
- Documentation generation

### What Requires Human Oversight:
- **Language-specific rules** (alphabetical order in different languages)
- **Process knowledge** (when native reviews are required)
- **Temporal context** (how repository changes affect old PRs)
- **Final approval decisions**

## Updated Recommendations

After corrections, the PR status is:
- **Ready to merge**: 2 PRs (#11962 Dependabot, #11681 SQL courses)
- **Minor fix needed**: 1 PR (#11683 Go courses - remove extra asterisk)
- **Major revision needed**: 1 PR (#11955 Vietnamese - invalid link type)
- **Needs native review**: 1 PR (#11946 Malayalam translation)
- **Needs conflict check**: 3 PRs (1+ year old Malay/Marathi translations)

## Proposed Workflow

AI-assisted reviews could be valuable with this workflow:
1. **AI generates initial analysis** (formatting, basic content checks)
2. **Human reviewer validates findings** (especially for edge cases)
3. **AI helps with response templates** (but human approves before posting)
4. **Maintainer makes final decisions** on merge-worthiness

This approach could help clear backlogs while maintaining quality, but requires human oversight for accuracy and process compliance.

Would you like me to test this refined approach on future PRs? I've documented the corrected methodology and can share the full review files if helpful.

Best,
[Your name]

---

P.S. The corrected review documentation is available at: https://github.com/rdhyee/free-programming-books/tree/PR-reviews

*All corrections have been made based on the quality control review - this demonstrates why human oversight remains essential even with sophisticated AI assistance.*