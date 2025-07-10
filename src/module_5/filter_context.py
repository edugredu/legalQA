import json
import re
import os

# User hyperparameter: set the word limit here
minimum_length_limit = 20  # First we set a minimum length to be considered
max_added_word_limit = 10000  # Change this value as needed

# Input/output paths
input_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'all_articles_flat_sorted.json'))
output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'context_articles_limited.json'))

# Load articles
with open(input_path, 'r', encoding='utf-8') as f:
    articles = json.load(f)

selected_articles = []
total_words = 0

# Filter out articles that are too short
for article in articles:
    text = article.get('text', '')
    word_count = len(re.findall(r'\w+', text))
    if word_count < minimum_length_limit:
        continue
    if total_words + word_count > max_added_word_limit:
        break
    selected_articles.append(article)
    total_words += word_count

# Save the selected articles to a new JSON file
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(selected_articles, f, indent=2, ensure_ascii=False)

print(f"Saved {len(selected_articles)} articles with a total of {total_words} words to {output_path}")
