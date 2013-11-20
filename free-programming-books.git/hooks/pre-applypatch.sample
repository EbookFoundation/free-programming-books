#!/bin/sh
#
# An example hook script to verify what is about to be committed
# by applypatch from an e-mail message.
#
# The hook should exit with non-zero status after issuing an
# appropriate message if it wants to stop the commit.
#
# To enable this hook, rename this file to "pre-applypatch".

. git-sh-setup
test -x "$GIT_DIR/hooks/pre-commit" &&
	exec "$GIT_DIR/hooks/pre-commit" ${1+"$@"}
:
