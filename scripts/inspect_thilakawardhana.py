import json
from collections import Counter

FILE = "data/raw/thilakawardhana/all_products_raw.json"

with open(FILE, "r", encoding="utf-8") as f:
    products = json.load(f)["products"]

product_types = Counter()
tags = Counter()

for product in products:
    product_type = product.get("product_type", "").strip()

    if product_type:
        product_types[product_type] += 1
    else:
        product_types["[EMPTY]"] += 1

    for tag in product.get("tags", []):
        tags[tag.strip()] += 1

print("\n--- PRODUCT TYPES ---")
for name, count in product_types.most_common():
    print(f"{name}: {count}")

print("\n--- TOP TAGS ---")
for name, count in tags.most_common(100):
    print(f"{name}: {count}")