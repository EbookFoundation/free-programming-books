#!/bin/sh
#
# An example hook script to prepare the commit log message.
# Called by "git commit" with the name of the file that has the
# commit message, followed by the description of the commit
# message's source.  The hook's purpose is to edit the commit
# message file.  If the hook fails with a non-zero status,
# the commit is aborted.
#
# To enable this hook, rename this file to "prepare-commit-msg".

# This hook includes three examples.  The first comments out the
# "Conflicts:" part of a merge commit.
#
# The second includes the output of "git diff --name-status -r"
# into the message, just before the "git status" output.  It is
# commented because it doesn't cope with --amend or with squashed
# commits.
#
# The third example adds a Signed-off-by line to the message, that can
# still be edited.  This is rarely a good idea.

case "$2,$3" in
  merge,)
    /usr/bin/perl -i.bak -ne 's/^/# /, s/^# #/#/ if /^Conflicts/ .. /#/; print' "$1" ;;

# ,|template,)
#   /usr/bin/perl -i.bak -pe '
#      print "\n" . `git diff --cached --name-status -r`
#	 if /^#/ && $first++ == 0' "$1" ;;

  *) ;;
esac

# SOB=$(git var GIT_AUTHOR_IDENT | sed -n 's/^\(.*>\).*$/Signed-off-by: \1/p')
# grep -qs "^$SOB" "$1" || echo "$SOB" >> "$1"
