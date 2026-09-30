from pathlib import Path
import json

import joblib
import pandas as pd
from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity


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

MODEL_DIR = BASE_DIR / "models" / "tfidf"

VECTORIZER_FILE = MODEL_DIR / "tfidf_vectorizer.joblib"
MATRIX_FILE = MODEL_DIR / "tfidf_matrix.npz"
PRODUCT_IDS_FILE = MODEL_DIR / "product_ids.json"


# -------------------------------------------------
# Load data and TF-IDF model
# -------------------------------------------------

products = pd.read_csv(
    PRODUCTS_FILE,
    dtype={"product_id": str}
)

vectorizer = joblib.load(
    VECTORIZER_FILE
)

tfidf_matrix = load_npz(
    MATRIX_FILE
)

with open(
    PRODUCT_IDS_FILE,
    "r",
    encoding="utf-8"
) as f:
    product_ids = json.load(f)


# Product lookup
products["product_id"] = products["product_id"].astype(str)

product_lookup = products.set_index(
    "product_id",
    drop=False
)


# -------------------------------------------------
# TF-IDF search
# -------------------------------------------------

def search_tfidf(query, top_k=10):

    query_vector = vectorizer.transform(
        [query]
    )

    # Query contains no known vocabulary
    if query_vector.nnz == 0:
        return []

    scores = cosine_similarity(
        query_vector,
        tfidf_matrix
    ).flatten()

    ranked_indices = scores.argsort()[::-1]

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
            "tfidf_score": float(
                scores[index]
            )
        })

    return results


# -------------------------------------------------
# Test query
# -------------------------------------------------

if __name__ == "__main__":

    query = input(
        "\nEnter fashion query: "
    )

    results = search_tfidf(
        query,
        top_k=10
    )

    print(
        f"\n--- TF-IDF RESULTS FOR: {query} ---"
    )

    if not results:
        print("No matching results found.")

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
            "TF-IDF Score:",
            round(
                result["tfidf_score"],
                4
            )
        )

        print(
            "URL:",
            result["product_url"]
        )