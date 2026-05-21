#!/usr/bin/env python3
"""
Link Checker for Free Programming Books

This script checks all URLs in markdown files to identify broken links.
It can be run locally or as part of CI/CD pipeline.

Features:
- Checks HTTP/HTTPS links for availability
- Reports broken links with status codes
- Suggests Wayback Machine alternatives for dead links
- Rate limiting to avoid overwhelming servers
- Parallel checking for improved performance
- Detailed reporting

Usage:
    python check_links.py <file_or_directory> [options]

Examples:
    # Check a single file
    python check_links.py books/free-programming-books-langs.md

    # Check all files in a directory
    python check_links.py books/

    # Check with custom timeout and retries
    python check_links.py books/ --timeout 10 --retries 3

    # Check only first N links (for testing)
    python check_links.py books/free-programming-books-langs.md --limit 10
"""

import sys
import os
import re
import argparse
import time
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

# Try to import requests, provide helpful error if not available
try:
    import requests
except ImportError:
    print("Error: 'requests' library is required but not installed.")
    print("Install it with: pip install requests")
    sys.exit(1)


class LinkChecker:
    """Main class for checking links in markdown files."""

    def __init__(self, timeout=10, retries=2, delay=0.5, max_workers=10):
        """
        Initialize the link checker.

        Args:
            timeout (int): Request timeout in seconds
            retries (int): Number of retries for failed requests
            delay (float): Delay between requests to same domain (rate limiting)
            max_workers (int): Maximum number of parallel workers
        """
        self.timeout = timeout
        self.retries = retries
        self.delay = delay
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; FPB-LinkChecker/1.0; +https://github.com/EbookFoundation/free-programming-books)'
        })
        self.domain_last_check = defaultdict(float)
        self.results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'broken_links': []
        }

    def extract_links_from_file(self, filepath):
        """
        Extract all URLs from a markdown file.

        Args:
            filepath (str): Path to the markdown file

        Returns:
            list: List of tuples (line_number, url)
        """
        links = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    # Match markdown links: [text](url)
                    matches = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', line)
                    for text, url in matches:
                        # Skip anchor links and relative paths
                        if url.startswith(('http://', 'https://')):
                            links.append((line_num, url.strip()))
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
        return links

    def check_url(self, url, filepath, line_num):
        """
        Check if a URL is accessible.

        Args:
            url (str): The URL to check
            filepath (str): The file containing the URL
            line_num (int): The line number in the file

        Returns:
            dict: Result dictionary with status information
        """
        result = {
            'url': url,
            'file': filepath,
            'line': line_num,
            'status': None,
            'error': None
        }

        # Rate limiting: wait if we checked this domain recently
        domain = urlparse(url).netloc
        time_since_last = time.time() - self.domain_last_check[domain]
        if time_since_last < self.delay:
            time.sleep(self.delay - time_since_last)

        # Try to check the URL with retries
        for attempt in range(self.retries + 1):
            try:
                response = self.session.head(
                    url,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                
                # Some servers don't respond to HEAD, try GET
                if response.status_code == 405 or response.status_code == 404:
                    response = self.session.get(
                        url,
                        timeout=self.timeout,
                        allow_redirects=True,
                        stream=True  # Don't download the entire content
                    )
                    response.close()

                result['status'] = response.status_code
                self.domain_last_check[domain] = time.time()

                if response.status_code < 400:
                    return result
                else:
                    result['error'] = f"HTTP {response.status_code}"
                    return result

            except requests.exceptions.Timeout:
                result['error'] = "Timeout"
            except requests.exceptions.ConnectionError:
                result['error'] = "Connection Error"
            except requests.exceptions.TooManyRedirects:
                result['error'] = "Too Many Redirects"
            except Exception as e:
                result['error'] = str(e)

            # Wait before retry
            if attempt < self.retries:
                time.sleep(1)

        return result

    def check_file(self, filepath, limit=None):
        """
        Check all links in a file.

        Args:
            filepath (str): Path to the markdown file
            limit (int): Optional limit on number of links to check (for testing)
        """
        print(f"\nChecking: {filepath}")
        links = self.extract_links_from_file(filepath)

        if not links:
            print("  No links found.")
            return

        if limit:
            links = links[:limit]
            print(f"  Found {len(links)} links (limited to {limit} for testing)")
        else:
            print(f"  Found {len(links)} links")

        # Check links in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.check_url, url, filepath, line_num): (url, line_num)
                for line_num, url in links
            }

            for future in as_completed(futures):
                result = future.result()
                self.results['total'] += 1

                if result['error']:
                    self.results['failed'] += 1
                    self.results['broken_links'].append(result)
                    print(f"  ✗ Line {result['line']}: {result['url']}")
                    print(f"    Error: {result['error']}")
                else:
                    self.results['success'] += 1
                    # Uncomment to see successful checks (verbose)
                    # print(f"  ✓ Line {result['line']}: {result['url']} (HTTP {result['status']})")

    def check_directory(self, dirpath, limit=None):
        """
        Check all markdown files in a directory.

        Args:
            dirpath (str): Path to the directory
            limit (int): Optional limit on number of links to check per file
        """
        for root, _, files in os.walk(dirpath):
            for filename in files:
                if filename.lower().endswith('.md'):
                    filepath = os.path.join(root, filename)
                    self.check_file(filepath, limit)

    def print_summary(self):
        """Print a summary of the link checking results."""
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total links checked: {self.results['total']}")
        print(f"Successful: {self.results['success']}")
        print(f"Failed: {self.results['failed']}")

        if self.results['broken_links']:
            print("\n" + "=" * 70)
            print("BROKEN LINKS")
            print("=" * 70)
            for link in self.results['broken_links']:
                print(f"\nFile: {link['file']}")
                print(f"Line: {link['line']}")
                print(f"URL: {link['url']}")
                print(f"Error: {link['error']}")
                
                # Suggest Wayback Machine alternative
                wayback_url = f"https://web.archive.org/web/*/{link['url']}"
                print(f"Wayback Machine: {wayback_url}")

    def save_report(self, output_file):
        """
        Save the results to a file.

        Args:
            output_file (str): Path to the output file
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("Link Checker Report\n")
                f.write("=" * 70 + "\n\n")
                f.write(f"Total links checked: {self.results['total']}\n")
                f.write(f"Successful: {self.results['success']}\n")
                f.write(f"Failed: {self.results['failed']}\n\n")

                if self.results['broken_links']:
                    f.write("Broken Links:\n")
                    f.write("-" * 70 + "\n\n")
                    for link in self.results['broken_links']:
                        f.write(f"File: {link['file']}\n")
                        f.write(f"Line: {link['line']}\n")
                        f.write(f"URL: {link['url']}\n")
                        f.write(f"Error: {link['error']}\n")
                        f.write(f"Wayback: https://web.archive.org/web/*/{link['url']}\n\n")

            print(f"\nReport saved to: {output_file}")
        except Exception as e:
            print(f"Error saving report: {e}")


def main():
    """Main entry point for the link checker."""
    parser = argparse.ArgumentParser(
        description="Check links in markdown files for the Free Programming Books repository."
    )
    parser.add_argument(
        'path',
        help="Path to a markdown file or directory to check"
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)"
    )
    parser.add_argument(
        '--retries',
        type=int,
        default=2,
        help="Number of retries for failed requests (default: 2)"
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help="Delay between requests to same domain in seconds (default: 0.5)"
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=10,
        help="Maximum number of parallel workers (default: 10)"
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help="Limit number of links to check per file (for testing)"
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help="Save report to file"
    )

    args = parser.parse_args()

    # Validate path
    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist.")
        sys.exit(1)

    # Create link checker
    checker = LinkChecker(
        timeout=args.timeout,
        retries=args.retries,
        delay=args.delay,
        max_workers=args.workers
    )

    # Check file or directory
    print("=" * 70)
    print("Free Programming Books - Link Checker")
    print("=" * 70)

    if os.path.isfile(args.path):
        checker.check_file(args.path, args.limit)
    elif os.path.isdir(args.path):
        checker.check_directory(args.path, args.limit)
    else:
        print(f"Error: '{args.path}' is neither a file nor a directory.")
        sys.exit(1)

    # Print summary
    checker.print_summary()

    # Save report if requested
    if args.output:
        checker.save_report(args.output)

    # Exit with error code if there were broken links
    sys.exit(1 if checker.results['failed'] > 0 else 0)


if __name__ == '__main__':
    main()
