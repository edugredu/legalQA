# module_2.py
import pyterrier as pt
import datasets
import pandas as pd
from pathlib import Path
import re

# Global variables for lazy initialization
_dataset = None
_pd_ds = None
_index_ref = None
_index_ref_title = None
_bm25_text = None
_bm25_title = None
_initialized = False

def _initialize():
    """Initialize the retrieval system (called once)"""
    global _dataset, _pd_ds, _index_ref, _index_ref_title, _bm25_text, _bm25_title, _initialized
    print("····")
    
    if _initialized:
        return
    
    # Initialize PyTerrier if not already done
    if not pt.started():
        pt.init()
    
    # Load dataset
    _dataset = datasets.load_dataset("jonathanli/eurlex")
    
    # Combine all parts of the dataset into one
    ds1 = _dataset['train'].to_pandas()
    ds2 = _dataset['test'].to_pandas()
    ds3 = _dataset['validation'].to_pandas()
    ds4 = pd.concat([ds1, ds2], axis=0)
    _pd_ds = pd.concat([ds4, ds3], axis=0)
    
    # Create index for dataset text
    cache_dir = Path("cache/")
    index_dir = cache_dir / "indices" / "eur_lex"
    
    pd_ds_rename = _pd_ds.rename(columns={'celex_id': 'docno'}, inplace=False)
    pd_ds_dict = pd_ds_rename.to_dict(orient='records')
    
    try:
        _index_ref = pt.IndexFactory.of(str(index_dir.absolute()))
    except:
        indexer = pt.index.IterDictIndexer(str(index_dir.absolute()))
        _index_ref = indexer.index(pd_ds_dict)
        
    
    # Create index for dataset titles
    index_dir2 = cache_dir / "indices" / "eur_lex_titles"
    
    pd_ds_rename_title = _pd_ds.rename(columns={'celex_id': 'docno', 'text':'not_text', 'title':'text'}, inplace=False)
    pd_ds_dict_title = pd_ds_rename_title.to_dict(orient='records')
    
    try:
        _index_ref_title = pt.IndexFactory.of(str(index_dir2.absolute()))
    except:
        indexer_title = pt.index.IterDictIndexer(str(index_dir2.absolute()))
        _index_ref_title = indexer_title.index(pd_ds_dict_title)
    
    # BM25 IR models for text and title of dataset documents
    _bm25_text = pt.terrier.Retriever(_index_ref, wmodel="BM25")
    _bm25_title = pt.terrier.Retriever(_index_ref_title, wmodel="BM25")
    
    _initialized = True

def _rrf(dfs, i=1, K=100):
    """RRF - Reciprocal Rank Fusion"""
    scores = {}
    for df in dfs:
        for _, row in df.iterrows():
            docno = row["docno"]
            rrf_score = (1 / (i + row["rank"]))
            if docno in scores:
                scores[docno] += rrf_score
            else:
                scores[docno] = rrf_score
    
    merged_df = pd.DataFrame(
        [{"qid": '1', "docno": k, "score": v} for k, v in sorted(scores.items(), key=lambda item: item[1], reverse=True)]
    )
    merged_df["rank"] = list(range(len(merged_df)))
    if K > len(merged_df):
        K = len(merged_df)
        
    return merged_df[:K]

def _get_text(row):
    return list(_pd_ds[_pd_ds['celex_id'] == row['docno']]['text'])[0]

def _get_title(row):
    return list(_pd_ds[_pd_ds['celex_id'] == row['docno']]['title'])[0]

def _get_eurovoc_concepts(row):
    return list(_pd_ds[_pd_ds['celex_id'] == row['docno']]['eurovoc_concepts'])[0]

def run_module_2(user_prompt, K=0.5):
    """
    Main function to retrieve documents based on user prompt with a score threshold.
    
    Args:
        user_prompt (str): The query string from the user
        K (float): The minimum score threshold to include documents (default: 0.5)
    
    Returns:
        pandas.DataFrame: DataFrame with results containing celex_id, score, title, text, and eurovoc_concepts
        At least 2 laws will be returned regardless of threshold.
    """
    # Initialize if not already done
    _initialize()
    
    # Clean the query
    re_query = re.sub(r'[^A-Za-z0-9\s]', '', user_prompt)
    
    # Retrieve documents from both text and title indices
    retr_text = _bm25_text.search(re_query)
    retr_title = _bm25_title.search(re_query)
    
    # Apply RRF to combine results (get more results to ensure proper filtering)
    all_results = _rrf([retr_text, retr_title], K=10)
    
    # Filter by score threshold
    filtered_results = all_results[all_results['score'] >= K]
    
    # Ensure at least 2 laws are returned
    if len(filtered_results) < 2:
        filtered_results = all_results.head(2)
    
    # Add metadata columns
    filtered_results['title'] = filtered_results.apply(_get_title, axis=1, raw=False)
    filtered_results['text'] = filtered_results.apply(_get_text, axis=1, raw=False)
    filtered_results['eurovoc_concepts'] = filtered_results.apply(_get_eurovoc_concepts, axis=1, raw=False)
    
    # Rename and select final columns
    filtered_results.rename(columns={'docno': 'celex_id'}, inplace=True)
    filtered_results = filtered_results[['celex_id', 'score', 'title', 'text', 'eurovoc_concepts']]
    
    return filtered_results, filtered_results['title'].tolist()
