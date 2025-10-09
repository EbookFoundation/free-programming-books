from __future__ import annotations

import argparse
import sys

from ._implementation import DependencyGroupResolver
from ._toml_compat import tomllib


def main(*, argv: list[str] | None = None) -> None:
    if tomllib is None:
        print(
            "Usage error: dependency-groups CLI requires tomli or Python 3.11+",
            file=sys.stderr,
        )
        raise SystemExit(2)

    parser = argparse.ArgumentParser(
        description=(
            "Lint Dependency Groups for validity. "
            "This will eagerly load and check all of your Dependency Groups."
        )
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
    try:
        resolver = DependencyGroupResolver(dependency_groups_raw)
    except (ValueError, TypeError) as e:
        errors.append(f"{type(e).__name__}: {e}")
    else:
        for groupname in resolver.dependency_groups:
            try:
                resolver.resolve(groupname)
            except (LookupError, ValueError, TypeError) as e:
                errors.append(f"{type(e).__name__}: {e}")

    if errors:
        print("errors encountered while examining dependency groups:")
        for msg in errors:
            print(f"  {msg}")
        sys.exit(1)
    else:
        print("ok")
        sys.exit(0)


if __name__ == "__main__":
    main()
