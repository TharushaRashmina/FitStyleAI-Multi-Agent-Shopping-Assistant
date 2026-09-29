from pathlib import Path
import json
import re
import sys

import joblib
import numpy as np

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


# -------------------------------------------------
# Project root
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


# -------------------------------------------------
# Imports
# -------------------------------------------------

from database.sqlserver_repository import (
    SQLServerRepository
)


# -------------------------------------------------
# Paths / Configuration
# -------------------------------------------------

BM25_DIR = (
    BASE_DIR
    / "models"
    / "bm25"
)

BM25_MODEL_FILE = (
    BM25_DIR
    / "bm25_model.joblib"
)

BM25_PRODUCT_IDS_FILE = (
    BM25_DIR
    / "product_ids.json"
)


QDRANT_PATH = (
    BASE_DIR
    / "data"
    / "qdrant"
)

QDRANT_COLLECTION = (
    "fitstyle_products"
)


MODEL_NAME = (
    "sentence-transformers/"
    "all-MiniLM-L6-v2"
)


# -------------------------------------------------
# Repository
# -------------------------------------------------

repository = (
    SQLServerRepository()
)


# -------------------------------------------------
# Tokenizer
# -------------------------------------------------

def tokenize(
    text
):

    text = str(
        text
    ).lower()

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

    bm25_product_ids = (
        json.load(f)
    )


# -------------------------------------------------
# Load Semantic Model
# -------------------------------------------------

semantic_model = (
    SentenceTransformer(
        MODEL_NAME,
        local_files_only=True
    )
)


# -------------------------------------------------
# BM25 Retrieval
# -------------------------------------------------

def retrieve_bm25(
    query,
    top_n=50
):

    query_tokens = tokenize(
        query
    )


    if not query_tokens:

        return []


    scores = (
        bm25.get_scores(
            query_tokens
        )
    )


    ranked_indices = (
        np.argsort(
            scores
        )[::-1][:top_n]
    )


    return [

        str(
            bm25_product_ids[
                index
            ]
        )

        for index
        in ranked_indices
    ]


# -------------------------------------------------
# Qdrant Semantic Retrieval
# -------------------------------------------------

def retrieve_semantic(
    query,
    top_n=50
):

    if not str(
        query
    ).strip():

        return []


    # ---------------------------------------------
    # Convert query to embedding
    # ---------------------------------------------

    query_embedding = (
        semantic_model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )[0]
    )


    # ---------------------------------------------
    # Connect to local Qdrant
    # ---------------------------------------------

    client = QdrantClient(
        path=str(
            QDRANT_PATH
        )
    )


    try:

        response = (
            client.query_points(

                collection_name=
                    QDRANT_COLLECTION,

                query=
                    query_embedding.tolist(),

                limit=
                    top_n,

                with_payload=True
            )
        )


        semantic_results = []


        for point in response.points:

            if not point.payload:
                continue


            product_id = (
                point.payload.get(
                    "product_id"
                )
            )


            if product_id:

                semantic_results.append(
                    str(
                        product_id
                    )
                )


        return semantic_results


    finally:

        client.close()


# -------------------------------------------------
# Reciprocal Rank Fusion
# -------------------------------------------------

def reciprocal_rank_fusion(
    bm25_results,
    semantic_results,
    rrf_k=60
):

    fused_scores = {}


    # ---------------------------------------------
    # BM25 ranking
    # ---------------------------------------------

    for rank, product_id in enumerate(
        bm25_results,
        start=1
    ):

        fused_scores[
            product_id
        ] = (

            fused_scores.get(
                product_id,
                0.0
            )

            +

            1 / (
                rrf_k
                + rank
            )
        )


    # ---------------------------------------------
    # Qdrant semantic ranking
    # ---------------------------------------------

    for rank, product_id in enumerate(
        semantic_results,
        start=1
    ):

        fused_scores[
            product_id
        ] = (

            fused_scores.get(
                product_id,
                0.0
            )

            +

            1 / (
                rrf_k
                + rank
            )
        )


    ranked_products = sorted(

        fused_scores.items(),

        key=lambda item:
            item[1],

        reverse=True
    )


    return ranked_products


# -------------------------------------------------
# Hybrid Search
# -------------------------------------------------

def search_hybrid(
    query,
    top_k=10,
    candidate_count=50
):

    # ---------------------------------------------
    # BM25 candidates
    # ---------------------------------------------

    bm25_results = (
        retrieve_bm25(
            query,
            top_n=candidate_count
        )
    )


    # ---------------------------------------------
    # Qdrant semantic candidates
    # ---------------------------------------------

    semantic_results = (
        retrieve_semantic(
            query,
            top_n=candidate_count
        )
    )


    # ---------------------------------------------
    # Equal RRF
    # ---------------------------------------------

    fused_results = (
        reciprocal_rank_fusion(
            bm25_results,
            semantic_results
        )
    )


    selected_results = (
        fused_results[
            :top_k
        ]
    )


    product_ids = [

        str(
            product_id
        )

        for product_id, _
        in selected_results
    ]


    score_lookup = {

        str(
            product_id
        ):
            float(
                rrf_score
            )

        for product_id, rrf_score
        in selected_results
    }


    # ---------------------------------------------
    # Actual product facts from SQL Server
    # ---------------------------------------------

    products = (
        repository
        .get_products_by_ids(
            product_ids
        )
    )


    # ---------------------------------------------
    # Build output
    # ---------------------------------------------

    results = []


    for product in products:

        product_id = str(
            product[
                "product_id"
            ]
        )


        results.append({

            "product_id":
                product_id,

            "product_name":
                product.get(
                    "product_name",
                    ""
                ),

            "category":
                product.get(
                    "category",
                    ""
                ),

            "target_group":
                product.get(
                    "target_group",
                    ""
                ),

            "material":
                product.get(
                    "material",
                    ""
                ),

            "style":
                product.get(
                    "style",
                    ""
                ),

            "occasion":
                product.get(
                    "occasion",
                    ""
                ),

            "color":
                product.get(
                    "color",
                    ""
                ),

            "base_price":
                product.get(
                    "base_price"
                ),

            "product_url":
                product.get(
                    "product_url",
                    ""
                ),

            "rrf_score":
                score_lookup.get(
                    product_id,
                    0.0
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


    results = (
        search_hybrid(
            query,
            top_k=10
        )
    )


    print(
        f"\n--- BM25 + QDRANT "
        f"HYBRID RESULTS FOR: "
        f"{query} ---"
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
            result[
                "product_id"
            ]
        )

        print(
            "Category:",
            result[
                "category"
            ]
        )

        print(
            "Target:",
            result[
                "target_group"
            ]
        )

        print(
            "Price:",
            result[
                "base_price"
            ]
        )

        print(
            "RRF Score:",
            round(
                result[
                    "rrf_score"
                ],
                6
            )
        )

        print(
            "URL:",
            result[
                "product_url"
            ]
        )