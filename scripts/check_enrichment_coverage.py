import csv

FILE = "data/processed/products_enriched.csv"

FIELDS = [
    "category",
    "sub_category",
    "target_group",
    "material",
    "fit_type",
    "pattern",
    "style",
    "occasion"
]

with open(FILE, "r", encoding="utf-8-sig") as f:
    products = list(csv.DictReader(f))

total = len(products)

print("\n--- ENRICHMENT COVERAGE ---")
print(f"Total products: {total}\n")

for field in FIELDS:
    filled = sum(
        1 for p in products
        if p[field].strip()
    )

    missing = total - filled
    percentage = (filled / total) * 100

    print(
        f"{field}: "
        f"filled={filled}, "
        f"missing={missing}, "
        f"coverage={percentage:.1f}%"
    )