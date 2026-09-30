from pathlib import Path
import json
import math
import sys

import pandas as pd


# -------------------------------------------------
# Paths / imports
# -------------------------------------------------

CURRENT_DIR = Path(__file__).resolve().parent
HYBRID_DIR = CURRENT_DIR.parent / "hybrid"

if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

if str(HYBRID_DIR) not in sys.path:
    sys.path.append(str(HYBRID_DIR))

from hard_filters import apply_hard_filters

from search_hybrid import (
    retrieve_bm25,
    retrieve_semantic
)


BASE_DIR = Path(__file__).resolve().parents[2]

PRODUCTS_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "products_final.csv"
)

GROUND_TRUTH_FILE = (
    BASE_DIR
    / "evaluation"
    / "ground_truth_queries.json"
)

SUMMARY_OUTPUT_FILE = (
    BASE_DIR
    / "evaluation"
    / "weighted_hybrid_summary.csv"
)

DETAIL_OUTPUT_FILE = (
    BASE_DIR
    / "evaluation"
    / "weighted_hybrid_evaluation.csv"
)


# -------------------------------------------------
# Load products
# -------------------------------------------------

products = pd.read_csv(
    PRODUCTS_FILE,
    dtype={"product_id": str}
)

TOTAL_PRODUCTS = len(products)


# -------------------------------------------------
# Load ground truth
# -------------------------------------------------

with open(
    GROUND_TRUTH_FILE,
    "r",
    encoding="utf-8"
) as f:
    ground_truth = json.load(f)


# -------------------------------------------------
# Weighted Reciprocal Rank Fusion
# -------------------------------------------------

def weighted_rrf(
    bm25_results,
    semantic_results,
    bm25_weight,
    semantic_weight,
    rrf_k=60
):

    fused_scores = {}

    # BM25 contribution
    for rank, product_id in enumerate(
        bm25_results,
        start=1
    ):
        fused_scores[product_id] = (
            fused_scores.get(product_id, 0.0)
            + (
                bm25_weight
                / (rrf_k + rank)
            )
        )

    # Semantic contribution
    for rank, product_id in enumerate(
        semantic_results,
        start=1
    ):
        fused_scores[product_id] = (
            fused_scores.get(product_id, 0.0)
            + (
                semantic_weight
                / (rrf_k + rank)
            )
        )

    ranked = sorted(
        fused_scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    return [
        product_id
        for product_id, _ in ranked
    ]


# -------------------------------------------------
# Weighted Hybrid + Hard Filters
# -------------------------------------------------

def retrieve_weighted_hybrid(
    query,
    filters,
    bm25_weight,
    semantic_weight,
    top_k=10
):

    # Rank entire collection
    bm25_results = retrieve_bm25(
        query,
        top_n=TOTAL_PRODUCTS
    )

    semantic_results = retrieve_semantic(
        query,
        top_n=TOTAL_PRODUCTS
    )

    fused_ids = weighted_rrf(
        bm25_results,
        semantic_results,
        bm25_weight,
        semantic_weight
    )

    # Apply exact structured constraints
    filtered_ids = apply_hard_filters(
        fused_ids,
        filters
    )

    return filtered_ids[:top_k]


# -------------------------------------------------
# Metrics
# -------------------------------------------------

def precision_at_k(retrieved, relevant, k):

    relevant_found = sum(
        1
        for product_id in retrieved[:k]
        if product_id in relevant
    )

    return relevant_found / k


def recall_at_k(retrieved, relevant, k):

    if not relevant:
        return 0.0

    relevant_found = sum(
        1
        for product_id in retrieved[:k]
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
# Weight combinations
# -------------------------------------------------

WEIGHT_CONFIGS = [
    (0.5, 0.5),
    (0.6, 0.4),
    (0.7, 0.3),
    (0.8, 0.2)
]

TOP_K = 10

summary_results = []
detail_results = []


# -------------------------------------------------
# Evaluate each weight configuration
# -------------------------------------------------

for bm25_weight, semantic_weight in WEIGHT_CONFIGS:

    config_results = []

    print(
        "\n---------------------------------------"
    )

    print(
        f"BM25={bm25_weight} | "
        f"Semantic={semantic_weight}"
    )

    print(
        "---------------------------------------"
    )

    for item in ground_truth:

        query_id = item["query_id"]
        query = item["query"]

        filters = item.get(
            "filters",
            {}
        )

        relevant = set(
            str(product_id)
            for product_id
            in item["relevant_product_ids"]
        )

        retrieved = retrieve_weighted_hybrid(
            query=query,
            filters=filters,
            bm25_weight=bm25_weight,
            semantic_weight=semantic_weight,
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

        result = {
            "bm25_weight": bm25_weight,
            "semantic_weight": semantic_weight,
            "query_id": query_id,
            "query": query,
            "relevant_count": len(relevant),
            "retrieved_count": len(retrieved),
            "precision@10": precision,
            "recall@10": recall,
            "f1@10": f1,
            "ndcg@10": ndcg
        }

        config_results.append(
            result
        )

        detail_results.append(
            result
        )

    config_df = pd.DataFrame(
        config_results
    )

    avg_precision = (
        config_df["precision@10"].mean()
    )

    avg_recall = (
        config_df["recall@10"].mean()
    )

    avg_f1 = (
        config_df["f1@10"].mean()
    )

    avg_ndcg = (
        config_df["ndcg@10"].mean()
    )

    summary_results.append({
        "bm25_weight": bm25_weight,
        "semantic_weight": semantic_weight,
        "precision@10": avg_precision,
        "recall@10": avg_recall,
        "f1@10": avg_f1,
        "ndcg@10": avg_ndcg
    })

    print(
        "Precision@10:",
        round(avg_precision, 4)
    )

    print(
        "Recall@10:",
        round(avg_recall, 4)
    )

    print(
        "F1@10:",
        round(avg_f1, 4)
    )

    print(
        "NDCG@10:",
        round(avg_ndcg, 4)
    )


# -------------------------------------------------
# Save detailed results
# -------------------------------------------------

detail_df = pd.DataFrame(
    detail_results
)

detail_df.to_csv(
    DETAIL_OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# -------------------------------------------------
# Save summary
# -------------------------------------------------

summary_df = pd.DataFrame(
    summary_results
)

summary_df.to_csv(
    SUMMARY_OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# -------------------------------------------------
# Find best configuration
# -------------------------------------------------

best_row = summary_df.sort_values(
    by=[
        "f1@10",
        "ndcg@10"
    ],
    ascending=False
).iloc[0]


print(
    "\n======================================="
)

print(
    "BEST WEIGHT CONFIGURATION"
)

print(
    "======================================="
)

print(
    "BM25 weight:",
    best_row["bm25_weight"]
)

print(
    "Semantic weight:",
    best_row["semantic_weight"]
)

print(
    "Precision@10:",
    round(
        best_row["precision@10"],
        4
    )
)

print(
    "Recall@10:",
    round(
        best_row["recall@10"],
        4
    )
)

print(
    "F1@10:",
    round(
        best_row["f1@10"],
        4
    )
)

print(
    "NDCG@10:",
    round(
        best_row["ndcg@10"],
        4
    )
)

print(
    "\nCreated:"
)

print(
    SUMMARY_OUTPUT_FILE
)

print(
    DETAIL_OUTPUT_FILE
)