# GitHub Copilot, please complete this script:

# Task:
# 1. Scan all Markdown files in the 'casts/' folder.
# 2. For each line matching "(podcast) Name - Title", fetch the last episode date.
#    - Use podcast RSS feeds if possible.
#    - If RSS is not available, fallback to a default date (e.g., June 2022).
# 3. Append "(last updated: Month YYYY)" to the line if not already present.
# 4. Only update if more than 2 years have passed since last episode.
# 5. Save all changes back to the same Markdown file.
# 6. Handle UTF-8 and Unicode characters properly.
# 7. Include all imports, helper functions, and comments for clarity.
# 8. Make the code modular so that it can later integrate with a JSON or CSV of known dates.
# 9. Print logs of updated files and podcast lines.

import os
import re
from datetime import datetime

# Configuration
CASTS_FOLDER = "casts"
DEFAULT_DATE = "June 2022"
YEARS_THRESHOLD = 2

# Regex to match podcast lines
podcast_pattern = re.compile(r"^\(podcast\) (.+) - (.+)$")

# Helper: append last updated if needed
def append_last_updated(line, date_str):
    if "(last updated:" not in line:
        return line.strip() + f" (last updated: {date_str})\n"
    return line

# Placeholder for fetching last episode date from RSS/Spotify/Apple Podcasts
def get_last_episode_date(podcast_name, podcast_title):
    """
    Copilot: fill this function to fetch the last episode date
    from RSS feeds, Spotify API, or Apple Podcasts API.
    Return "Month YYYY" format.
    If not available, return DEFAULT_DATE.
    """
    return DEFAULT_DATE  # fallback

# Process a single Markdown file
def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        match = podcast_pattern.match(line)
        if match:
            name, title = match.groups()
            last_date = get_last_episode_date(name, title)
            # Only update if older than threshold
            # Copilot: fill logic to compare last_date with today and YEARS_THRESHOLD
            line = append_last_updated(line, last_date)
        new_lines.append(line)

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"✅ Updated: {file_path}")

# Main loop: scan all Markdown files
def main():
    for root, dirs, files in os.walk(CASTS_FOLDER):
        for file in files:
            if file.endswith(".md"):
                process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
