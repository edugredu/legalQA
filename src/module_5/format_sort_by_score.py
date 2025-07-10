import json
import re

results = []

# Read the entire file as a single string
with open('/app/src/module_4/output/filtered_laws.json', 'r', encoding='utf-8') as f:
    text = f.read()

# Regex to match each object containing both celex_id and filtered_json
pattern = (
    r'"celex_id"\s*:\s*"([^"]+)"'           # Capture celex_id
    r'(?:.|\n)*?'                           # Non-greedy match up to filtered_json
    r'"filtered_json"\s*:\s*"((?:\\.|[^"\\])*)"'  # Capture filtered_json string
)

matches = re.findall(pattern, text)

for celex_id, filtered_json_str in matches:
    try:
        # First, decode the double-escaped string
        filtered_json_decoded = bytes(filtered_json_str, "utf-8").decode("unicode_escape")
        # Now parse as JSON
        filtered_json_obj = json.loads(filtered_json_decoded)
        for article in filtered_json_obj.get("articles", []):
            flat_article = dict(article)
            flat_article["celex_id"] = celex_id
            results.append(flat_article)
    except Exception as e:
        print(f"Error parsing filtered_json for celex_id {celex_id}: {e}")

# Sort by score descending
results.sort(key=lambda x: x.get("score", 0), reverse=True)

with open('all_articles_flat_sorted.json', 'w', encoding='utf-8') as out:
    json.dump(results, out, indent=4, ensure_ascii=False)

print(f"Extracted and sorted {len(results)} articles.")
