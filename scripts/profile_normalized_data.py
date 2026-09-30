import csv
from collections import Counter

PRODUCTS_FILE = "data/processed/products.csv"
VARIANTS_FILE = "data/processed/product_variants.csv"

# ---------- PRODUCTS ----------
with open(PRODUCTS_FILE, "r", encoding="utf-8-sig") as f:
    products = list(csv.DictReader(f))

print("\n--- PRODUCTS PROFILE ---")
print("Total products:", len(products))

for field in [
    "brand",
    "product_type_raw",
    "tags",
    "description",
    "image_url",
    "product_url"
]:
    missing = sum(
        1 for p in products
        if not p[field].strip()
    )

    print(f"{field} missing: {missing}")

# Product types
types = Counter(
    p["product_type_raw"].strip()
    for p in products
    if p["product_type_raw"].strip()
)

print("\n--- TOP PRODUCT TYPES ---")
for name, count in types.most_common(30):
    print(f"{name}: {count}")


# ---------- VARIANTS ----------
with open(VARIANTS_FILE, "r", encoding="utf-8-sig") as f:
    variants = list(csv.DictReader(f))

print("\n--- VARIANTS PROFILE ---")
print("Total variants:", len(variants))

size_missing = sum(
    1 for v in variants
    if not v["size"].strip()
)

color_missing = sum(
    1 for v in variants
    if not v["color"].strip()
)

available = sum(
    1 for v in variants
    if v["available"].lower() == "true"
)

print("Variants missing size:", size_missing)
print("Variants missing color:", color_missing)
print("Available variants:", available)

sizes = Counter(
    v["size"].strip()
    for v in variants
    if v["size"].strip()
)

print("\n--- TOP SIZES ---")
for size, count in sizes.most_common(30):
    print(f"{size}: {count}")