from pathlib import Path
import json

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


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

MODEL_DIR = BASE_DIR / "models" / "semantic"

EMBEDDINGS_FILE = MODEL_DIR / "product_embeddings.npy"
PRODUCT_IDS_FILE = MODEL_DIR / "product_ids.json"
MODEL_INFO_FILE = MODEL_DIR / "model_info.json"


# -------------------------------------------------
# Load model information
# -------------------------------------------------

with open(
    MODEL_INFO_FILE,
    "r",
    encoding="utf-8"
) as f:
    model_info = json.load(f)

MODEL_NAME = model_info["model_name"]


# -------------------------------------------------
# Load semantic model
# -------------------------------------------------

model = SentenceTransformer(
    MODEL_NAME,
    local_files_only=True
)


# -------------------------------------------------
# Load products and embeddings
# -------------------------------------------------

products = pd.read_csv(
    PRODUCTS_FILE,
    dtype={"product_id": str}
)

embeddings = np.load(
    EMBEDDINGS_FILE
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
# Semantic search
# -------------------------------------------------

def search_semantic(query, top_k=10):

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )[0]

    # Product embeddings and query embedding
    # are normalized, so dot product =
    # cosine similarity
    scores = np.dot(
        embeddings,
        query_embedding
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

            "semantic_score": float(
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

    results = search_semantic(
        query,
        top_k=10
    )

    print(
        f"\n--- SEMANTIC RESULTS FOR: {query} ---"
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
            "Semantic Score:",
            round(
                result["semantic_score"],
                4
            )
        )

        print(
            "URL:",
            result["product_url"]
        )