import json
import os
import re

INPUT_FILE = "data/raw/thilakawardhana/all_products_raw.json"
OUTPUT_DIR = "data/processed"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Strong fashion product types
FASHION_PRODUCT_TYPES = {
    "dresses",
    "women tops",
    "t-tots",
    "shoes",
    "men t shirt",
    "women jeans",
    "women pants",
    "women t shirts",
    "women skirts",
    "men formal ss shirts",
    "teen",
    "men formal ls shirts",
    "mens trousers",
    "mens shorts",
    "mens jeans",
    "women nightwears",
    "saree",
    "jumpsuits",
    "women shorts",
}

# Fashion indicators from title/tags/description
FASHION_TERMS = {
    "dress", "frock", "top", "blouse",
    "t shirt", "tee", "shirt", "polo",
    "hoodie", "jersey",
    "jeans", "denim", "trouser", "trousers",
    "pants", "chino", "shorts", "skirt",
    "jumpsuit", "saree", "sarong",
    "shoe", "shoes", "sneaker", "sneakers",
    "heel", "heels", "sandals", "slippers",
    "bag", "handbag", "backpack",
    "belt", "tie", "wallet",
    "watch", "watches",
    "innerwear", "bra",
    "activewear", "nightwear",
    "mens", "womens", "boys", "girls","short", "uniform", "brief", "bangle",
"bracelet", "necklace", "earring",
"jewellery", "jewelry","sunglass", "sunglasses",
"cufflink", "cufflinks",
"backpack"
}

# Strong non-fashion indicators
NON_FASHION_TERMS = {
    "perfume", "facewash", "face wash",
    "shampoo", "lip balm", "cream",
    "cosmetic", "skincare",
    "samsung", "apple", "huawei", "zte",
    "phone", "smartphone",
    "shaver",
    "toy", "toys", "teddy",
    "flask", "spoon", "cutting board",
    "bedsheet", "towel",
    "photo frame", "pen holder",
    "pacifier", "nail clipper",
    "brush and comb","perfumes", "earbud", "earbuds",
"earphone", "earphones",
"nail polish", "nail enamel",
"eye liner", "eyeliner",
"facial mask", "face scrub",
"sunscreen", "lotion",
"deodorant", "roll on",
"kettle", "bottle", "lunch box",
"pressure cooker", "blender",
"steam iron", "game","soft toys", "animal toys",
"religious", "pirikara",
"hair gel",
"fork", "umbrella",
"rice cooker",
"television", "tv",
"carpet", "carpets",
"floor mat", "floor mats",
"floor rug", "floor rugs",
"coconut scraper",
"heater"
}


def normalize(text):
    text = str(text).lower()
    text = text.replace("_", " ")
    text = text.replace("-", " ")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def contains_term(text, terms):
    padded = f" {text} "

    for term in terms:
        term = normalize(term)

        if f" {term} " in padded:
            return True

    return False


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    products = json.load(f)["products"]


fashion_products = []
non_fashion_products = []
needs_review = []

for product in products:

    product_type = normalize(product.get("product_type", ""))

    title = normalize(product.get("title", ""))

    tags = normalize(
        " ".join(product.get("tags", []))
    )

    description = normalize(
        product.get("body_html", "")
    )

    combined_text = " ".join([
        title,
        tags,
        description
    ])

    # 1. Strong product_type match
    if product_type in FASHION_PRODUCT_TYPES:
        fashion_products.append(product)
        continue

    has_fashion = contains_term(
        combined_text,
        FASHION_TERMS
    )

    has_non_fashion = contains_term(
        combined_text,
        NON_FASHION_TERMS
    )

    # 2. Clearly fashion
    if has_fashion and not has_non_fashion:
        fashion_products.append(product)

    # 3. Clearly non-fashion
    elif has_non_fashion and not has_fashion:
        non_fashion_products.append(product)

    # 4. Ambiguous
    else:
        needs_review.append(product)


def save_json(filename, products):
    path = os.path.join(OUTPUT_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {"products": products},
            f,
            ensure_ascii=False,
            indent=2
        )


save_json(
    "fashion_products_raw.json",
    fashion_products
)

save_json(
    "non_fashion_products.json",
    non_fashion_products
)

save_json(
    "needs_review.json",
    needs_review
)


print("\n--- FILTER RESULTS ---")
print(f"Total products:      {len(products)}")
print(f"Fashion products:    {len(fashion_products)}")
print(f"Non-fashion:         {len(non_fashion_products)}")
print(f"Needs manual review: {len(needs_review)}")