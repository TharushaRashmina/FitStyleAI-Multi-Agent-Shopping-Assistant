from pathlib import Path
import sys


# -------------------------------------------------
# Paths / imports
# -------------------------------------------------

CURRENT_DIR = Path(__file__).resolve().parent
HYBRID_DIR = CURRENT_DIR.parent / "hybrid"

BASE_DIR = Path(__file__).resolve().parents[2]


if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

if str(HYBRID_DIR) not in sys.path:
    sys.path.append(str(HYBRID_DIR))


# -------------------------------------------------
# Imports
# -------------------------------------------------

from database.sqlserver_repository import (
    SQLServerRepository
)

from search_hybrid import (
    retrieve_bm25,
    retrieve_semantic,
    reciprocal_rank_fusion
)


# -------------------------------------------------
# SQL Server Repository
# -------------------------------------------------

repository = SQLServerRepository()

TOTAL_PRODUCTS = (
    repository.get_product_count()
)


# -------------------------------------------------
# Hybrid + SQL Server Hard Filter Search
# -------------------------------------------------

def search_hybrid_filtered(
    query,
    filters=None,
    top_k=10
):

    filters = filters or {}


    # -------------------------------------------------
    # 1. BM25 ranking
    # -------------------------------------------------

    bm25_results = retrieve_bm25(
        query,
        top_n=TOTAL_PRODUCTS
    )


    # -------------------------------------------------
    # 2. Semantic ranking
    # -------------------------------------------------

    semantic_results = retrieve_semantic(
        query,
        top_n=TOTAL_PRODUCTS
    )


    # -------------------------------------------------
    # 3. Equal Reciprocal Rank Fusion
    # -------------------------------------------------

    fused_results = reciprocal_rank_fusion(
        bm25_results,
        semantic_results
    )


    ranked_ids = [
        str(product_id)
        for product_id, _
        in fused_results
    ]


    score_lookup = {
        str(product_id): float(score)
        for product_id, score
        in fused_results
    }


    # -------------------------------------------------
    # 4. SQL Server hard filters
    # -------------------------------------------------

    eligible_ids = (
        repository.filter_product_ids(
            ranked_ids,
            filters
        )
    )


    # Only fetch the required final products
    selected_ids = (
        eligible_ids[:top_k]
    )


    # -------------------------------------------------
    # 5. Product facts from SQL Server
    # -------------------------------------------------

    products = (
        repository.get_products_by_ids(
            selected_ids
        )
    )


    # -------------------------------------------------
    # 6. Build final results
    # -------------------------------------------------

    results = []


    for product in products:

        product_id = str(
            product["product_id"]
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

            "sub_category":
                product.get(
                    "sub_category",
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

            "fit_type":
                product.get(
                    "fit_type",
                    ""
                ),

            "pattern":
                product.get(
                    "pattern",
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

            "available_any":
                product.get(
                    "available_any"
                ),

            "image_url":
                product.get(
                    "image_url",
                    ""
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

    query = (
        "men formal shirt under 5000"
    )


    filters = {

        "category":
            "tops",

        "target_group":
            "men",

        "style":
            "formal",

        "max_price":
            5000
    }


    results = (
        search_hybrid_filtered(
            query,
            filters,
            top_k=10
        )
    )


    print(
        "\n--- SQL SERVER FILTERED "
        "HYBRID RESULTS ---"
    )

    print(
        "Query:",
        query
    )

    print(
        "Filters:",
        filters
    )

    print(
        "Total Products:",
        TOTAL_PRODUCTS
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
            "RRF Score:",
            round(
                result["rrf_score"],
                6
            )
        )