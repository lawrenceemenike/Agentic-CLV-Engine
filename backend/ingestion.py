import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os

class IngestionPipeline:
    def __init__(self, persist_dir="./chroma_db"):
        self.persist_dir = persist_dir
        # Using a fast, local sentence transformer
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = Chroma(embedding_function=self.embeddings, persist_directory=self.persist_dir)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    def ingest_quantitative_features(self, data: list) -> pd.DataFrame:
        """
        Quantitative Feature Ingestion (Epic 1.1)
        """
        df = pd.DataFrame(data)
        
        # Must ingest tenure_months, monthly_fee, feature_utilization, user_ratio, and support_tickets.
        required_cols = ['account_id', 'tenure_months', 'monthly_fee', 'feature_utilization', 'user_ratio', 'support_tickets']
        
        # Ensure all columns exist, add NaN if missing
        for col in required_cols:
            if col not in df.columns:
                df[col] = pd.NA
                
        # Must handle null values via localized forward-filling or statistical median replacement
        # We will use median for numeric features, and ffill for others
        numeric_cols = ['tenure_months', 'monthly_fee', 'feature_utilization', 'user_ratio', 'support_tickets']
        
        for col in numeric_cols:
            median_val = df[col].median()
            if pd.isna(median_val):
                median_val = 0 # Fallback if entirely empty
            df[col] = df[col].fillna(median_val)
            
        df = df.groupby('account_id', group_keys=False).ffill()
        
        print("[INGESTION] Quantitative features processed successfully.")
        return df

    def ingest_unstructured_text(self, text_data: list, metadata_list: list = None):
        """
        Unstructured Text Parsing & RAG Staging (Epic 1.2)
        text_data: list of raw CRM text strings
        """
        if metadata_list is None:
            metadata_list = [{} for _ in text_data]
            
        docs = self.text_splitter.create_documents(text_data, metadatas=metadata_list)
        
        # Persist embeddings locally
        self.vector_store.add_documents(docs)
        print(f"[INGESTION] {len(docs)} chunks vectorized and persisted to {self.persist_dir}.")
        
    def retrieve_context(self, query: str, k: int = 3):
        return self.vector_store.similarity_search(query, k=k)

if __name__ == "__main__":
    # Test Ingestion
    pipeline = IngestionPipeline()
    
    # Test Quant
    mock_data = [
        {'account_id': 'ACC-123', 'tenure_months': 12, 'monthly_fee': 1000, 'feature_utilization': None, 'user_ratio': 0.8, 'support_tickets': 2},
        {'account_id': 'ACC-124', 'tenure_months': None, 'monthly_fee': 1500, 'feature_utilization': 0.9, 'user_ratio': 0.7, 'support_tickets': None}
    ]
    df = pipeline.ingest_quantitative_features(mock_data)
    print(df.head())
    
    # Test RAG
    pipeline.ingest_unstructured_text(["Client mentioned that they are extremely happy.", "They might churn if latency doesn't improve."], [{"account_id": "ACC-123"}, {"account_id": "ACC-124"}])
    res = pipeline.retrieve_context("churn latency", k=1)
    print("RAG Retrieval Test:", res[0].page_content)
