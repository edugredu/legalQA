import pyterrier as pt
import datasets
import pandas as pd
from pathlib import Path
import re
dataset = datasets.load_dataset("jonathanli/eurlex")

# RRF - Reciprocal Rank Fusion
def rrf(dfs, i=1, K=100):
    scores = {}

    for df in dfs:
        for _, row in df.iterrows():
            docno = row["docno"]
            rrf_score = (1 / (i+row["rank"]))
            if docno in scores:
                scores[docno] += rrf_score
            else:
                scores[docno] = rrf_score
    # main_qid is used here to evaluate performance of merged data frame
    merged_df = pd.DataFrame(
        [{"qid": '1', "docno": k, "score": v} for k, v in sorted(scores.items(), key=lambda item: item[1], reverse=True)] 
    )
    # print(merged_df[merged_df["docno"]==244319])
    merged_df["rank"] = list(range(len(merged_df)))
    if K>len(merged_df):
        K = len(merged_df)
    return merged_df[:K]

# Combine all parts of the dataset into one
ds1 = dataset['train'].to_pandas()
ds2 = dataset['test'].to_pandas()
ds3 = dataset['validation'].to_pandas()
ds4 = pd.concat([ds1, ds2], axis=0)
pd_ds = pd.concat([ds4, ds3], axis=0)

# Create index for dataset text
index_ref = None
cache_dir = Path("cache/")
index_dir = cache_dir / "indices" / "eur_lex"

pd_ds_rename = pd_ds.rename(columns={'celex_id': 'docno'}, inplace=False)

pd_ds_dict = pd_ds_rename.to_dict(orient='records')

try:
    index_ref = pt.IndexFactory.of(str(index_dir.absolute()))
except:
    indexer = pt.index.IterDictIndexer(str(index_dir.absolute()))
    index_ref = indexer.index(
        pd_ds_dict
    )   

# Create index for dataset titles
index_ref_title = None
cache_dir = Path("cache/")
index_dir2 = cache_dir / "indices" / "eur_lex_titles"

pd_ds_rename = pd_ds.rename(columns={'celex_id': 'docno', 'text':'not_text', 'title':'text'}, inplace=False)

pd_ds_dict = pd_ds_rename.to_dict(orient='records')

try:
    index_ref_title = pt.IndexFactory.of(str(index_dir2.absolute()))
except:
    indexer_title = pt.index.IterDictIndexer(str(index_dir2.absolute()))
    index_ref_title = indexer_title.index(
        pd_ds_dict
    )   

# BM25 IR models for text and title of dataset documents
bm25_text = pt.terrier.Retriever(index_ref, wmodel="BM25")
bm25_title = pt.terrier.Retriever(index_ref_title, wmodel="BM25")

# retrieves relevant documents given both text and title
#  performs RRF to give single combined result of top-K documents
def get_text(row):
    return list(pd_ds[pd_ds['celex_id']==row['docno']]['text'])[0]

def get_title(row):
    return list(pd_ds[pd_ds['celex_id']==row['docno']]['title'])[0]

def get_eurovoc_concepts(row):
    return list(pd_ds[pd_ds['celex_id']==row['docno']]['eurovoc_concepts'])[0]

def retrieve_docs(query, K=10):
    re_query = re.sub(r'[^A-Za-z0-9\s]', '', query)
    retr_text = bm25_text.search(re_query)
    retr_title = bm25_title.search(re_query)
    results = rrf([retr_text, retr_title], K=K)
    results['title'] = results.apply(get_title, axis=1, raw=False)
    results['text'] = results.apply(get_text, axis=1, raw=False)
    results['eurovoc_concepts'] = results.apply(get_eurovoc_concepts, axis=1, raw=False)
    results.rename(columns={'docno': 'celex_id'}, inplace=True)
    results = results[['celex_id', 'title', 'text', 'eurovoc_concepts']]
    results.to_csv('/app/src/module_2/outputs/sample3.csv', index=False)
    # return results


with open("/app/src/module_1/outputs/sample3.txt", "r", encoding="utf-8") as f:
    input_query = f.read().strip()

retrieve_docs(input_query)