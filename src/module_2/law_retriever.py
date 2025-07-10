import re
import pandas as pd
import pyterrier as pt
from pathlib import Path
import datasets


class LawRetriever:
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self.cache_dir = Path("cache/")
        self.index_dir = self.cache_dir / "indices" / "eur_lex"
        self.index_dir_title = self.cache_dir / "indices" / "eur_lex_titles"
        self.dataset = datasets.load_dataset(self.dataset_path)
        if isinstance(self.dataset, datasets.DatasetDict):
            ds1 = self.dataset['train'].to_pandas()
            ds2 = self.dataset['test'].to_pandas()
            ds3 = self.dataset['validation'].to_pandas()
            ds4 = pd.concat([ds1, ds2], axis=0)
            self.dataset = pd.concat([ds4, ds3], axis=0)
        self.dataset = self.dataset.rename(columns={'celex_id': 'docno'}, inplace=False)
        self.dataset = self.dataset.to_dict(orient='records')

        try:
            self.index_ref = pt.IndexFactory.of(str(self.index_dir.absolute()))
        except:
            indexer = pt.index.IterDictIndexer(str(self.index_dir.absolute()))
            self.index_ref = indexer.index(
                self.dataset
            )

        # BM25 IR models for text and title of dataset documents
        self.bm25_text = pt.terrier.Retriever(self.index_ref, wmodel="BM25")
        self.bm25_title = pt.terrier.Retriever(self.index_ref_title, wmodel="BM25")

    def get_text(self, row):
        return list(self.dataset[self.dataset['docno']==row['docno']]['text'])[0]

    def get_title(self, row):
        return list(self.dataset[self.dataset['docno']==row['docno']]['title'])[0]

    def retrieve_docs(self, query, K=10):
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
        
        
        re_query = re.sub(r'[^A-Za-z0-9\s]', '', query)
        retr_text = self.bm25_text.search(re_query)
        retr_title = self.bm25_title.search(re_query)
        results = rrf([retr_text, retr_title], K=K)
        results['title'] = results.apply(self.get_title, axis=1, raw=False)
        results['text'] = results.apply(self.get_text, axis=1, raw=False)
        results['eurovoc_concepts'] = results.apply(self.get_eurovoc_concepts, axis=1, raw=False)
        results.rename(columns={'docno': 'celex_id'}, inplace=True)
        results = results[['celex_id', 'title', 'text', 'eurovoc_concepts']]
        #results.to_csv('/app/src/module_2/outputs/sample3.csv', index=False)
        return results
        
    def run(self, query: str):
        return self.retrieve_docs(query)