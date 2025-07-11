import ast
import json
import numpy as np
import pandas as pd
from typing import Optional
from sentence_transformers import SentenceTransformer

def run_module_4(df: pd.DataFrame, query: str, threshold: float = 0.5, model_name: str = 'jinaai/jina-embeddings-v2-small-en') -> pd.DataFrame:
    """
    Filter laws dataframe based on similarity of articles and annexes to the query.

    Args:
        df (pd.DataFrame): DataFrame containing laws with a 'structured_json' column.
        query (str): Query text to compare against.
        threshold (float): Similarity threshold for filtering (0-1). Default: 0.5.
        model_name (str): SentenceTransformer model name. Default: 'jinaai/jina-embeddings-v2-small-en'.

    Returns:
        pd.DataFrame: Filtered DataFrame with columns ['celex_id', 'filtered_json'].
                     Only contains rows where at least one article or annex meets the threshold.

    Raises:
        ValueError: If required columns are missing from the input DataFrame.
        Exception: If model loading fails.
    """
    
    # Validate input DataFrame
    required_columns = ['structured_json', 'celex_id']
    missing_columns = [col for col in required_columns if col not in df.columns]
    print(missing_columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    
    # Initialize the sentence transformer model
    try:
        model = SentenceTransformer(model_name)
    except Exception as e:
        raise Exception(f"Failed to load model '{model_name}': {str(e)}")
    
    # Encode the query
    query_emb = model.encode(query, convert_to_numpy=True)

    def filter_structured(data: dict):
        """
        Parse the Python-style JSON in sj, compute cosine similarity of each
        article/annex text to the query, add 'score' and keep only elements
        with score >= threshold.
        """
        # Parse Python-dict string
        # try:
        #     #data = ast.literal_eval(sj)
        # except (ValueError, SyntaxError):
        #     return {'articles': [], 'annexes': []}

        out = {'articles': [], 'annexes': []}
        
        for section in ('articles', 'annexes'):
            for elem in data.get(section, []):
                text = elem.get('text', '')
                if not text:  # Skip empty texts
                    continue
                    
                # Embed and compute cosine similarity
                emb = model.encode(text, convert_to_numpy=True)
                score = float(
                    np.dot(query_emb, emb) /
                    (np.linalg.norm(query_emb) * np.linalg.norm(emb))
                )
                elem['score'] = score
                if score >= threshold:
                    out[section].append(elem)
        return out

    # Create a copy of the DataFrame to avoid modifying the original
    df_copy = df.copy()
    
    print("a filtrar")
    # Apply filtering
    df_copy['filtered_json'] = df_copy['structured_json'].apply(filter_structured)

    # Keep only rows with at least one match
    mask = df_copy['filtered_json'].apply(lambda d: len(d['articles']) + len(d['annexes']) > 0)
    df_filtered = df_copy[mask].copy()

    # Convert filtered dict back to JSON string
    df_filtered['filtered_json'] = df_filtered['filtered_json'].apply(json.dumps)

    # Select relevant columns and return
    result = df_filtered[['celex_id', 'filtered_json']]
    return result

def load_query_from_file(query_file: str) -> str:
    """
    Helper function to load query from a text file.
    
    Args:
        query_file (str): Path to the query text file.
        
    Returns:
        str: Query text content.
    """
    with open(query_file, 'r', encoding='utf-8') as f:
        return f.read().strip()

def save_filtered_laws(df: pd.DataFrame, output_path: str) -> None:
    """
    Helper function to save filtered laws to CSV.
    
    Args:
        df (pd.DataFrame): Filtered DataFrame to save.
        output_path (str): Path where to save the CSV file.
    """
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    