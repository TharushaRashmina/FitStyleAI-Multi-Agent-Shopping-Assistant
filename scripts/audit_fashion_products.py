import json
import csv
import re

INPUT_FILE = "data/processed/fashion_products_merged.json"
OUTPUT_FILE = "data/processed/suspicious_fashion_products.csv"

NON_FASHION_TERMS = {
    "perfume", "parfum", "eau de toilette", "eau de parfum",
    "body spray", "deodorant",
    "facewash", "face wash", "shampoo", "conditioner",
    "cream", "lotion", "skincare", "cosmetic",
    "nail polish", "nail enamel", "eyeliner",
    "shaver", "trimmer",
    "phone", "smartphone", "samsung", "iphone", "huawei",
    "earbud", "earbuds", "earphone", "headphone",
    "toy", "toys", "teddy",
    "flask", "kettle", "rice cooker",
    "bottle", "lunch box", "cutting board",
    "bedsheet", "towel", "carpet",
    "photo frame", "pen holder"
}

def clean_text(text):
    text = str(text).lower()
    text = text.replace("_", " ")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    products = json.load(f)["products"]

suspicious = []

for product in products:

    text = " ".join([
        product.get("title", ""),
        product.get("product_type", ""),
        " ".join(product.get("tags", [])),
        product.get("body_html", "")
    ])

    text = clean_text(text)

    matched_terms = [
        term for term in NON_FASHION_TERMS
        if term in text
    ]

    if matched_terms:
        suspicious.append({
            "id": str(product.get("id", "")),
            "title": product.get("title", ""),
            "product_type": product.get("product_type", ""),
            "tags": ", ".join(product.get("tags", [])),
            "matched_terms": ", ".join(matched_terms),
            "decision": ""
        })

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "id",
            "title",
            "product_type",
            "tags",
            "matched_terms",
            "decision"
        ]
    )

    writer.writeheader()
    writer.writerows(suspicious)

print("\n--- AUDIT RESULTS ---")
print(f"Fashion products checked: {len(products)}")
print(f"Suspicious products:       {len(suspicious)}")
print(f"Saved to: {OUTPUT_FILE}")