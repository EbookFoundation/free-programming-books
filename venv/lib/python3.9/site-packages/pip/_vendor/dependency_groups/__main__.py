import argparse
import sys

from ._implementation import resolve
from ._toml_compat import tomllib


def main() -> None:
    if tomllib is None:
        print(
            "Usage error: dependency-groups CLI requires tomli or Python 3.11+",
            file=sys.stderr,
        )
        raise SystemExit(2)

    parser = argparse.ArgumentParser(
        description=(
            "A dependency-groups CLI. Prints out a resolved group, newline-delimited."
        )
    )
    parser.add_argument(
        "GROUP_NAME", nargs="*", help="The dependency group(s) to resolve."
    )
    parser.add_argument(
        "-f",
        "--pyproject-file",
        default="pyproject.toml",
        help="The pyproject.toml file. Defaults to trying in the current directory.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="An output file. Defaults to stdout.",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List the available dependency groups",
    )
    args = parser.parse_args()

    with open(args.pyproject_file, "rb") as fp:
        pyproject = tomllib.load(fp)

    dependency_groups_raw = pyproject.get("dependency-groups", {})

    if args.list:
        print(*dependency_groups_raw.keys())
        return
    if not args.GROUP_NAME:
        print("A GROUP_NAME is required", file=sys.stderr)
        raise SystemExit(3)

    content = "\n".join(resolve(dependency_groups_raw, *args.GROUP_NAME))

    if args.output is None or args.output == "-":
        print(content)
    else:
        with open(args.output, "w", encoding="utf-8") as fp:
            print(content, file=fp)


if __name__ == "__main__":
    main()
