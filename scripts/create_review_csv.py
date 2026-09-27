import json
import csv

INPUT_FILE = "data/processed/needs_review.json"
OUTPUT_FILE = "data/processed/needs_review.csv"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    products = json.load(f)["products"]

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)

    # Header
    writer.writerow([
        "id",
        "title",
        "product_type",
        "tags",
        "decision"
    ])

    # Product rows
    for product in products:
        writer.writerow([
            str(product.get("id", "")),
            product.get("title", ""),
            product.get("product_type", ""),
            ", ".join(product.get("tags", [])),
            ""
        ])

print(f"Created: {OUTPUT_FILE}")
print(f"Products to review: {len(products)}")