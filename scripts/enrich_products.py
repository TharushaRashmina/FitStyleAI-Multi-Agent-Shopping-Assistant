import csv
import re

INPUT_FILE = "data/processed/products.csv"
OUTPUT_FILE = "data/processed/products_enriched.csv"


CATEGORY_RULES = {
    "tops": [
        "t shirt", "t-shirt", "shirt", "top",
        "blouse", "polo", "tee"
    ],

    "bottoms": [
        "jeans", "denim", "trouser", "trousers",
        "pants", "chino", "shorts",
        "skirt", "skort"
    ],

    "dresses": [
        "dress", "frock", "jumpsuit"
    ],

    "footwear": [
        "shoe", "shoes", "heel", "heels",
        "sandal", "sandals", "sneaker",
        "sneakers", "slipper"
    ],

    "ethnic_wear": [
        "saree", "sarong", "batik"
    ],

    "innerwear": [
        "innerwear", "bra", "brief",
        "panty", "lingerie"
    ],

    "nightwear": [
        "nightwear", "night dress",
        "sleepwear", "pyjama", "pajama"
    ],

    "activewear": [
        "activewear", "sportswear",
        "gym wear", "legging"
    ],

    "bags": [
        "bag", "handbag", "backpack",
        "clutch"
    ],

    "accessories": [
        "belt", "wallet", "tie",
        "watch", "watches",
        "sunglass", "sunglasses",
        "cufflink", "bangle",
        "bracelet", "necklace",
        "earring", "jewellery", "jewelry"
    ]
}

SUBCATEGORY_RULES = [
    "t-shirt", "polo", "shirt", "blouse", "top",

    "jeans", "trousers", "pants",
    "chino", "shorts", "skirt", "skort",

    "dress", "frock", "jumpsuit",

    "heels", "sandals", "sneakers",
    "shoes", "slippers",

    "saree", "sarong",

    "bra", "brief", "innerwear",
    "nightwear",

    "activewear", "leggings",

    "handbag", "backpack", "clutch", "bag",

    "belt", "wallet", "tie", "watch",
    "sunglasses", "cufflinks",
    "bangle", "bracelet",
    "necklace", "earrings"
]

TARGET_RULES = {
    "women": [
        "women", "womens", "woman", "ladies"
    ],

    "men": [
        "men", "mens", "man"
    ],

    "boys": [
        "boys", "boy"
    ],

    "girls": [
        "girls", "girl"
    ],

    "teen": [
        "teen"
    ],

    "kids": [
        "kids", "children"
    ]
}

MATERIALS = [
    "cotton", "linen", "polyester", "denim",
    "viscose", "rayon", "silk", "elastane",
    "spandex", "woven"
]

FITS = [
    "slim fit",
    "regular fit",
    "relaxed fit",
    "oversized",
    "bodycon"
]

PATTERNS = [
    "printed",
    "floral",
    "striped",
    "check",
    "checked",
    "plain",
    "solid",
    "embroidered"
]

STYLES = [
    "casual",
    "formal",
    "smart casual",
    "smart-casual",
    "business casual",
    "workwear",
    "activewear"
]

OCCASIONS = [
    "office",
    "party",
    "wedding",
    "casual wear",
    "brunch",
    "date",
    "special occasion"
]


def normalize(text):
    text = str(text).lower()
    text = text.replace("_", " ")
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_first(text, values):
    for value in values:
        if value in text:
            return value
    return ""


def detect_category(text):
    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in text for keyword in keywords):
            return category
    return ""


def detect_target(text):
    for target, keywords in TARGET_RULES.items():
        if any(keyword in text for keyword in keywords):
            return target
    return ""


with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
    products = list(csv.DictReader(f))


output_rows = []

for product in products:

    text = normalize(" ".join([
        product["product_name"],
        product["product_type_raw"],
        product["tags"],
        product["description"]
    ]))

    product["category"] = detect_category(text)

    product["sub_category"] = find_first(
        text,
        SUBCATEGORY_RULES
    )

    product["target_group"] = detect_target(text)

    product["material"] = find_first(
        text,
        MATERIALS
    )

    product["fit_type"] = find_first(
        text,
        FITS
    )

    product["pattern"] = find_first(
        text,
        PATTERNS
    )

    product["style"] = find_first(
        text,
        STYLES
    )

    product["occasion"] = find_first(
        text,
        OCCASIONS
    )

    output_rows.append(product)


fieldnames = list(output_rows[0].keys())


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
    writer.writerows(output_rows)


print("\n--- ENRICHMENT COMPLETE ---")
print("Products:", len(output_rows))
print("Created:", OUTPUT_FILE)