from pathlib import Path
import sys


# -------------------------------------------------
# Project paths
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

RETRIEVAL_DIR = (
    BASE_DIR
    / "scripts"
    / "retrieval"
)

if str(RETRIEVAL_DIR) not in sys.path:
    sys.path.append(str(RETRIEVAL_DIR))


# -------------------------------------------------
# Import final retrieval pipeline
# -------------------------------------------------

from search_hybrid_filtered import (
    search_hybrid_filtered
)

from database.sqlserver_repository import (
    SQLServerRepository
)


# -------------------------------------------------
# Product Retrieval Agent
# -------------------------------------------------

class ProductRetrievalAgent:

    def __init__(self, default_top_k=10):

        self.name = "Product Retrieval Agent"

        self.default_top_k = (
            default_top_k
        )

        self.retrieval_method = (
            "BM25 + Qdrant Semantic + "
            "Equal RRF + SQL Server Hard Filters"
        )

        # Used for a final exclusion pass after the
        # normal hybrid retrieval pipeline.
        self.repository = SQLServerRepository()


    # ---------------------------------------------
    # Validate input
    # ---------------------------------------------

    def _validate_input(
        self,
        query,
        filters
    ):

        if not query:
            raise ValueError(
                "Query cannot be empty."
            )

        if not isinstance(query, str):
            raise TypeError(
                "Query must be a string."
            )

        if filters is None:
            filters = {}

        if not isinstance(filters, dict):
            raise TypeError(
                "Filters must be a dictionary."
            )

        return (
            query.strip(),
            filters
        )


    # ---------------------------------------------
    # Retrieve products
    # ---------------------------------------------

    def retrieve(
        self,
        query,
        filters=None,
        exclusions=None,
        top_k=None
    ):

        query, filters = (
            self._validate_input(
                query,
                filters
            )
        )

        if top_k is None:
            top_k = self.default_top_k

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        results = (
            search_hybrid_filtered(
                query=query,
                filters=filters,
                top_k=top_k
            )
        )

        exclusions = exclusions or []

        # Apply explicit negative constraints after
        # the normal positive hard-filter pipeline.
        # This keeps existing retrieval behavior intact
        # while guaranteeing "do not / except / without"
        # constraints at the structured-data layer.
        if exclusions and results:

            ranked_ids = [
                str(product["product_id"])
                for product in results
            ]

            allowed_ids = (
                self.repository.filter_product_ids(
                    ranked_ids,
                    {
                        "exclusions":
                            exclusions
                    }
                )
            )

            allowed_set = set(
                allowed_ids
            )

            results = [
                product
                for product in results
                if str(
                    product.get(
                        "product_id"
                    )
                ) in allowed_set
            ]

        return {
            "agent": self.name,

            "status": "success",

            "query": query,

            "filters": filters,

            "exclusions":
                exclusions,

            "retrieval_method":
                self.retrieval_method,

            "result_count":
                len(results),

            "products":
                results
        }


    # ---------------------------------------------
    # Standard Agent Interface
    # ---------------------------------------------

    def run(self, input_data):

        if not isinstance(
            input_data,
            dict
        ):
            raise TypeError(
                "Agent input must be "
                "a dictionary."
            )

        query = input_data.get(
            "query",
            ""
        )

        filters = input_data.get(
            "filters",
            {}
        )

        exclusions = input_data.get(
            "exclusions",
            []
        )

        if exclusions is None:
            exclusions = []

        if not isinstance(
            exclusions,
            list
        ):
            raise TypeError(
                "Exclusions must be a list."
            )

        top_k = input_data.get(
            "top_k",
            self.default_top_k
        )

        return self.retrieve(
            query=query,
            filters=filters,
            exclusions=exclusions,
            top_k=top_k
        )


# -------------------------------------------------
# Test
# -------------------------------------------------

if __name__ == "__main__":

    agent = ProductRetrievalAgent(
        default_top_k=10
    )

    test_input = {

        "query":
            "men formal shirt under 5000",

        "filters": {
            "category": "tops",
            "target_group": "men",
            "style": "formal",
            "max_price": 5000
        },

        "top_k": 5
    }

    response = agent.run(
        test_input
    )

    print(
        "\n--- PRODUCT RETRIEVAL AGENT ---"
    )

    print(
        "Agent:",
        response["agent"]
    )

    print(
        "Method:",
        response[
            "retrieval_method"
        ]
    )

    print(
        "Query:",
        response["query"]
    )

    print(
        "Filters:",
        response["filters"]
    )

    print(
        "Results:",
        response["result_count"]
    )


    for rank, product in enumerate(
        response["products"],
        start=1
    ):

        print(
            f"\n{rank}. "
            f"{product['product_name']}"
        )

        print(
            "Product ID:",
            product["product_id"]
        )

        print(
            "Price:",
            product["base_price"]
        )

        print(
            "RRF Score:",
            round(
                product["rrf_score"],
                6
            )
        )
