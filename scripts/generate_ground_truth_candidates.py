
import json
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

PRODUCTS_FILE = BASE_DIR / "data" / "processed" / "products_final.csv"
VARIANTS_FILE = BASE_DIR / "data" / "processed" / "product_variants_final.csv"

QUERIES_FILE = BASE_DIR / "evaluation" / "ground_truth_queries.json"
OUTPUT_FILE = BASE_DIR / "evaluation" / "ground_truth_candidates.csv"


def normalize(value):
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def to_bool(value):
    return normalize(value) in {"true", "1", "yes", "y"}


def has_available_size(product_id, requested_size, variants):
    rows = variants[
        variants["product_id"].astype(str) == str(product_id)
    ].copy()

    if rows.empty:
        return False

    requested_size = normalize(requested_size)

    size_match = rows["size"].apply(normalize) == requested_size
    available_match = rows["available"].apply(to_bool)

    return bool((size_match & available_match).any())


def get_available_sizes(product_id, variants):
    rows = variants[
        variants["product_id"].astype(str) == str(product_id)
    ].copy()

    if rows.empty:
        return ""

    rows = rows[rows["available"].apply(to_bool)]

    sizes = sorted({
        str(size).strip()
        for size in rows["size"]
        if not pd.isna(size) and str(size).strip()
    })

    return ", ".join(sizes)


def text_matches(value, expected):
    value = normalize(value)
    expected = normalize(expected)

    if not value or not expected:
        return False

    return expected in value


def product_matches(product, filters, variants):
    # Category
    if "category" in filters:
        if normalize(product.get("category")) != normalize(filters["category"]):
            return False

    # Target group
    if "target_group" in filters:
        if normalize(product.get("target_group")) != normalize(filters["target_group"]):
            return False

    # Material
    if "material" in filters:
        if not text_matches(product.get("material"), filters["material"]):
            return False

    # Style
    if "style" in filters:
        if not text_matches(product.get("style"), filters["style"]):
            return False

    # Occasion
    if "occasion" in filters:
        if not text_matches(product.get("occasion"), filters["occasion"]):
            return False

    # Color
    if "color" in filters:
        if not text_matches(product.get("color"), filters["color"]):
            return False

    # Maximum price
    if "max_price" in filters:
        try:
            price = float(product.get("base_price"))
            if price > float(filters["max_price"]):
                return False
        except (TypeError, ValueError):
            return False

    # Exact available size
    if "size" in filters:
        if not has_available_size(
            product["product_id"],
            filters["size"],
            variants
        ):
            return False

    return True


def main():
    products = pd.read_csv(PRODUCTS_FILE, dtype={"product_id": str})
    variants = pd.read_csv(
        VARIANTS_FILE,
        dtype={
            "product_id": str,
            "variant_id": str,
            "size": str
        }
    )

    with open(QUERIES_FILE, "r", encoding="utf-8") as f:
        queries = json.load(f)

    candidate_rows = []

    print("\nGround Truth Candidate Counts")
    print("-" * 55)

    for query in queries:
        query_id = query["query_id"]
        query_text = query["query"]
        filters = query.get("filters", {})
        known_relevant = set(query.get("relevant_product_ids", []))

        query_candidates = []

        for _, product in products.iterrows():
            if product_matches(product, filters, variants):

                row = {
                    "query_id": query_id,
                    "query": query_text,
                    "product_id": product["product_id"],
                    "product_name": product.get("product_name", ""),
                    "category": product.get("category", ""),
                    "sub_category": product.get("sub_category", ""),
                    "target_group": product.get("target_group", ""),
                    "material": product.get("material", ""),
                    "style": product.get("style", ""),
                    "occasion": product.get("occasion", ""),
                    "color": product.get("color", ""),
                    "base_price": product.get("base_price", ""),
                    "available_sizes": get_available_sizes(
                        product["product_id"],
                        variants
                    ),
                    "product_url": product.get("product_url", ""),
                    "relevant": (
                        1 if product["product_id"] in known_relevant
                        else 0 if known_relevant
                        else ""
                    )
                }

                query_candidates.append(row)

        candidate_rows.extend(query_candidates)

        print(
            f"{query_id}: {len(query_candidates):>3} candidates "
            f"| {query_text}"
        )

    candidates_df = pd.DataFrame(candidate_rows)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    candidates_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("-" * 55)
    print(f"Queries: {len(queries)}")
    print(f"Candidate rows: {len(candidates_df)}")
    print(f"Created: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
