# import os
# import re

# BOOKS_DIR = "books"

# def normalize(line):
#     """Prepare a line for comparison: lowercase, remove special characters, strip whitespace."""
#     line = line.strip().lower()
#     return re.sub(r'[^a-z0-9 ]', '', line)

# def is_sorted(lines):
#     """Return True if lines are alphabetically sorted."""
#     cleaned = [normalize(line) for line in lines if line.strip()]
#     return cleaned == sorted(cleaned)

# def sort_lines(lines):
#     """Return lines sorted alphabetically."""
#     return sorted(lines, key=normalize)

# def lint_and_fix_file(filepath):
#     """Check and fix alphabetical order of list items in a single markdown file."""
#     if not os.path.exists(filepath):
#         print(f"❌ File not found: {filepath}")
#         return 0

#     with open(filepath, encoding="utf-8") as f:
#         lines = f.readlines()

#     fixed_lines = []
#     section_lines = []
#     in_section = False
#     warnings = 0

#     for line in lines + [""]:  # Extra blank line to flush last section
#         if line.startswith("### "):
#             if section_lines and not is_sorted(section_lines):
#                 section_lines = sort_lines(section_lines)
#                 warnings += 1
#             fixed_lines.extend(section_lines)
#             section_lines = []
#             fixed_lines.append(line)
#             in_section = True
#         elif line.startswith("* "):
#             section_lines.append(line)
#         elif in_section and not line.strip():
#             if section_lines and not is_sorted(section_lines):
#                 section_lines = sort_lines(section_lines)
#                 warnings += 1
#             fixed_lines.extend(section_lines)
#             fixed_lines.append(line)
#             section_lines = []
#             in_section = False
#         else:
#             fixed_lines.append(line)

#     # Save changes if any
#     if warnings > 0:
#         with open(filepath, "w", encoding="utf-8") as f:
#             f.writelines(fixed_lines)

#     return warnings

# def lint_books_directory(directory=BOOKS_DIR):
#     """Lint and fix all markdown files in the books directory."""
#     total_warnings = 0
#     md_files = [f for f in os.listdir(directory) if f.endswith(".md")]

#     if not md_files:
#         print(f"❌ No markdown files found in '{directory}'")
#         return

#     for md_file in md_files:
#         path = os.path.join(directory, md_file)
#         warnings = lint_and_fix_file(path)
#         if warnings:
#             print(f"⚠️  {warnings} section(s) fixed in {md_file}")
#         total_warnings += warnings

#     if total_warnings == 0:
#         print("✅ All sections are already sorted!")
#     else:
#         print(f"✅ Lint complete — total {total_warnings} section(s) fixed.")

# if __name__ == "__main__":
#     lint_books_directory()

import os
import re
from datetime import datetime

BOOKS_DIR = "books"
LOG_FILE = "fpb_lint_log.md"

def normalize(line):
    """Prepare a line for comparison: lowercase, remove special characters, strip whitespace."""
    line = line.strip().lower()
    return re.sub(r'[^a-z0-9 ]', '', line)

def is_sorted(lines):
    """Return True if lines are alphabetically sorted."""
    cleaned = [normalize(line) for line in lines if line.strip()]
    return cleaned == sorted(cleaned)

def sort_lines(lines):
    """Return lines sorted alphabetically."""
    return sorted(lines, key=normalize)

def lint_and_fix_file(filepath):
    """
    Check and fix alphabetical order of list items in a single markdown file.
    Returns a list of change logs for this file.
    """
    if not os.path.exists(filepath):
        return []

    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    fixed_lines = []
    section_lines = []
    in_section = False
    logs = []

    for line in lines + [""]:  # Extra blank line to flush last section
        if line.startswith("### "):
            if section_lines and not is_sorted(section_lines):
                old_section = section_lines.copy()
                section_lines = sort_lines(section_lines)
                logs.append(f"Section '{line.strip()}' in {os.path.basename(filepath)} fixed:\n- " +
                            "\n- ".join([l.strip() for l in old_section]))
            fixed_lines.extend(section_lines)
            section_lines = []
            fixed_lines.append(line)
            in_section = True
        elif line.startswith("* "):
            section_lines.append(line)
        elif in_section and not line.strip():
            if section_lines and not is_sorted(section_lines):
                old_section = section_lines.copy()
                section_lines = sort_lines(section_lines)
                logs.append(f"Section ended before blank line in {os.path.basename(filepath)} fixed:\n- " +
                            "\n- ".join([l.strip() for l in old_section]))
            fixed_lines.extend(section_lines)
            fixed_lines.append(line)
            section_lines = []
            in_section = False
        else:
            fixed_lines.append(line)

    # Save changes if any
    if logs:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)

    return logs

def lint_books_directory(directory=BOOKS_DIR, log_file=LOG_FILE):
    """Lint all markdown files and store logs in a document."""
    all_logs = []
    md_files = [f for f in os.listdir(directory) if f.endswith(".md")]

    for md_file in md_files:
        path = os.path.join(directory, md_file)
        logs = lint_and_fix_file(path)
        if logs:
            all_logs.extend(logs)

    if all_logs:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"# FPB Linter Logs — {timestamp}\n\n")
            f.write("\n\n".join(all_logs))
        print(f"✅ Lint finished — changes logged in '{log_file}'")
    else:
        print("✅ All sections are already sorted! No logs generated.")

if __name__ == "__main__":
    lint_books_directory()
