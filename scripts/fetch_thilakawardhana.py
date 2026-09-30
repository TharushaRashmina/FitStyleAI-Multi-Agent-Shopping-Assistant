import requests
import json
import os
import time

BASE_URL = "https://thilakawardhana.com/products.json"

OUTPUT_DIR = "data/raw/thilakawardhana"
os.makedirs(OUTPUT_DIR, exist_ok=True)

all_products = []
page = 1

while True:
    print(f"Fetching page {page}...")

    params = {
        "limit": 250,
        "page": page
    }

    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    products = data.get("products", [])

    if not products:
        print("No more products.")
        break

    # Save each raw page
    page_file = os.path.join(
        OUTPUT_DIR,
        f"page_{page}.json"
    )

    with open(page_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    all_products.extend(products)

    print(f"Found {len(products)} products")

    page += 1
    time.sleep(1)

# Save all products together
combined_file = os.path.join(
    OUTPUT_DIR,
    "all_products_raw.json"
)

with open(combined_file, "w", encoding="utf-8") as f:
    json.dump(
        {"products": all_products},
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"\nTotal products collected: {len(all_products)}")
print("Saved to:", combined_file)