from pathlib import Path
import json
import math
import re

import joblib
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


# -------------------------------------------------
# Paths
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

GROUND_TRUTH_FILE = (
    BASE_DIR
    / "evaluation"
    / "ground_truth_queries.json"
)

BM25_DIR = BASE_DIR / "models" / "bm25"
SEMANTIC_DIR = BASE_DIR / "models" / "semantic"

BM25_MODEL_FILE = BM25_DIR / "bm25_model.joblib"
BM25_PRODUCT_IDS_FILE = BM25_DIR / "product_ids.json"

SEMANTIC_EMBEDDINGS_FILE = (
    SEMANTIC_DIR / "product_embeddings.npy"
)

SEMANTIC_PRODUCT_IDS_FILE = (
    SEMANTIC_DIR / "product_ids.json"
)

SEMANTIC_MODEL_INFO_FILE = (
    SEMANTIC_DIR / "model_info.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "evaluation"
    / "hybrid_evaluation.csv"
)


# -------------------------------------------------
# Tokenizer
# -------------------------------------------------

def tokenize(text):
    text = str(text).lower()

    return re.findall(
        r"\b[a-z0-9]+\b",
        text
    )


# -------------------------------------------------
# Load BM25
# -------------------------------------------------

bm25 = joblib.load(
    BM25_MODEL_FILE
)

with open(
    BM25_PRODUCT_IDS_FILE,
    "r",
    encoding="utf-8"
) as f:
    bm25_product_ids = json.load(f)


# -------------------------------------------------
# Load Semantic model
# -------------------------------------------------

semantic_embeddings = np.load(
    SEMANTIC_EMBEDDINGS_FILE
)

with open(
    SEMANTIC_PRODUCT_IDS_FILE,
    "r",
    encoding="utf-8"
) as f:
    semantic_product_ids = json.load(f)

with open(
    SEMANTIC_MODEL_INFO_FILE,
    "r",
    encoding="utf-8"
) as f:
    model_info = json.load(f)

MODEL_NAME = model_info["model_name"]

semantic_model = SentenceTransformer(
    MODEL_NAME,
    local_files_only=True
)


# -------------------------------------------------
# Load Ground Truth
# -------------------------------------------------

with open(
    GROUND_TRUTH_FILE,
    "r",
    encoding="utf-8"
) as f:
    ground_truth = json.load(f)


# -------------------------------------------------
# BM25 retrieval
# -------------------------------------------------

def retrieve_bm25(query, top_n=50):

    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    scores = bm25.get_scores(
        query_tokens
    )

    ranked_indices = np.argsort(
        scores
    )[::-1][:top_n]

    return [
        str(bm25_product_ids[index])
        for index in ranked_indices
    ]


# -------------------------------------------------
# Semantic retrieval
# -------------------------------------------------

def retrieve_semantic(query, top_n=50):

    query_embedding = semantic_model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )[0]

    scores = np.dot(
        semantic_embeddings,
        query_embedding
    )

    ranked_indices = np.argsort(
        scores
    )[::-1][:top_n]

    return [
        str(semantic_product_ids[index])
        for index in ranked_indices
    ]


# -------------------------------------------------
# Reciprocal Rank Fusion
# -------------------------------------------------

def reciprocal_rank_fusion(
    bm25_results,
    semantic_results,
    rrf_k=60
):

    fused_scores = {}

    for rank, product_id in enumerate(
        bm25_results,
        start=1
    ):
        fused_scores[product_id] = (
            fused_scores.get(product_id, 0.0)
            + 1 / (rrf_k + rank)
        )

    for rank, product_id in enumerate(
        semantic_results,
        start=1
    ):
        fused_scores[product_id] = (
            fused_scores.get(product_id, 0.0)
            + 1 / (rrf_k + rank)
        )

    ranked_products = sorted(
        fused_scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    return [
        product_id
        for product_id, _ in ranked_products
    ]


# -------------------------------------------------
# Hybrid retrieval
# -------------------------------------------------

def retrieve_hybrid(
    query,
    top_k=10,
    candidate_count=50
):

    bm25_results = retrieve_bm25(
        query,
        top_n=candidate_count
    )

    semantic_results = retrieve_semantic(
        query,
        top_n=candidate_count
    )

    fused_results = reciprocal_rank_fusion(
        bm25_results,
        semantic_results
    )

    return fused_results[:top_k]


# -------------------------------------------------
# Metrics
# -------------------------------------------------

def precision_at_k(retrieved, relevant, k):

    retrieved_k = retrieved[:k]

    if not retrieved_k:
        return 0.0

    relevant_found = sum(
        1
        for product_id in retrieved_k
        if product_id in relevant
    )

    return relevant_found / k


def recall_at_k(retrieved, relevant, k):

    if not relevant:
        return 0.0

    retrieved_k = retrieved[:k]

    relevant_found = sum(
        1
        for product_id in retrieved_k
        if product_id in relevant
    )

    return relevant_found / len(relevant)


def f1_score(precision, recall):

    if precision + recall == 0:
        return 0.0

    return (
        2 * precision * recall
        / (precision + recall)
    )


def ndcg_at_k(retrieved, relevant, k):

    dcg = 0.0

    for rank, product_id in enumerate(
        retrieved[:k],
        start=1
    ):

        relevance = (
            1 if product_id in relevant else 0
        )

        dcg += relevance / math.log2(
            rank + 1
        )

    ideal_relevant_count = min(
        len(relevant),
        k
    )

    idcg = sum(
        1 / math.log2(rank + 1)
        for rank in range(
            1,
            ideal_relevant_count + 1
        )
    )

    if idcg == 0:
        return 0.0

    return dcg / idcg


# -------------------------------------------------
# Evaluate
# -------------------------------------------------

TOP_K = 10

results = []

for item in ground_truth:

    query_id = item["query_id"]
    query = item["query"]

    relevant = set(
        str(product_id)
        for product_id
        in item["relevant_product_ids"]
    )

    retrieved = retrieve_hybrid(
        query,
        top_k=TOP_K,
        candidate_count=50
    )

    precision = precision_at_k(
        retrieved,
        relevant,
        TOP_K
    )

    recall = recall_at_k(
        retrieved,
        relevant,
        TOP_K
    )

    f1 = f1_score(
        precision,
        recall
    )

    ndcg = ndcg_at_k(
        retrieved,
        relevant,
        TOP_K
    )

    results.append({
        "query_id": query_id,
        "query": query,
        "relevant_count": len(relevant),
        "precision@10": precision,
        "recall@10": recall,
        "f1@10": f1,
        "ndcg@10": ndcg
    })


# -------------------------------------------------
# Save
# -------------------------------------------------

results_df = pd.DataFrame(results)

results_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# -------------------------------------------------
# Print
# -------------------------------------------------

print("\n--- HYBRID EVALUATION ---")

for _, row in results_df.iterrows():

    print(
        f"{row['query_id']} | "
        f"P@10={row['precision@10']:.3f} | "
        f"R@10={row['recall@10']:.3f} | "
        f"F1@10={row['f1@10']:.3f} | "
        f"NDCG@10={row['ndcg@10']:.3f}"
    )


print("\n--- AVERAGE RESULTS ---")

print(
    "Precision@10:",
    round(
        results_df["precision@10"].mean(),
        4
    )
)

print(
    "Recall@10:",
    round(
        results_df["recall@10"].mean(),
        4
    )
)

print(
    "F1@10:",
    round(
        results_df["f1@10"].mean(),
        4
    )
)

print(
    "NDCG@10:",
    round(
        results_df["ndcg@10"].mean(),
        4
    )
)

print(
    "\nCreated:",
    OUTPUT_FILE
)