import os
import ast
import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

class LegalDocumentFilter:
    def __init__(self, threshold: float, model_name: str):
        """
        Initialize the LegalDocumentFilter.

        Parameters:
        - threshold (float): Cosine similarity cutoff for filtering.
        - model_name (str): Name of the sentence transformer model.
        """
        self.threshold = threshold
        self.model = SentenceTransformer(model_name)
        self.df = None
        self.query_emb = None
        self.df_filtered = None

    def load_data(self, input_dataframe: pd.DataFrame, nrows = None):
        """Load the CSV data into a DataFrame."""
        self.df = input_dataframe
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

    def save_results(self, output_csv, output_json=None):
        """Save the filtered results to CSV and optionally to JSON."""
        if self.df_filtered is None:
            raise ValueError("No filtered results to save.")
        result = self.df_filtered[['celex_id', 'reference', 'summary', 'filtered_json']]
        result.to_csv(output_csv, index=False)
        if output_json:
            result.to_json(output_json, orient='records', lines=True)
