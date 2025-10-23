#!/bin/bash
# Replace any line starting with - followed by space and [ with * followed by same
sed -i '' 's/^-   \[/\*   \[/g' free-programming-books-langs.md
# Replace any line starting with multiple spaces, then - followed by space and [ with same spaces followed by * and same
sed -i '' 's/^\([[:space:]]*\)-   \[/\1\*   \[/g' free-programming-books-langs.md