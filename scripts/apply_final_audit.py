import json
import csv

INPUT_JSON = "data/processed/fashion_products_merged.json"
AUDIT_CSV = "data/processed/suspicious_fashion_products.csv"

OUTPUT_JSON = "data/processed/fashion_products_clean.json"
REMOVED_JSON = "data/processed/removed_from_fashion.json"

# Load current fashion products
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    products = json.load(f)["products"]

# Read KEEP / REMOVE decisions
decisions = {}

with open(AUDIT_CSV, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        product_id = str(row["id"]).strip()
        decision = row["decision"].strip().upper()

        if decision in {"KEEP", "REMOVE"}:
            decisions[product_id] = decision

clean_products = []
removed_products = []

for product in products:
    product_id = str(product["id"])

    if decisions.get(product_id) == "REMOVE":
        removed_products.append(product)
    else:
        clean_products.append(product)

# Save final clean dataset
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(
        {"products": clean_products},
        f,
        ensure_ascii=False,
        indent=2
    )

# Save removed products separately
with open(REMOVED_JSON, "w", encoding="utf-8") as f:
    json.dump(
        {"products": removed_products},
        f,
        ensure_ascii=False,
        indent=2
    )

print("\n--- FINAL CLEANING RESULTS ---")
print(f"Before cleaning: {len(products)}")
print(f"Removed:         {len(removed_products)}")
print(f"Final products:  {len(clean_products)}")
print(f"Saved to: {OUTPUT_JSON}")