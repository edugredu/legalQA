import json
import os
from collections import defaultdict

# Input/output paths
input_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'context_articles_limited.json'))
output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'grouped_by_celex_id.json'))

# Load articles
with open(input_path, 'r', encoding='utf-8') as f:
    articles = json.load(f)

# Group by celex_id
grouped = defaultdict(list)
for article in articles:
    celex_id = article.get('celex_id', 'UNKNOWN')
    grouped[celex_id].append(article)

# Sort each group by score descending
for celex_id, items in grouped.items():
    items.sort(key=lambda x: x.get('score', 0), reverse=True)

# Convert defaultdict to dict for JSON serialization
grouped_dict = dict(grouped)

# Save to file
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(grouped_dict, f, indent=2, ensure_ascii=False)

print(f"Grouped {len(articles)} articles into {len(grouped_dict)} celex_id groups. Output written to {output_path}")
