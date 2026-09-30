from pathlib import Path
import json
import re

import joblib
import numpy as np
import pandas as pd


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

MODEL_DIR = BASE_DIR / "models" / "bm25"

BM25_MODEL_FILE = MODEL_DIR / "bm25_model.joblib"
PRODUCT_IDS_FILE = MODEL_DIR / "product_ids.json"


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

bm25 = joblib.load(
    BM25_MODEL_FILE
)

with open(
    PRODUCT_IDS_FILE,
    "r",
    encoding="utf-8"
) as f:
    product_ids = json.load(f)


products["product_id"] = (
    products["product_id"]
    .astype(str)
)

product_lookup = products.set_index(
    "product_id",
    drop=False
)


# -------------------------------------------------
# BM25 search
# -------------------------------------------------

def search_bm25(query, top_k=10):

    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    scores = bm25.get_scores(
        query_tokens
    )

    ranked_indices = np.argsort(
        scores
    )[::-1]

    results = []

    for index in ranked_indices[:top_k]:

        product_id = str(
            product_ids[index]
        )

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

    return results


# -------------------------------------------------
# Test
# -------------------------------------------------

if __name__ == "__main__":

    query = input(
        "\nEnter fashion query: "
    )

    results = search_bm25(
        query,
        top_k=10
    )

    print(
        f"\n--- BM25 RESULTS FOR: {query} ---"
    )

    if not results:
        print(
            "No matching results found."
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

        print(
            "URL:",
            result["product_url"]
        )