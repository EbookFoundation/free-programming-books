# pdf_to_audiobook.py
# Inspired-by: https://zapier.com/blog/python-automation/
# License: MIT (sample code)

import PyPDF2, pyttsx3, sys
pdf_path = sys.argv[1] if len(sys.argv) > 1 else "book.pdf"
mp3_path = pdf_path.replace(".pdf", ".mp3")

reader = PyPDF2.PdfReader(open(pdf_path, "rb"))
engine  = pyttsx3.init()
text = " ".join(page.extract_text() for page in reader.pages)
engine.save_to_file(text, mp3_path)
engine.runAndWait()
print("🎧", mp3_path, "created")
