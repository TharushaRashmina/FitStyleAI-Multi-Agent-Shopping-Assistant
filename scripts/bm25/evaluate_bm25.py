from pathlib import Path
import json
import math
import re

import joblib
import numpy as np
import pandas as pd


# -------------------------------------------------
# Paths
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

GROUND_TRUTH_FILE = (
    BASE_DIR
    / "evaluation"
    / "ground_truth_queries.json"
)

MODEL_DIR = BASE_DIR / "models" / "bm25"

BM25_MODEL_FILE = MODEL_DIR / "bm25_model.joblib"
PRODUCT_IDS_FILE = MODEL_DIR / "product_ids.json"

OUTPUT_FILE = (
    BASE_DIR
    / "evaluation"
    / "bm25_evaluation.csv"
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
# Load model and ground truth
# -------------------------------------------------

bm25 = joblib.load(
    BM25_MODEL_FILE
)

with open(
    PRODUCT_IDS_FILE,
    "r",
    encoding="utf-8"
) as f:
    product_ids = json.load(f)

with open(
    GROUND_TRUTH_FILE,
    "r",
    encoding="utf-8"
) as f:
    ground_truth = json.load(f)


# -------------------------------------------------
# Retrieval
# -------------------------------------------------

def retrieve(query, top_k=10):

    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    scores = bm25.get_scores(
        query_tokens
    )

    ranked_indices = np.argsort(
        scores
    )[::-1]

    return [
        str(product_ids[index])
        for index in ranked_indices[:top_k]
    ]


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

    retrieved = retrieve(
        query,
        top_k=TOP_K
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

print("\n--- BM25 EVALUATION ---")

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