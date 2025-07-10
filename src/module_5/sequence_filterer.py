import json
import re
import pandas as pd

class SequenceFilterer:
    def __init__(self, minimum_length_limit=20, max_added_word_limit=10000):
        self.minimum_length_limit = minimum_length_limit
        self.max_added_word_limit = max_added_word_limit

    def _parse_and_flatten(self, celex_id, filtered_json_str):
        """Decode and flatten articles, adding celex_id and sorting by score."""
        try:
            filtered_json_decoded = bytes(filtered_json_str, "utf-8").decode("unicode_escape")
            filtered_json_obj = json.loads(filtered_json_decoded)
            articles = []
            for article in filtered_json_obj.get("articles", []):
                flat_article = dict(article)
                flat_article["celex_id"] = celex_id
                articles.append(flat_article)
            articles.sort(key=lambda x: x.get("score", 0), reverse=True)
            return articles
        except Exception as e:
            print(f"Error parsing filtered_json for celex_id {celex_id}: {e}")
            return []

    def _filter_by_word_count(self, articles):
        """Filter articles by minimum length and limit total words."""
        selected = []
        total_words = 0
        for article in articles:
            text = article.get('text', '')
            word_count = len(re.findall(r'\\w+', text))
            if word_count < self.minimum_length_limit:
                continue
            if total_words + word_count > self.max_added_word_limit:
                break
            selected.append(article)
            total_words += word_count
        return selected

    def add_processed_column(self, df, source_column='filtered_json'):
        """
        Adds a new column 'processed_articles' to the DataFrame.
        Each row contains a list of filtered and sorted articles with celex_id.
        """
        processed = []
        for idx, row in df.iterrows():
            celex_id = row.get('celex_id', None)
            filtered_json_str = row.get(source_column, None)
            if celex_id is None or filtered_json_str is None:
                processed.append([])
                continue
            articles = self._parse_and_flatten(celex_id, filtered_json_str)
            filtered = self._filter_by_word_count(articles)
            processed.append(filtered)
        df = df.copy()
        df['processed_articles'] = processed
        return df
