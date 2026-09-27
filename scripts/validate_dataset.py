import csv
from collections import Counter

PRODUCTS_FILE = "data/processed/products_with_colors.csv"
VARIANTS_FILE = "data/processed/product_variants.csv"

with open(PRODUCTS_FILE, "r", encoding="utf-8-sig") as f:
    products = list(csv.DictReader(f))

with open(VARIANTS_FILE, "r", encoding="utf-8-sig") as f:
    variants = list(csv.DictReader(f))

product_ids = [p["product_id"].strip() for p in products]
variant_ids = [v["variant_id"].strip() for v in variants]

duplicate_products = [
    pid for pid, count in Counter(product_ids).items()
    if count > 1
]

duplicate_variants = [
    vid for vid, count in Counter(variant_ids).items()
    if count > 1
]

valid_product_ids = set(product_ids)

orphan_variants = [
    v for v in variants
    if v["product_id"].strip() not in valid_product_ids
]

missing_price = sum(
    1 for v in variants
    if not v["price"].strip()
)

invalid_availability = sum(
    1 for v in variants
    if v["available"].strip().lower()
    not in {"true", "false"}
)

print("\n--- DATASET VALIDATION ---")
print("Products:", len(products))
print("Variants:", len(variants))
print("Duplicate product IDs:", len(duplicate_products))
print("Duplicate variant IDs:", len(duplicate_variants))
print("Orphan variants:", len(orphan_variants))
print("Variants missing price:", missing_price)
print("Invalid availability values:", invalid_availability)