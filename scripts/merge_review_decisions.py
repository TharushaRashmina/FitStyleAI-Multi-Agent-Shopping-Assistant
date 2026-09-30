import json
import csv
import os

FASHION_FILE = "data/processed/fashion_products_raw.json"
NON_FASHION_FILE = "data/processed/non_fashion_products.json"
REVIEW_JSON = "data/processed/needs_review.json"
REVIEW_CSV = "data/processed/needs_review.csv"

OUTPUT_DIR = "data/processed"

with open(FASHION_FILE, "r", encoding="utf-8") as f:
    fashion_products = json.load(f)["products"]

with open(NON_FASHION_FILE, "r", encoding="utf-8") as f:
    non_fashion_products = json.load(f)["products"]

with open(REVIEW_JSON, "r", encoding="utf-8") as f:
    review_products = json.load(f)["products"]

# Read manual decisions
decisions = {}

with open(REVIEW_CSV, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        product_id = str(row["id"]).strip()
        decision = row["decision"].strip().upper()

        decisions[product_id] = decision


review_fashion = []
review_non_fashion = []
unclassified = []

for product in review_products:

    product_id = str(product["id"])
    decision = decisions.get(product_id, "")

    if decision == "F":
        review_fashion.append(product)

    elif decision == "N":
        review_non_fashion.append(product)

    else:
        unclassified.append(product)


final_fashion = fashion_products + review_fashion
final_non_fashion = non_fashion_products + review_non_fashion


with open(
    os.path.join(OUTPUT_DIR, "fashion_products_merged.json"),
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        {"products": final_fashion},
        f,
        ensure_ascii=False,
        indent=2
    )


with open(
    os.path.join(OUTPUT_DIR, "non_fashion_products_final.json"),
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        {"products": final_non_fashion},
        f,
        ensure_ascii=False,
        indent=2
    )


print("\n--- MERGE RESULTS ---")
print(f"Original fashion:       {len(fashion_products)}")
print(f"Review marked F:        {len(review_fashion)}")
print(f"Review marked N:        {len(review_non_fashion)}")
print(f"Unclassified:           {len(unclassified)}")
print(f"Final fashion total:    {len(final_fashion)}")
print(f"Final non-fashion:      {len(final_non_fashion)}")