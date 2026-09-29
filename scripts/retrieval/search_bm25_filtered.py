from pathlib import Path
import json
import re
import sys

import joblib
import numpy as np
import pandas as pd


# -------------------------------------------------
# Allow import from current folder
# -------------------------------------------------

CURRENT_DIR = Path(__file__).resolve().parent

if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from hard_filters import apply_hard_filters


# -------------------------------------------------
# Paths
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

PRODUCTS_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "products_final.csv"
)

BM25_DIR = BASE_DIR / "models" / "bm25"

BM25_MODEL_FILE = (
    BM25_DIR
    / "bm25_model.joblib"
)

PRODUCT_IDS_FILE = (
    BM25_DIR
    / "product_ids.json"
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
# Load data
# -------------------------------------------------

products = pd.read_csv(
    PRODUCTS_FILE,
    dtype={"product_id": str}
)

products["product_id"] = (
    products["product_id"]
    .astype(str)
)

product_lookup = products.set_index(
    "product_id",
    drop=False
)


# -------------------------------------------------
# Load BM25
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


# -------------------------------------------------
# BM25 + Hard Filter Search
# -------------------------------------------------

def search_bm25_filtered(
    query,
    filters,
    top_k=10
):

    query_tokens = tokenize(
        query
    )

    if not query_tokens:
        return []

    # BM25 scores for all products
    scores = bm25.get_scores(
        query_tokens
    )

    # Apply hard filters to all products
    eligible_ids = apply_hard_filters(
        product_ids,
        filters
    )

    eligible_set = set(
        eligible_ids
    )

    # Rank all products by BM25
    ranked_indices = np.argsort(
        scores
    )[::-1]

    results = []

    for index in ranked_indices:

        product_id = str(
            product_ids[index]
        )

        # Skip products that fail hard filters
        if product_id not in eligible_set:
            continue

        if product_id not in product_lookup.index:
            continue

        product = product_lookup.loc[
            product_id
        ]

        results.append({
            "product_id": product_id,

            "product_name": product.get(
                "product_name", ""
            ),

            "category": product.get(
                "category", ""
            ),

            "target_group": product.get(
                "target_group", ""
            ),

            "material": product.get(
                "material", ""
            ),

            "style": product.get(
                "style", ""
            ),

            "occasion": product.get(
                "occasion", ""
            ),

            "color": product.get(
                "color", ""
            ),

            "base_price": product.get(
                "base_price", ""
            ),

            "product_url": product.get(
                "product_url", ""
            ),

            "bm25_score": float(
                scores[index]
            )
        })

        if len(results) >= top_k:
            break

    return results


# -------------------------------------------------
# Test Q001
# -------------------------------------------------

if __name__ == "__main__":

    query = (
        "men formal shirt under 5000"
    )

    filters = {
        "category": "tops",
        "target_group": "men",
        "style": "formal",
        "max_price": 5000
    }

    results = search_bm25_filtered(
        query,
        filters,
        top_k=10
    )

    print(
        f"\n--- FILTERED BM25 RESULTS FOR: {query} ---"
    )

    print(
        "Filters:",
        filters
    )

    for rank, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\n{rank}. "
            f"{result['product_name']}"
        )

        print(
            "Product ID:",
            result["product_id"]
        )

        print(
            "Category:",
            result["category"]
        )

        print(
            "Target:",
            result["target_group"]
        )

        print(
            "Style:",
            result["style"]
        )

        print(
            "Price:",
            result["base_price"]
        )

        print(
            "BM25 Score:",
            round(
                result["bm25_score"],
                4
            )
        )