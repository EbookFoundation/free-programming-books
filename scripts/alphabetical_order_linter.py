# alphabetical_order_linter.py

import os
import re

# Jin folders ki .md files ko humein check karna hai, unki list
DIRECTORIES_TO_CHECK = ["books", "courses", "more", "casts"]

def clean_text(text):
    """
    Ek line se link aur special characters hatakar saaf text nikalta hai
    taaki hum aasaani se compare kar sakein.
    Example: '* [Awesome Book](http://a.com)' -> 'awesome book'
    """
    text = text.strip()  # Shuru aur aakhir ke extra space hatata hai
    # Markdown links ([Title](url)) se title nikalne ki koshish
    match = re.search(r'\*\s*\[([^\]]+)\]', text)
    if match:
        text = match.group(1)
    elif text.startswith('* '):
        # Agar link nahin hai, to '*' ke baad ka text lein
        text = text[2:]
        
    # Title se special characters hata dein
    text = re.sub(r'[^\w\s]', '', text)
    return text.lower() # Sab kuch lowercase mein badal deta hai

def check_file(filepath):
    """Ek file ke andar alphabetical order check karta hai."""
    errors_found = False
    last_line_text = ""
    previous_line_content = ""
    
    try:
        # NOTE: Hum file content ko direct access nahin kar sakte, isliye logic assume kar rahe hain.
        # Asli PR mein, maintainer is script ko locally chalaayega.
        # Niche diya gaya logic GitHub Actions mein chalega.
        
        # Yah hissa PR ke description mein samjhana zaroori hai.
        pass # Is block ko abhi ke liye khaali chhod dein, kyunki hum web UI mein file read nahin kar sakte.
             # Asli code jo PR mein jaayega, woh neeche waala hai.

    except Exception as e:
        print(f"Could not process file {filepath}: {e}")

    # Asli logic jo PR mein kaam aayega:
    # with open(filepath, 'r', encoding='utf-8') as f:
    #     lines = f.readlines()
    # ... (baaki logic neeche hai) ...

    return errors_found

def main():
    """Main function jo script ko chalata hai."""
    print("This script will be used by maintainers to check for alphabetical order.")


if __name__ == "__main__":
    main()

# --- Yahaan se poora code paste karein ---

import os
import re

DIRECTORIES_TO_CHECK = ["books", "courses", "more", "casts"]

def clean_text(text):
    text = text.strip()
    match = re.search(r'\*\s*\[([^\]]+)\]', text)
    if match:
        text = match.group(1)
    elif text.startswith('* '):
        text = text[2:]
    
    text = re.sub(r'[^\w\s]', '', text)
    return text.lower()

def check_file(filepath, lines):
    errors_found = False
    last_line_text = ""
    previous_line_content = ""
    
    for line_num, line in enumerate(lines, 1):
        if line.strip().startswith('* '):
            current_line_text = clean_text(line)
            
            if last_line_text and current_line_text < last_line_text:
                print(f"ERROR: Alphabetical order violation in '{filepath}' at line {line_num}:")
                print(f"  -> This line: '{line.strip()}'")
                print(f"  -> Should come AFTER: '{previous_line_content.strip()}'\n")
                errors_found = True
            
            last_line_text = current_line_text
            previous_line_content = line
        else:
            last_line_text = ""
            previous_line_content = ""
            
    return errors_found

def main():
    print("Starting alphabetical order check...")
    total_errors_found = False
    
    for directory in DIRECTORIES_TO_CHECK:
        if os.path.isdir(directory):
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith(".md"):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                            if check_file(filepath, lines):
                                total_errors_found = True
                        except Exception as e:
                            print(f"Could not read file {filepath}: {e}")
        else:
            print(f"Warning: Directory '{directory}' not found. Skipping.")
            
    if total_errors_found:
        print("\nCheck finished. Alphabetical order issues found. 😕")
        exit(1)
    else:
        print("\nCheck finished. All lists appear to be in alphabetical order. Great job! 👍")

if __name__ == "__main__":
    main()
