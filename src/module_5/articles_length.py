import re
import json

# File paths
input_file = "/home/fabio/Documents/GitHub/Essir_2025_work/legalQA/src/module_3/lawsWithText.csv"
output_file = "articles_length.json"

def extract_law_name(text):
    # Search only the first 2000 characters for efficiency and accuracy
    header = text[:2000]
    patterns = [
        r"(COMMISSION DELEGATED REGULATION \(EU\) \d+/\d+ of [^\n]+)",
        r"(REGULATION \(EU\) \d+/\d+ of [^\n]+)",
        r"(DIRECTIVE \(EU\) \d+/\d+ of [^\n]+)",
        r"(COMMISSION IMPLEMENTING REGULATION \(EU\) \d+/\d+ of [^\n]+)",
        r"(COMMISSION REGULATION \(EC\) No \d+/\d+ of [^\n]+)",
        r"(REGULATION \(EC\) No \d+/\d+ of [^\n]+)"
        # Add more patterns as needed
    ]
    for pattern in patterns:
        match = re.search(pattern, header)
        if match:
            return match.group(1).strip()
    # Fallback: look for a line in all caps with "REGULATION" or "DIRECTIVE"
    for line in header.splitlines():
        if line.isupper() and ("REGULATION" in line or "DIRECTIVE" in line):
            return line.strip()
    return "Unknown Law Name"

# Read the law text
with open(input_file, "r", encoding="utf-8") as f:
    text = f.read()

law_name = extract_law_name(text)

chapter_pattern = r"^(CHAPTER\s+[IVXLCDM]+.*)$"
section_pattern = r"^(SECTION\s+\d+.*)$"
article_pattern = r"^(Article\s+\d+[A-Za-z]*)"

chapter_matches = list(re.finditer(chapter_pattern, text, re.MULTILINE))
section_matches = list(re.finditer(section_pattern, text, re.MULTILINE))
article_matches = list(re.finditer(article_pattern, text, re.MULTILINE))

# Prepare chapters and sections with their start and end positions
chapters = []
for idx, match in enumerate(chapter_matches):
    chapter_name = match.group(1).strip()
    start = match.start()
    end = chapter_matches[idx + 1].start() if idx + 1 < len(chapter_matches) else len(text)
    chapters.append((start, end, chapter_name))

sections = []
for idx, match in enumerate(section_matches):
    section_name = match.group(1).strip()
    start = match.start()
    end = section_matches[idx + 1].start() if idx + 1 < len(section_matches) else len(text)
    sections.append((start, end, section_name))

def find_chapter(pos):
    for start, end, chapter_name in chapters:
        if start <= pos < end:
            return chapter_name, start, end
    return "NO CHAPTER", None, None

def find_section(pos, chapter_start, chapter_end):
    # Find section within chapter boundaries
    for start, end, section_name in sections:
        if chapter_start is not None and chapter_start <= start < chapter_end:
            if start <= pos < end:
                return section_name
    # No section found in chapter up to this article: infer Section 1
    if chapter_start is not None:
        # Check if any section exists in this chapter before this article
        for start, end, section_name in sections:
            if chapter_start <= start < chapter_end and start < pos:
                return section_name
        return "SECTION 1"
    return "NO SECTION"

articles = []
for idx, match in enumerate(article_matches):
    article_name = match.group(1).strip()
    start = match.end()
    end = article_matches[idx + 1].start() if idx + 1 < len(article_matches) else len(text)
    article_body = text[start:end].strip()
    word_count = len(re.findall(r'\w+', article_body))
    article_pos = match.start()
    chapter_name, chapter_start, chapter_end = find_chapter(article_pos)
    section_name = find_section(article_pos, chapter_start, chapter_end)
    articles.append({
        "law_name": law_name,
        "chapter": chapter_name,
        "section": section_name,
        "article_name": article_name,
        "article_length_words": word_count
    })

# Deduplicate by (law_name, chapter, section, article_name), keeping the longest
deduped = {}
for entry in articles:
    key = (entry["law_name"], entry["chapter"], entry["section"], entry["article_name"])
    if key not in deduped or entry["article_length_words"] > deduped[key]["article_length_words"]:
        deduped[key] = entry

deduped_articles = list(deduped.values())

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(deduped_articles, f, indent=2, ensure_ascii=False)

print(f"Metadata for {len(deduped_articles)} unique articles written to {output_file}")
