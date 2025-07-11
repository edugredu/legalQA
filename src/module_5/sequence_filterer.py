import json
import re
import pandas as pd

class SequenceFilterer:
    def __init__(self, minimum_length_limit=20, max_added_word_limit=10000):
        self.minimum_length_limit = minimum_length_limit
        self.max_added_word_limit = max_added_word_limit

    def _clean_json_str(self, raw_str: str) -> str:
        """Ultra-robust JSON string cleaning."""
        import re
        
        # Step 1: Decode unicode escapes
        try:
            decoded = bytes(raw_str, "utf-8").decode("unicode_escape")
        except:
            decoded = raw_str
        
        # Step 2: Remove ALL control characters completely
        # This removes characters 0-31 (except \n, \r, \t) and 127-159
        cleaned = ''.join(char for char in decoded if ord(char) >= 32 or char in '\n\r\t')
        
        # Step 3: Handle problematic Unicode characters
        cleaned = re.sub(r'[\u00A0\u1680\u180E\u2000-\u200B\u202F\u205F\u3000\uFEFF]', ' ', cleaned)
        
        # Step 4: The key fix - properly escape ALL special characters within JSON strings
        # We need to parse the structure and escape content within quotes
        
        result = ""
        i = 0
        in_string = False
        
        while i < len(cleaned):
            char = cleaned[i]
            
            if char == '"' and (i == 0 or cleaned[i-1] != '\\'):
                # Toggle string state
                in_string = not in_string
                result += char
            elif in_string:
                # We're inside a JSON string value - escape special characters
                if char == '\\':
                    result += '\\\\'
                elif char == '"':
                    result += '\\"'
                elif char == '\n':
                    result += '\\n'
                elif char == '\r':
                    result += '\\r'
                elif char == '\t':
                    result += '\\t'
                elif char == '\b':
                    result += '\\b'
                elif char == '\f':
                    result += '\\f'
                elif ord(char) < 32:
                    # Any remaining control character - escape as unicode
                    result += f'\\u{ord(char):04x}'
                else:
                    result += char
            else:
                # We're in JSON structure (outside strings)
                result += char
            
            i += 1
        
        return result

    def _parse_and_flatten(self, celex_id: str, filtered_json_str: str) -> list:
        """Decode, clean, parse JSON, flatten articles, sort by score."""
        try:
            cleaned = self._clean_json_str(filtered_json_str)
            obj = json.loads(cleaned)
            articles = []
            for art in obj.get("articles", []):
                flat = dict(art)
                flat["celex_id"] = celex_id
                articles.append(flat)
            return sorted(articles, key=lambda x: x.get("score", 0), reverse=True)
        except Exception as e:
            print(f"Parse error for {celex_id}: {e}")
            print(f"Problematic JSON: {filtered_json_str[:200]}...")
            return []

    def _filter_by_word_count(self, articles: list) -> list:
        """Select articles above min length and within total-word cap."""
        selected, total = [], 0
        for art in articles:
            text = art.get("text", "")
            wc = len(re.findall(r'\w+', text))
            if wc < self.minimum_length_limit: 
                continue
            if total + wc > self.max_added_word_limit:
                break
            selected.append(art)
            total += wc
        return selected

    def add_processed_column(self, df: pd.DataFrame,
                           source_column: str = "filtered_json") -> pd.DataFrame:
        """
        Returns a copy of `df` with one new column:
        - processed_text: concatenated text of filtered articles per row
        """
        def _process(row):
            cid = row["celex_id"]
            raw = row[source_column]
            if pd.isna(cid) or pd.isna(raw):
                return ""
            arts = self._parse_and_flatten(cid, raw)
            filt = self._filter_by_word_count(arts)
            text = "\n\n".join(a.get("text", "") for a in filt)
            return text

        out = df.copy()
        out["processed_text"] = df.apply(_process, axis=1)
        return out


    def aggregate_all_articles(self, df: pd.DataFrame, title_df: pd.DataFrame = None, 
                          source_column: str = "filtered_json") -> dict:
        """
        Aggregate all articles from all rows into a single JSON structure,
        sorted by descending score, maintaining all original information plus celex_id
        and law titles (if title_df is provided).
        
        Args:
            df: Main DataFrame with articles data
            title_df: DataFrame with celex_id and title columns (optional)
            source_column: Column name containing the JSON data
        
        Returns:
            dict: JSON-like structure with 'articles' key containing all aggregated articles
        """
        all_articles = []
        
        # Create title mapping if title_df is provided
        title_mapping = {}
        if title_df is not None:
            title_mapping = dict(zip(title_df['celex_id'], title_df['title']))
        
        # Process each row in the dataframe
        for idx, row in df.iterrows():
            cid = row.get("celex_id")
            raw = row.get(source_column)
            
            if pd.isna(cid) or pd.isna(raw):
                continue
                
            # Parse and flatten articles from this row
            arts = self._parse_and_flatten(cid, raw)
            
            # Apply word count filtering
            filt = self._filter_by_word_count(arts)
            
            # Add law title to each article if title mapping is available
            if title_mapping:
                for article in filt:
                    celex_id = article.get('celex_id')
                    law_title = title_mapping.get(celex_id, 'Unknown Law')
                    article['law_title'] = law_title
            
            # Add filtered articles to the aggregated list
            all_articles.extend(filt)
        
        # Sort all articles by descending score
        all_articles_sorted = sorted(all_articles, key=lambda x: x.get("score", 0), reverse=True)
        
        # Create final JSON structure
        final_json = {
            "articles": all_articles_sorted,
            "total_articles": len(all_articles_sorted),
            "includes_law_titles": title_mapping is not None
        }
        
        return final_json
    
    
    def generate_text_prompt(self, aggregated_json: dict) -> str:
        """
        Generate a text prompt where each paragraph is introduced by the law title
        followed by the relevant articles of that law.
        
        Args:
            aggregated_json: The dictionary returned by aggregate_all_articles()
        
        Returns:
            str: Clean text with one paragraph per law, introduced by law title
        """
        from collections import defaultdict
        
        articles = aggregated_json.get('articles', [])
        grouped = defaultdict(list)
        
        # Group articles by celex_id, preserving law titles
        for article in articles:
            celex_id = article.get('celex_id', 'UNKNOWN')
            text = article.get('text', '')
            law_title = article.get('law_title', 'Unknown Law')
            
            if text:  # Only add non-empty texts
                grouped[celex_id].append({
                    'text': text,
                    'law_title': law_title.strip()  # Remove any trailing newlines
                })
        
        # Create formatted paragraphs
        paragraphs = []
        for celex_id, articles_info in grouped.items():
            if articles_info:
                # Use the law title from the first article (all should be the same)
                law_title = articles_info[0]['law_title']
                
                # Extract just the texts
                texts = [article['text'] for article in articles_info]
                
                # Create paragraph: law title + articles
                paragraph = f"{law_title}\n\n" + "\n\n".join(texts)
                paragraphs.append(paragraph)
        
        # Join all paragraphs with triple newlines for clear separation
        final_text = "\n\n\n".join(paragraphs)
        return final_text


