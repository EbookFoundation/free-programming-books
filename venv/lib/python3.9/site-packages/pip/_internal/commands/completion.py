import sys
import textwrap
from optparse import Values

from pip._internal.cli.base_command import Command
from pip._internal.cli.status_codes import SUCCESS
from pip._internal.utils.misc import get_prog

BASE_COMPLETION = """
# pip {shell} completion start{script}# pip {shell} completion end
"""

COMPLETION_SCRIPTS = {
    "bash": """
        _pip_completion()
        {{
            COMPREPLY=( $( COMP_WORDS="${{COMP_WORDS[*]}}" \\
                           COMP_CWORD=$COMP_CWORD \\
                           PIP_AUTO_COMPLETE=1 $1 2>/dev/null ) )
        }}
        complete -o default -F _pip_completion {prog}
    """,
    "zsh": """
        #compdef -P pip[0-9.]#
        __pip() {{
          compadd $( COMP_WORDS="$words[*]" \\
                     COMP_CWORD=$((CURRENT-1)) \\
                     PIP_AUTO_COMPLETE=1 $words[1] 2>/dev/null )
        }}
        if [[ $zsh_eval_context[-1] == loadautofunc ]]; then
          # autoload from fpath, call function directly
          __pip "$@"
        else
          # eval/source/. command, register function for later
          compdef __pip -P 'pip[0-9.]#'
        fi
    """,
    "fish": """
        function __fish_complete_pip
            set -lx COMP_WORDS \\
                (commandline --current-process --tokenize --cut-at-cursor) \\
                (commandline --current-token --cut-at-cursor)
            set -lx COMP_CWORD (math (count $COMP_WORDS) - 1)
            set -lx PIP_AUTO_COMPLETE 1
            set -l completions
            if string match -q '2.*' $version
                set completions (eval $COMP_WORDS[1])
            else
                set completions ($COMP_WORDS[1])
            end
            string split \\  -- $completions
        end
        complete -fa "(__fish_complete_pip)" -c {prog}
    """,
    "powershell": """
        if ((Test-Path Function:\\TabExpansion) -and -not `
            (Test-Path Function:\\_pip_completeBackup)) {{
            Rename-Item Function:\\TabExpansion _pip_completeBackup
        }}
        function TabExpansion($line, $lastWord) {{
            $lastBlock = [regex]::Split($line, '[|;]')[-1].TrimStart()
            if ($lastBlock.StartsWith("{prog} ")) {{
                $Env:COMP_WORDS=$lastBlock
                $Env:COMP_CWORD=$lastBlock.Split().Length - 1
                $Env:PIP_AUTO_COMPLETE=1
                (& {prog}).Split()
                Remove-Item Env:COMP_WORDS
                Remove-Item Env:COMP_CWORD
                Remove-Item Env:PIP_AUTO_COMPLETE
            }}
            elseif (Test-Path Function:\\_pip_completeBackup) {{
                # Fall back on existing tab expansion
                _pip_completeBackup $line $lastWord
            }}
        }}
    """,
}


class CompletionCommand(Command):
    """A helper command to be used for command completion."""

    ignore_require_venv = True

    def add_options(self) -> None:
        self.cmd_opts.add_option(
            "--bash",
            "-b",
            action="store_const",
            const="bash",
            dest="shell",
            help="Emit completion code for bash",
        )
        self.cmd_opts.add_option(
            "--zsh",
            "-z",
            action="store_const",
            const="zsh",
            dest="shell",
            help="Emit completion code for zsh",
        )
        self.cmd_opts.add_option(
            "--fish",
            "-f",
            action="store_const",
            const="fish",
            dest="shell",
            help="Emit completion code for fish",
        )
        self.cmd_opts.add_option(
            "--powershell",
            "-p",
            action="store_const",
            const="powershell",
            dest="shell",
            help="Emit completion code for powershell",
        )

        self.parser.insert_option_group(0, self.cmd_opts)

    def run(self, options: Values, args: list[str]) -> int:
        """Prints the completion code of the given shell"""
        shells = COMPLETION_SCRIPTS.keys()
        shell_options = ["--" + shell for shell in sorted(shells)]
        if options.shell in shells:
            script = textwrap.dedent(
                COMPLETION_SCRIPTS.get(options.shell, "").format(prog=get_prog())
            )
            print(BASE_COMPLETION.format(script=script, shell=options.shell))
            return SUCCESS
        else:
            sys.stderr.write(
                "ERROR: You must pass {}\n".format(" or ".join(shell_options))
            )
            return SUCCESS
