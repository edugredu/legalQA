import json
import os

# Input/output paths
input_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'grouped_by_celex_id.json'))
output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'llm_context.txt'))

# Load grouped articles
with open(input_path, 'r', encoding='utf-8') as f:
    grouped = json.load(f)

lines = []
for celex_id, articles in grouped.items():
    law_text = '\n'.join(article.get('text', '').strip() for article in articles if article.get('text'))
    if law_text:
        lines.append(f"===== LAW: {celex_id} =====\n{law_text}\n\n")

with open(output_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"LLM context file written to {output_path}")
