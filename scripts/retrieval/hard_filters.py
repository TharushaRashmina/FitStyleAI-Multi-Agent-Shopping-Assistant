from pathlib import Path

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

VARIANTS_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "product_variants_final.csv"
)


# -------------------------------------------------
# Load data
# -------------------------------------------------

products = pd.read_csv(
    PRODUCTS_FILE,
    dtype={"product_id": str}
)

variants = pd.read_csv(
    VARIANTS_FILE,
    dtype={
        "product_id": str,
        "variant_id": str,
        "size": str
    }
)

products["product_id"] = (
    products["product_id"].astype(str)
)

variants["product_id"] = (
    variants["product_id"].astype(str)
)

product_lookup = products.set_index(
    "product_id",
    drop=False
)


# -------------------------------------------------
# Helper functions
# -------------------------------------------------

def normalize(value):

    if pd.isna(value):
        return ""

    return str(value).strip().lower()


def text_matches(product_value, required_value):

    product_value = normalize(product_value)
    required_value = normalize(required_value)

    if not required_value:
        return True

    return required_value in product_value


def is_available(value):

    if isinstance(value, bool):
        return value

    return normalize(value) in {
        "true",
        "1",
        "yes"
    }


# -------------------------------------------------
# Size availability
# -------------------------------------------------

def has_available_size(product_id, required_size):

    required_size = normalize(
        required_size
    )

    product_variants = variants[
        variants["product_id"] == product_id
    ]

    for _, variant in product_variants.iterrows():

        variant_size = normalize(
            variant.get("size", "")
        )

        available = is_available(
            variant.get("available", False)
        )

        if (
            variant_size == required_size
            and available
        ):
            return True

    return False


# -------------------------------------------------
# Apply filters
# -------------------------------------------------

def apply_hard_filters(
    candidate_ids,
    filters
):

    filtered_ids = []

    for product_id in candidate_ids:

        product_id = str(product_id)

        if product_id not in product_lookup.index:
            continue

        product = product_lookup.loc[
            product_id
        ]

        # Category
        if filters.get("category"):

            if not text_matches(
                product.get("category", ""),
                filters["category"]
            ):
                continue

        # Target group
        if filters.get("target_group"):

            if not text_matches(
                product.get("target_group", ""),
                filters["target_group"]
            ):
                continue

        # Material
        if filters.get("material"):

            if not text_matches(
                product.get("material", ""),
                filters["material"]
            ):
                continue

        # Style
        if filters.get("style"):

            if not text_matches(
                product.get("style", ""),
                filters["style"]
            ):
                continue

        # Occasion
        if filters.get("occasion"):

            if not text_matches(
                product.get("occasion", ""),
                filters["occasion"]
            ):
                continue

        # Color
        if filters.get("color"):

            if not text_matches(
                product.get("color", ""),
                filters["color"]
            ):
                continue

        # Maximum price
        if filters.get("max_price") is not None:

            try:
                price = float(
                    product.get(
                        "base_price"
                    )
                )

                if price > float(
                    filters["max_price"]
                ):
                    continue

            except (TypeError, ValueError):
                continue

        # Exact available size
        if filters.get("size"):

            if not has_available_size(
                product_id,
                filters["size"]
            ):
                continue

        filtered_ids.append(
            product_id
        )

    return filtered_ids


# -------------------------------------------------
# Simple test
# -------------------------------------------------

if __name__ == "__main__":

    all_product_ids = (
        products["product_id"]
        .astype(str)
        .tolist()
    )

    test_filters = {
        "category": "tops",
        "target_group": "men",
        "style": "formal",
        "max_price": 5000
    }

    filtered = apply_hard_filters(
        all_product_ids,
        test_filters
    )

    print(
        "\n--- HARD FILTER TEST ---"
    )

    print(
        "Products before filtering:",
        len(all_product_ids)
    )

    print(
        "Products after filtering:",
        len(filtered)
    )

    print(
        "\nMatching product IDs:"
    )

    for product_id in filtered[:20]:
        print(product_id)