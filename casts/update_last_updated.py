import os
import re
from datetime import datetime
import feedparser
import requests
import json

# Configuration
CASTS_FOLDER = "casts"
DEFAULT_DATE = "June 2022"
YEARS_THRESHOLD = 2

# Regex to match podcast lines
podcast_pattern = re.compile(r"^\(podcast\) (.+) - (.+)$")

def append_last_updated(line, date_str):
    """
    Append (last updated: Month YYYY) if not already present.
    """
    if "(last updated:" not in line:
        return line.strip() + f" (last updated: {date_str})\n"
    return line

def find_rss_feed(podcast_name):
    """
    Try to find the RSS feed for a podcast using the iTunes Search API.
    Returns the feed URL if found, else None.
    """
    try:
        url = f"https://itunes.apple.com/search?term={requests.utils.quote(podcast_name)}&entity=podcast&limit=1"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("resultCount", 0) > 0:
                feed_url = data["results"][0].get("feedUrl")
                if feed_url:
                    return feed_url
    except Exception as e:
        print(f"⚠️ Could not find RSS for podcast '{podcast_name}': {e}")
    return None

def parse_pub_date(entry):
    """
    Parse the published date from a feed entry into a datetime object.
    Supports multiple RSS date formats.
    Returns None if it can't be parsed.
    """
    for key in ["published", "pubDate", "updated"]:
        pub_date = entry.get(key)
        if pub_date:
            # Try several date formats
            for fmt in (
                "%a, %d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d"
            ):
                try:
                    return datetime.strptime(pub_date, fmt)
                except Exception:
                    continue
    # Try feedparser's parsed time
    if "published_parsed" in entry and entry["published_parsed"]:
        try:
            return datetime(*entry["published_parsed"][:6])
        except Exception:
            pass
    return None

def get_last_episode_date(podcast_name, podcast_title):
    """
    Get the last episode's date as "Month YYYY" from the feed, or DEFAULT_DATE if not found.
    """
    feed_url = find_rss_feed(podcast_name)
    if feed_url:
        try:
            feed = feedparser.parse(feed_url)
            if feed.entries:
                dt = parse_pub_date(feed.entries[0])
                if dt:
                    return dt.strftime("%B %Y"), dt
        except Exception as e:
            print(f"⚠️ Error parsing feed for '{podcast_name}': {e}")
    # Fallback
    return DEFAULT_DATE, None

def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    updated = False
    for line in lines:
        match = podcast_pattern.match(line)
        if match:
            name, title = match.groups()
            last_date_str, last_date_dt = get_last_episode_date(name, title)
            # Check if last episode is older than YEARS_THRESHOLD
            if last_date_dt:
                years_passed = (datetime.now() - last_date_dt).days / 365.25
                if years_passed > YEARS_THRESHOLD:
                    old_line = line
                    line = append_last_updated(line, last_date_str)
                    if line != old_line:
                        print(f"🔁 {file_path}: {name} - {title} (last episode: {last_date_str})")
                        updated = True
            else:
                # If no date info, append anyway as fallback
                old_line = line
                line = append_last_updated(line, last_date_str)
                if line != old_line:
                    print(f"🔁 {file_path}: {name} - {title} (last episode: {last_date_str}, fallback)")
                    updated = True
        new_lines.append(line)

    if updated:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"✅ Updated: {file_path}")

def main():
    for root, dirs, files in os.walk(CASTS_FOLDER):
        for file in files:
            if file.endswith(".md"):
                process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
