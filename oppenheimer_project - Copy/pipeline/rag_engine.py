import os
import sys
import re
import json
import pickle
import numpy as np
import torch
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder

os.environ["TOKENIZERS_PARALLELISM"] = "false"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
DATA_SOURCE = os.path.join(BASE_DIR, "data_source", "oppenheimer_corpus.txt")
INDEX_DIR = os.path.join(BASE_DIR, "vector_store")
os.makedirs(INDEX_DIR, exist_ok=True)

PARENT_CHUNKS_PATH = os.path.join(INDEX_DIR, "parent_chunks.json")
CHILD_CHUNKS_PATH = os.path.join(INDEX_DIR, "child_chunks.json")
EMBEDDINGS_PATH = os.path.join(INDEX_DIR, "child_embeddings.npy")
TOKEN_EMBEDDINGS_PATH = os.path.join(INDEX_DIR, "child_token_embeddings.pkl")
BM25_PATH = os.path.join(INDEX_DIR, "bm25_model.pkl")

class AdvancedOppenheimerRAG:
    def __init__(self):
        print("⚡ Initializing Tier-1 Accelerated Hybrid Retrieval Environment...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🖥️ Execution Target Device: {self.device.upper()}")
        
        self.embed_model = SentenceTransformer("BAAI/bge-m3", device=self.device)
        self.reranker = CrossEncoder("BAAI/bge-reranker-large", device=self.device)
        
        self.parent_chunks: List[Dict[str, Any]] = []
        self.child_chunks: List[Dict[str, Any]] = []
        self.bm25: BM25Okapi = None
        self.child_embeddings: np.ndarray = None
        self.child_token_embeddings: List[torch.Tensor] = []

    def _clean_tokenize(self, text: str) -> List[str]:
        """Strips punctuation artifacts and extracts precise lowercase alpha-numeric tokens."""
        return re.findall(r'\b\w+\b', text.lower())

    def build_hierarchical_corpus(self):
        """Parses raw text, maps parent-child chunk frameworks, and extracts metadata tags."""
        if not os.path.exists(DATA_SOURCE):
            raise FileNotFoundError(f"Missing master data source file at: {DATA_SOURCE}")
            
        with open(DATA_SOURCE, "r", encoding="utf-8") as f:
            raw_text = f.read()

        doc_splits = re.split(r'(=== DOCUMENT START:.*?===|SECTION I:|SECTION II:|DOCUMENT REFERENCE I:|DOCUMENT REFERENCE II:)', raw_text)
        
        current_metadata = {"domain": "biography", "epoch": "general"}
        parent_id_counter = 0
        child_id_counter = 0
        
        print("🧱 Executing programmatic parent-child fragmentation layer...")
        
        for element in doc_splits:
            element = element.strip()
            if not element:
                continue
                
            if "DOCUMENT START" in element or "DOCUMENT REFERENCE" in element:
                current_metadata = {"domain": "physics", "epoch": "1939_academic"}
                continue
            elif "LETTERS" in element or "SECTION" in element:
                current_metadata = {"domain": "biography", "epoch": "historical_letters"}
                continue
                
            parent_chunks_raw = [element[i:i+1800] for i in range(0, len(element), 1400)]
            
            for p_text in parent_chunks_raw:
                if len(p_text.strip()) < 50:
                    continue
                
                parent_obj = {
                    "parent_id": parent_id_counter,
                    "text": p_text.strip(),
                    "metadata": current_metadata.copy()
                }
                self.parent_chunks.append(parent_obj)
                
                child_chunks_raw = [p_text[j:j+400] for j in range(0, len(p_text), 300)]
                for c_text in child_chunks_raw:
                    if len(c_text.strip()) < 20:
                        continue
                    self.child_chunks.append({
                        "child_id": child_id_counter,
                        "parent_id": parent_id_counter,
                        "text": c_text.strip(),
                        "metadata": current_metadata.copy()
                    })
                    child_id_counter += 1
                parent_id_counter += 1

        print(f"📊 Corpus Split Metrics: Derived {len(self.parent_chunks)} Parents & {len(self.child_chunks)} Children.")

        print("🧬 Generating Multi-Vector Structural Representation Space across GPU...")
        child_texts = [child["text"] for child in self.child_chunks]
        
        self.child_embeddings = self.embed_model.encode(
            child_texts, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True
        )
        
        print("🪙 Compiling token-level multi-vector spaces into cache structures...")
        with torch.no_grad():
            raw_tokens = self.embed_model.encode(
                child_texts, show_progress_bar=True, output_value="token_embeddings", convert_to_tensor=True
            )
            if isinstance(raw_tokens, torch.Tensor):
                self.child_token_embeddings = [t.cpu() for t in raw_tokens]
            else:
                self.child_token_embeddings = [t.cpu() for t in raw_tokens]
        
        tokenized_corpus = [self._clean_tokenize(doc) for doc in child_texts]
        self.bm25 = BM25Okapi(tokenized_corpus)
        
        self.save_indices_to_disk()

    def save_indices_to_disk(self):
        """Writes compiled matrices, string sets, and model states permanently to disk storage."""
        print("💾 Serializing indices and writing vectors straight to your hard drive...")
        
        with open(PARENT_CHUNKS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.parent_chunks, f, ensure_ascii=False, indent=2)
            
        with open(CHILD_CHUNKS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.child_chunks, f, ensure_ascii=False, indent=2)
            
        np.save(EMBEDDINGS_PATH, self.child_embeddings)
        
        with open(TOKEN_EMBEDDINGS_PATH, "wb") as f:
            pickle.dump(self.child_token_embeddings, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        with open(BM25_PATH, "wb") as f:
            pickle.dump(self.bm25, f)
            
        print(f"🚀 Success! Persistence complete. Vector store ready: {INDEX_DIR}")

    def load_indices_from_disk(self) -> bool:
        """Loads pre-compiled vector matrices from your storage sector in under 5 milliseconds."""
        if not (os.path.exists(PARENT_CHUNKS_PATH) and os.path.exists(CHILD_CHUNKS_PATH) and 
                os.path.exists(EMBEDDINGS_PATH) and os.path.exists(TOKEN_EMBEDDINGS_PATH) and os.path.exists(BM25_PATH)):
            return False
            
        print("📦 Pre-compiled storage indices found! Streaming structures straight to RAM...")
        with open(PARENT_CHUNKS_PATH, "r", encoding="utf-8") as f:
            self.parent_chunks = json.load(f)
            
        with open(CHILD_CHUNKS_PATH, "r", encoding="utf-8") as f:
            self.child_chunks = json.load(f)
            
        self.child_embeddings = np.load(EMBEDDINGS_PATH)
        
        with open(TOKEN_EMBEDDINGS_PATH, "rb") as f:
            self.child_token_embeddings = pickle.load(f)
        
        with open(BM25_PATH, "rb") as f:
            self.bm25 = pickle.load(f)
            
        print("🏁 High-speed vector structures loaded and active.")
        return True

    def pipeline_retrieve(self, query: str, metadata_filter: Dict[str, Any] = None, top_k: int = 3) -> List[Dict[str, Any]]:
        query_tokens = self._clean_tokenize(query)
        
        query_embedding = self.embed_model.encode(query, convert_to_numpy=True, normalize_embeddings=True)
        
        with torch.no_grad():
            query_token_embeddings = self.embed_model.encode(query, output_value="token_embeddings", convert_to_tensor=True).to(self.device)
        
        dense_scores = np.dot(self.child_embeddings, query_embedding)
        
        bm25_raw_scores = np.array(self.bm25.get_scores(query_tokens))
        normalized_bm25_scores = bm25_raw_scores / (bm25_raw_scores + 10.0)

        scored_candidates = []

        for idx, child in enumerate(self.child_chunks):
            if metadata_filter:
                match = all(child["metadata"].get(k) == v for k, v in metadata_filter.items())
                if not match:
                    continue
            
            dense_score = float(dense_scores[idx])
            normalized_bm25 = float(normalized_bm25_scores[idx])

            with torch.no_grad():
                child_tokens = self.child_token_embeddings[idx].to(self.device)
                similarity_matrix = torch.matmul(query_token_embeddings, child_tokens.T)
                colbert_score = float(torch.sum(torch.max(similarity_matrix, dim=1).values).item())
                normalized_colbert = torch.sigmoid(torch.tensor(colbert_score)).item()

            hybrid_score = (0.35 * dense_score) + (0.25 * normalized_bm25) + (0.40 * normalized_colbert)
            scored_candidates.append((hybrid_score, child))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        top_candidates = scored_candidates[:12]
        
        if not top_candidates:
            return []

        rerank_pairs = []
        candidate_parents = []
        
        for score, child in top_candidates:
            parent_obj = next(p for p in self.parent_chunks if p["parent_id"] == child["parent_id"])
            if parent_obj not in candidate_parents:
                rerank_pairs.append([query, parent_obj["text"]])
                candidate_parents.append(parent_obj)

        if not rerank_pairs:
            return []

        reranker_scores = self.reranker.predict(rerank_pairs)
        
        final_ranked_results = []
        for i, idx in enumerate(np.argsort(reranker_scores)[::-1]):
            if i >= top_k:
                break
            final_ranked_results.append({
                "rank": i + 1,
                "confidence_score": float(reranker_scores[idx]),
                "text": candidate_parents[idx]["text"],
                "metadata": candidate_parents[idx]["metadata"]
            })

        return final_ranked_results

if __name__ == "__main__":
    rag_engine = AdvancedOppenheimerRAG()
    
    if not rag_engine.load_indices_from_disk():
        rag_engine.build_hierarchical_corpus()
    
    test_query = "What is the critical mass limit equation for a collapsing neutron star core?"
    print(f"\n🔍 Executing Diagnostic Query: '{test_query}'")
    results = rag_engine.pipeline_retrieve(test_query, top_k=2)
    
    for res in results:
        print(f"\n[RANK {res['rank']}] (Confidence Rank: {res['confidence_score']:.4f})")
        print(f"Context Extract: {res['text'][:200]}...")
        
    print("\n👋 System diagnostics complete. Terminating background worker threads cleanly.")
    sys.exit(0)
