import json
from collections import Counter

FILE = "data/processed/needs_review.json"

with open(FILE, "r", encoding="utf-8") as f:
    products = json.load(f)["products"]

types = Counter()
tags = Counter()

for p in products:
    ptype = p.get("product_type", "").strip() or "[EMPTY]"
    types[ptype] += 1

    for tag in p.get("tags", []):
        tags[tag.strip()] += 1

print("\n--- REVIEW PRODUCT TYPES ---")
for name, count in types.most_common():
    print(f"{name}: {count}")

print("\n--- REVIEW TOP TAGS ---")
for name, count in tags.most_common(100):
    print(f"{name}: {count}")