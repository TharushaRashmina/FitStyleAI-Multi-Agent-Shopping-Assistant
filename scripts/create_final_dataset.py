import csv
import re
import shutil

PRODUCTS_INPUT = "data/processed/products_with_colors.csv"
VARIANTS_INPUT = "data/processed/product_variants.csv"

PRODUCTS_OUTPUT = "data/processed/products_final.csv"
VARIANTS_OUTPUT = "data/processed/product_variants_final.csv"


SEARCH_FIELDS = [
    "product_name",
    "brand",
    "category",
    "sub_category",
    "target_group",
    "material",
    "fit_type",
    "pattern",
    "style",
    "occasion",
    "color",
    "product_type_raw",
    "tags",
    "description"
]


def clean_text(text):
    text = str(text).lower()
    text = text.replace("|", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# Load products
with open(PRODUCTS_INPUT, "r", encoding="utf-8-sig") as f:
    products = list(csv.DictReader(f))


# Add search_text
for product in products:

    combined = " ".join(
        product.get(field, "")
        for field in SEARCH_FIELDS
    )

    product["search_text"] = clean_text(combined)


# Save products_final.csv
fieldnames = list(products[0].keys())

with open(
    PRODUCTS_OUTPUT,
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


# Copy validated variants as final
shutil.copyfile(
    VARIANTS_INPUT,
    VARIANTS_OUTPUT
)


print("\n--- FINAL DATASET ---")
print(f"Products: {len(products)}")
print(f"Created: {PRODUCTS_OUTPUT}")
print(f"Created: {VARIANTS_OUTPUT}")