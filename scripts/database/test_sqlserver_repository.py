from pathlib import Path
import sys


# -------------------------------------------------
# Project root
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


# -------------------------------------------------
# Import repository
# -------------------------------------------------

from database.sqlserver_repository import (
    SQLServerRepository
)


# -------------------------------------------------
# Test
# -------------------------------------------------

if __name__ == "__main__":

    repository = SQLServerRepository()

    test_product_id = (
        "TH_10104961728824"
    )


    print(
        "\n--- SQL SERVER REPOSITORY TEST ---"
    )


    # ---------------------------------------------
    # Product
    # ---------------------------------------------

    product = (
        repository.get_product_by_id(
            test_product_id
        )
    )


    if product:

        print(
            "\nProduct Found:"
        )

        print(
            "Product ID:",
            product["product_id"]
        )

        print(
            "Name:",
            product["product_name"]
        )

        print(
            "Category:",
            product["category"]
        )

        print(
            "Price:",
            product["base_price"]
        )

    else:

        print(
            "\nProduct not found."
        )


    # ---------------------------------------------
    # All variants
    # ---------------------------------------------

    variants = (
        repository.get_variants_by_product(
            test_product_id
        )
    )

    print(
        "\nTotal Variants:",
        len(variants)
    )


    for variant in variants[:10]:

        print(
            "-",
            variant["variant_id"],
            "| Size:",
            variant["size"],
            "| Available:",
            variant["available"],
            "| Price:",
            variant["price"]
        )


    # ---------------------------------------------
    # Available variants
    # ---------------------------------------------

    available_variants = (
        repository.get_available_variants(
            test_product_id
        )
    )

    print(
        "\nAvailable Variants:",
        len(available_variants)
    )


    for variant in available_variants[:10]:

        print(
            "- Size:",
            variant["size"],
            "| Available:",
            variant["available"]
        )


    # ---------------------------------------------
    # Test one real available size
    # ---------------------------------------------

    if available_variants:

        test_size = (
            available_variants[0]["size"]
        )

        result = (
            repository.has_available_size(
                test_product_id,
                test_size
            )
        )

        print(
            "\nSize Check:"
        )

        print(
            "Requested Size:",
            test_size
        )

        print(
            "Available:",
            result
        )

    else:

        print(
            "\nNo available variants found "
            "for size test."
        )


    # ---------------------------------------------
    # Multi Product Test
    # ---------------------------------------------

    print(
        "\n--- MULTI PRODUCT TEST ---"
    )

    test_ids = [
        "TH_10104961728824",
        "TH_10106909196600",
        "TH_10108268511544"
    ]

    products = (
        repository.get_products_by_ids(
            test_ids
        )
    )

    print(
        "Products returned:",
        len(products)
    )

    for product in products:

        print(
            "-",
            product["product_id"],
            "|",
            product["product_name"]
        )


    # ---------------------------------------------
    # Filter Test
    # ---------------------------------------------

    print(
        "\n--- FILTER TEST ---"
    )

    filtered_ids = (
        repository.filter_product_ids(

            test_ids,

            {
                "category": "tops",
                "target_group": "women",
                "max_price": 1500
            }
        )
    )

    print(
        "Filtered IDs:",
        filtered_ids
    )
    