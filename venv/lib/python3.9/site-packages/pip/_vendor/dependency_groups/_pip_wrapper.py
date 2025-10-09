from __future__ import annotations

import argparse
import subprocess
import sys

from ._implementation import DependencyGroupResolver
from ._toml_compat import tomllib


def _invoke_pip(deps: list[str]) -> None:
    subprocess.check_call([sys.executable, "-m", "pip", "install", *deps])


def main(*, argv: list[str] | None = None) -> None:
    if tomllib is None:
        print(
            "Usage error: dependency-groups CLI requires tomli or Python 3.11+",
            file=sys.stderr,
        )
        raise SystemExit(2)

    parser = argparse.ArgumentParser(description="Install Dependency Groups.")
    parser.add_argument(
        "DEPENDENCY_GROUP", nargs="+", help="The dependency groups to install."
    )
    parser.add_argument(
        "-f",
        "--pyproject-file",
        default="pyproject.toml",
        help="The pyproject.toml file. Defaults to trying in the current directory.",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    with open(args.pyproject_file, "rb") as fp:
        pyproject = tomllib.load(fp)
    dependency_groups_raw = pyproject.get("dependency-groups", {})

    errors: list[str] = []
    resolved: list[str] = []
    try:
        resolver = DependencyGroupResolver(dependency_groups_raw)
    except (ValueError, TypeError) as e:
        errors.append(f"{type(e).__name__}: {e}")
    else:
        for groupname in args.DEPENDENCY_GROUP:
            try:
                resolved.extend(str(r) for r in resolver.resolve(groupname))
            except (LookupError, ValueError, TypeError) as e:
                errors.append(f"{type(e).__name__}: {e}")

    if errors:
        print("errors encountered while examining dependency groups:")
        for msg in errors:
            print(f"  {msg}")
        sys.exit(1)

    _invoke_pip(resolved)


if __name__ == "__main__":
    main()
