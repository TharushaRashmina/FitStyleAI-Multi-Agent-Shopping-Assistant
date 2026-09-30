from pathlib import Path
import sys

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
# Configuration
# -------------------------------------------------

QDRANT_PATH = (
    BASE_DIR
    / "data"
    / "qdrant"
)

COLLECTION_NAME = (
    "fitstyle_products"
)

MODEL_NAME = (
    "sentence-transformers/"
    "all-MiniLM-L6-v2"
)


# -------------------------------------------------
# Semantic search
# -------------------------------------------------

def search_qdrant(
    query,
    top_k=10
):

    model = SentenceTransformer(
        MODEL_NAME,
        local_files_only=True
    )

    client = QdrantClient(
        path=str(QDRANT_PATH)
    )

    repository = SQLServerRepository()


    try:

        # -----------------------------------------
        # Convert query into embedding
        # -----------------------------------------

        query_vector = (
            model.encode(
                query,
                normalize_embeddings=True
            )
        )


        # -----------------------------------------
        # Search Qdrant
        # -----------------------------------------

        response = (
            client.query_points(
                collection_name=
                    COLLECTION_NAME,

                query=
                    query_vector.tolist(),

                limit=
                    top_k,

                with_payload=True
            )
        )


        points = response.points


        # -----------------------------------------
        # Extract product IDs
        # -----------------------------------------

        product_ids = [

            str(
                point.payload[
                    "product_id"
                ]
            )

            for point in points
        ]


        score_lookup = {

            str(
                point.payload[
                    "product_id"
                ]
            ):
                float(
                    point.score
                )

            for point in points
        }


        # -----------------------------------------
        # Product facts from SQL Server
        # -----------------------------------------

        products = (
            repository
            .get_products_by_ids(
                product_ids
            )
        )


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

                "style":
                    product.get(
                        "style",
                        ""
                    ),

                "base_price":
                    product.get(
                        "base_price"
                    ),

                "semantic_score":
                    score_lookup.get(
                        product_id,
                        0.0
                    )
            })


        return results


    finally:

        client.close()


# -------------------------------------------------
# Test
# -------------------------------------------------

if __name__ == "__main__":

    query = (
        "men formal shirt"
    )


    results = search_qdrant(
        query,
        top_k=10
    )


    print(
        "\n--- QDRANT SEMANTIC SEARCH ---"
    )

    print(
        "Query:",
        query
    )

    print(
        "Results:",
        len(results)
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
            "Semantic Score:",
            round(
                result[
                    "semantic_score"
                ],
                6
            )
        )