import os
import ast
import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

class DocumentFilter:
    def __init__(self, threshold=0.5, model_name='jinaai/jina-embeddings-v2-small-en'):
        """
        Initialize the DocumentFilter.

        Parameters:
        - input_csv (str): Path to the input CSV file.
        - threshold (float): Cosine similarity cutoff for filtering.
        - model_name (str): Name of the sentence transformer model.
        """
        self.threshold = threshold
        self.model = SentenceTransformer(model_name)
        self.df = None
        self.query_emb = None

    def load_data(self, nrows=None):
        """Load the CSV data into a DataFrame."""
        self.df = pd.read_csv(self.input_csv)
        if nrows:
            self.df = self.df.head(nrows)

    def set_query(self, query):
        """Set the user query and compute its embedding."""
        self.query_emb = self.model.encode(query, convert_to_numpy=True)

    def _filter_structured(self, sj):
        """
        Parse the structured_json, compute cosine similarity for each article/annex,
        and retain only those above the threshold.
        """
        try:
            data = ast.literal_eval(sj)
        except (ValueError, SyntaxError):
            return {'articles': [], 'annexes': []}

        out = {'articles': [], 'annexes': []}
        for section in ('articles', 'annexes'):
            for elem in data.get(section, []):
                text = elem.get('text', '')
                emb = self.model.encode(text, convert_to_numpy=True)
                score = float(
                    np.dot(self.query_emb, emb) /
                    (np.linalg.norm(self.query_emb) * np.linalg.norm(emb))
                )
                elem['score'] = score
                if score >= self.threshold:
                    out[section].append(elem)
        return out

    def filter_documents(self):
        """Apply filtering to all documents in the DataFrame."""
        if self.df is None or self.query_emb is None:
            raise ValueError("Data not loaded or query not set.")
        self.df['filtered_json'] = self.df['structured_json'].apply(self._filter_structured)
        mask = self.df['filtered_json'].apply(lambda d: len(d['articles']) + len(d['annexes']) > 0)
        self.df_filtered = self.df[mask].copy()
        self.df_filtered['filtered_json'] = self.df_filtered['filtered_json'].apply(json.dumps)
        
        return self.df_filtered

    def save_results(self, output_csv, output_json=None):
        """Save the filtered results to CSV and optionally to JSON."""
        result = self.df_filtered[['celex_id', 'reference', 'summary', 'filtered_json']]
        result.to_csv(output_csv, index=False)
        if output_json:
            result.to_json(output_json, orient='records', lines=True)
            
    def run(self, input_csv, query, nrows=None, output_csv='filtered_laws.csv', output_json=None):
        """
        Run the filtering process.

        Parameters:
        - input_csv (str): Path to the input CSV file.
        - query (str): User query for filtering.
        - nrows (int): Number of rows to read from the CSV.
        - output_csv (str): Path to save the filtered results in CSV format.
        - output_json (str): Path to save the filtered results in JSON format.
        """
        self.input_csv = input_csv
        self.load_data(nrows)
        self.set_query(query)
        dataframe = self.filter_documents()

        return dataframe

# Example usage:
#filterer = DocumentFilter(threshold=0.5, model_name='jinaai/jina-embeddings-v2-small-en')
#dataframe = filterer.run('input.csv', "Your query here", nrows=5)
#filterer.save_results('filtered_laws.csv', 'filtered_laws.json')


