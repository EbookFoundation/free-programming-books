import os

root = "courses"
output = "docs/roadmaps.md"

entries = []
for file in sorted(os.listdir(root)):
    if file.startswith("free-courses-") and file.endswith(".md"):
        lang = file.replace("free-courses-", "").replace(".md", "").upper()
        entries.append(f"- [{lang} Roadmap](../{root}/{file})")

with open(output, "w", encoding="utf-8") as f:
    f.write("# 🧭 Learning Roadmaps\n\n")
    f.write("Explore structured learning paths by language:\n\n")
    f.write("\n".join(entries))
    f.write("\n\n---\n\n[← Back to Home](../README.md)\n")
