import json
import csv
import os
from urllib.parse import urlparse

SOURCE_JSON = "data/processed/fashion_products_clean.json"

PRODUCTS_FILE = "data/processed/products_final.csv"
VARIANTS_FILE = "data/processed/product_variants_final.csv"

# ඔයා mark කරපු file name
GROUND_TRUTH_FILE = "evaluation/ground_truth_candidates.csv"


# -------------------------------------------------
# Load original JSON - this contains exact Shopify IDs
# -------------------------------------------------
with open(SOURCE_JSON, "r", encoding="utf-8") as f:
    original_products = json.load(f)["products"]


# handle -> exact prefixed product ID
handle_to_product_id = {}

# original product ID -> prefixed product ID
old_product_to_new = {}

# original variant ID -> prefixed variant ID
old_variant_to_new = {}

for product in original_products:
    original_product_id = str(product["id"])
    handle = product.get("handle", "").strip()

    new_product_id = f"TH_{original_product_id}"

    handle_to_product_id[handle] = new_product_id
    old_product_to_new[original_product_id] = new_product_id

    for variant in product.get("variants", []):
        original_variant_id = str(variant["id"])
        old_variant_to_new[original_variant_id] = (
            f"THV_{original_variant_id}"
        )


def get_handle_from_url(url):
    if not url:
        return ""

    path = urlparse(url).path
    parts = path.strip("/").split("/")

    if "products" in parts:
        index = parts.index("products")

        if index + 1 < len(parts):
            return parts[index + 1]

    return ""


# -------------------------------------------------
# 1. FIX products_final.csv
# -------------------------------------------------
with open(PRODUCTS_FILE, "r", encoding="utf-8-sig") as f:
    products = list(csv.DictReader(f))

for product in products:
    handle = get_handle_from_url(
        product.get("product_url", "")
    )

    exact_id = handle_to_product_id.get(handle)

    if exact_id:
        product["product_id"] = exact_id


with open(
    PRODUCTS_FILE,
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=products[0].keys()
    )

    writer.writeheader()
    writer.writerows(products)


# -------------------------------------------------
# 2. REBUILD product_variants_final.csv
#    directly from original JSON
# -------------------------------------------------
variant_rows = []

for product in original_products:

    product_id = f"TH_{product['id']}"

    # Shopify option position -> option name
    option_names = {}

    for option in product.get("options", []):
        option_names[option.get("position")] = (
            option.get("name", "")
        )

    for variant in product.get("variants", []):

        size = ""
        color = ""

        values = {
            1: variant.get("option1"),
            2: variant.get("option2"),
            3: variant.get("option3")
        }

        for position, value in values.items():

            if value is None:
                continue

            option_name = option_names.get(
                position, ""
            ).lower()

            if "size" in option_name:
                size = str(value)

            elif (
                "color" in option_name
                or "colour" in option_name
            ):
                color = str(value)

        variant_rows.append({
            "variant_id": f"THV_{variant['id']}",
            "product_id": product_id,
            "size": size,
            "color": color,
            "available": variant.get(
                "available", False
            ),
            "price": variant.get("price", ""),
            "sku": variant.get("sku", "")
        })


with open(
    VARIANTS_FILE,
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:

    fieldnames = [
        "variant_id",
        "product_id",
        "size",
        "color",
        "available",
        "price",
        "sku"
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(variant_rows)


# -------------------------------------------------
# 3. FIX ground_truth_candidates.csv
#    Relevant 1/0 decisions remain unchanged
# -------------------------------------------------
if os.path.exists(GROUND_TRUTH_FILE):

    with open(
        GROUND_TRUTH_FILE,
        "r",
        encoding="utf-8-sig"
    ) as f:
        ground_truth = list(csv.DictReader(f))

    fixed = 0

    for row in ground_truth:

        handle = get_handle_from_url(
            row.get("product_url", "")
        )

        exact_id = handle_to_product_id.get(handle)

        if exact_id:
            row["product_id"] = exact_id
            fixed += 1

    with open(
        GROUND_TRUTH_FILE,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=ground_truth[0].keys()
        )

        writer.writeheader()
        writer.writerows(ground_truth)

else:
    fixed = 0


print("\n--- ID FIX COMPLETE ---")
print(f"Products fixed: {len(products)}")
print(f"Variants rebuilt: {len(variant_rows)}")
print(f"Ground truth rows fixed: {fixed}")
print()
print("Example product ID format: TH_10825362047288")
print("Example variant ID format: THV_52803742007608")