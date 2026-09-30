import csv
import re

INPUT_FILE = "data/processed/products_enriched.csv"
OUTPUT_FILE = "data/processed/products_with_colors.csv"

COLORS = [
    "black", "white", "red", "blue", "navy",
    "green", "yellow", "pink", "purple",
    "brown", "beige", "grey", "gray",
    "orange", "maroon", "wine", "cream",
    "khaki", "olive", "gold", "silver",
    "nude", "peach", "coral"
]


def normalize(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
    products = list(csv.DictReader(f))


for product in products:

    # Give title more importance
    title = normalize(product["product_name"])

    description = normalize(
        " ".join([
            product["tags"],
            product["description"]
        ])
    )

    found_colors = []

    # First check title
    for color in COLORS:
        if re.search(rf"\b{re.escape(color)}\b", title):
            found_colors.append(color)

    # If title has no color, check description
    if not found_colors:
        for color in COLORS:
            if re.search(
                rf"\b{re.escape(color)}\b",
                description
            ):
                found_colors.append(color)

    product["color"] = "|".join(
        dict.fromkeys(found_colors)
    )


fieldnames = list(products[0].keys())

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(products)


filled = sum(
    1 for p in products
    if p["color"].strip()
)

print("\n--- COLOR EXTRACTION ---")
print("Total products:", len(products))
print("Products with color:", filled)
print("Missing color:", len(products) - filled)
print("Created:", OUTPUT_FILE)