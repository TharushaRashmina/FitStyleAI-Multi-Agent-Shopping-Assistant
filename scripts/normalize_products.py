import json
import csv
import re

INPUT_FILE = "data/processed/fashion_products_clean.json"

PRODUCTS_FILE = "data/processed/products.csv"
VARIANTS_FILE = "data/processed/product_variants.csv"

STORE_URL = "https://thilakawardhana.com"


def clean_html(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    products = json.load(f)["products"]


product_rows = []
variant_rows = []


for product in products:

    product_id = str(product.get("id", ""))

    variants = product.get("variants", [])

    # Base price
    prices = [
        float(v["price"])
        for v in variants
        if v.get("price")
    ]

    base_price = min(prices) if prices else ""

    # Main image
    images = product.get("images", [])

    image_url = images[0].get("src", "") if images else ""

    # Real product URL
    handle = product.get("handle", "")

    product_url = (
        f"{STORE_URL}/products/{handle}"
        if handle else ""
    )

    # Availability
    available_any = any(
        v.get("available", False)
        for v in variants
    )

    # Product row
    product_rows.append({
        "product_id": product_id,
        "source": "Thilakawardhana",
        "product_name": product.get("title", ""),
        "brand": product.get("vendor", ""),
        "product_type_raw": product.get("product_type", ""),
        "tags": "|".join(product.get("tags", [])),
        "description": clean_html(
            product.get("body_html", "")
        ),
        "base_price": base_price,
        "image_url": image_url,
        "product_url": product_url,
        "available_any": available_any
    })

    # Detect Shopify option names
    option_names = {}

    for option in product.get("options", []):
        position = option.get("position")
        option_names[position] = option.get("name", "")

    for variant in variants:

        size = ""
        color = ""

        option_values = {
            1: variant.get("option1"),
            2: variant.get("option2"),
            3: variant.get("option3")
        }

        for position, value in option_values.items():

            if value is None:
                continue

            option_name = option_names.get(
                position, ""
            ).lower()

            if "size" in option_name:
                size = value

            elif "color" in option_name or "colour" in option_name:
                color = value

        variant_rows.append({
            "variant_id": str(
                variant.get("id", "")
            ),
            "product_id": product_id,
            "size": size,
            "color": color,
            "available": variant.get(
                "available", False
            ),
            "price": variant.get("price", ""),
            "sku": variant.get("sku", "")
        })


# Save products.csv
with open(
    PRODUCTS_FILE,
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:

    fieldnames = [
        "product_id",
        "source",
        "product_name",
        "brand",
        "product_type_raw",
        "tags",
        "description",
        "base_price",
        "image_url",
        "product_url",
        "available_any"
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(product_rows)


# Save variants
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


print("\n--- NORMALIZATION RESULTS ---")
print(f"Products: {len(product_rows)}")
print(f"Variants: {len(variant_rows)}")
print(f"Created: {PRODUCTS_FILE}")
print(f"Created: {VARIANTS_FILE}")