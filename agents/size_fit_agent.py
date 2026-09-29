from pathlib import Path
import sys


# -------------------------------------------------
# Project root
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


# -------------------------------------------------
# Import SQL Server repository
# -------------------------------------------------

from database.sqlserver_repository import (
    SQLServerRepository
)


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def normalize_size(value):

    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .upper()
    )


# -------------------------------------------------
# Size / Fit Agent
# -------------------------------------------------

class SizeFitAgent:

    def __init__(self):

        self.name = "Size/Fit Agent"

        self.repository = (
            SQLServerRepository()
        )


    # -------------------------------------------------
    # Get available variants
    # -------------------------------------------------

    def get_available_variants(
        self,
        product_id
    ):

        variants = (
            self.repository
            .get_available_variants(
                product_id
            )
        )

        available_variants = []

        for variant in variants:

            size = normalize_size(
                variant.get(
                    "size"
                )
            )

            if not size:
                continue

            available_variants.append({

                "variant_id":
                    str(
                        variant.get(
                            "variant_id",
                            ""
                        )
                    ),

                "size":
                    size,

                "available":
                    True,

                "price":
                    variant.get(
                        "price"
                    ),

                "color":
                    variant.get(
                        "color"
                    ),

                "sku":
                    variant.get(
                        "sku"
                    )
            })

        return available_variants


    # -------------------------------------------------
    # Get available sizes
    # -------------------------------------------------

    def get_available_sizes(
        self,
        product_id
    ):

        available_variants = (
            self.get_available_variants(
                product_id
            )
        )

        sizes = []

        for variant in available_variants:

            size = variant[
                "size"
            ]

            if size not in sizes:

                sizes.append(
                    size
                )

        return sizes


    # -------------------------------------------------
    # Check one product
    # -------------------------------------------------

    def check_product(
        self,
        product_id,
        requested_size=None
    ):

        product_id = str(
            product_id
        )

        product = (
            self.repository
            .get_product_by_id(
                product_id
            )
        )


        # Product not found
        if product is None:

            return {

                "product_id":
                    product_id,

                "status":
                    "product_not_found",

                "requested_size":
                    requested_size,

                "size_available":
                    False,

                "available_sizes":
                    [],

                "matching_variants":
                    []
            }


        available_variants = (
            self.get_available_variants(
                product_id
            )
        )

        available_sizes = (
            self.get_available_sizes(
                product_id
            )
        )


        # -----------------------------------------
        # No size requested
        # -----------------------------------------

        if requested_size is None:

            return {

                "product_id":
                    product_id,

                "product_name":
                    product.get(
                        "product_name",
                        ""
                    ),

                "status":
                    "size_not_requested",

                "requested_size":
                    None,

                "size_available":
                    None,

                "available_sizes":
                    available_sizes,

                "matching_variants":
                    []
            }


        # -----------------------------------------
        # Size requested
        # -----------------------------------------

        requested_size = (
            normalize_size(
                requested_size
            )
        )


        matching_variants = [

            variant

            for variant
            in available_variants

            if variant[
                "size"
            ] == requested_size
        ]


        # Repository-level exact check
        size_available = (
            self.repository
            .has_available_size(
                product_id,
                requested_size
            )
        )


        return {

            "product_id":
                product_id,

            "product_name":
                product.get(
                    "product_name",
                    ""
                ),

            "status":
                (
                    "size_available"
                    if size_available
                    else
                    "size_not_available"
                ),

            "requested_size":
                requested_size,

            "size_available":
                size_available,

            "available_sizes":
                available_sizes,

            "matching_variants":
                matching_variants
        }


    # -------------------------------------------------
    # Check multiple products
    # -------------------------------------------------

    def check_products(
        self,
        products_input,
        requested_size=None
    ):

        results = []


        for item in products_input:

            if isinstance(
                item,
                dict
            ):

                product_id = (
                    item.get(
                        "product_id"
                    )
                )

            else:

                product_id = str(
                    item
                )


            if not product_id:
                continue


            result = (
                self.check_product(
                    product_id,
                    requested_size
                )
            )

            results.append(
                result
            )


        return results


    # -------------------------------------------------
    # Standard Agent Interface
    # -------------------------------------------------

    def run(
        self,
        input_data
    ):

        if not isinstance(
            input_data,
            dict
        ):

            raise TypeError(
                "Agent input must be "
                "a dictionary."
            )


        products_input = (
            input_data.get(
                "products",
                []
            )
        )

        requested_size = (
            input_data.get(
                "requested_size"
            )
        )


        results = (
            self.check_products(
                products_input,
                requested_size
            )
        )


        matched_products = [

            result

            for result
            in results

            if result.get(
                "size_available"
            ) is True
        ]


        return {

            "agent":
                self.name,

            "status":
                "success",

            "data_source":
                "SQL Server",

            "requested_size":
                requested_size,

            "checked_count":
                len(results),

            "matched_count":
                len(
                    matched_products
                ),

            "products":
                results,

            "matched_products":
                matched_products,

            "fit_note":
                (
                    "Size availability is "
                    "verified using actual "
                    "product variants stored "
                    "in SQL Server. "
                    "This does not guarantee "
                    "physical fit."
                )
        }


# -------------------------------------------------
# Test
# -------------------------------------------------

if __name__ == "__main__":

    agent = SizeFitAgent()


    test_product_ids = [
        "TH_10104961728824"
    ]


    available_sizes = (
        agent.get_available_sizes(
            test_product_ids[0]
        )
    )


    if available_sizes:

        test_size = (
            available_sizes[0]
        )

    else:

        test_size = "M"


    test_input = {

        "products":
            test_product_ids,

        "requested_size":
            test_size
    }


    response = (
        agent.run(
            test_input
        )
    )


    print(
        "\n--- SIZE / FIT AGENT ---"
    )

    print(
        "Data Source:",
        response[
            "data_source"
        ]
    )

    print(
        "Requested Size:",
        response[
            "requested_size"
        ]
    )

    print(
        "Products Checked:",
        response[
            "checked_count"
        ]
    )

    print(
        "Products Matching Size:",
        response[
            "matched_count"
        ]
    )


    for result in response[
        "products"
    ]:

        print(
            "\nProduct:",
            result.get(
                "product_name",
                ""
            )
        )

        print(
            "Product ID:",
            result[
                "product_id"
            ]
        )

        print(
            "Available Sizes:",
            result[
                "available_sizes"
            ]
        )

        print(
            "Requested Size Available:",
            result[
                "size_available"
            ]
        )

        print(
            "Status:",
            result[
                "status"
            ]
        )


    print(
        "\nNote:",
        response[
            "fit_note"
        ]
    )