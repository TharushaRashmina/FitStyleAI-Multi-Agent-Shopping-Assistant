from pathlib import Path
import json
import re

import joblib
import pandas as pd
from rank_bm25 import BM25Okapi


# -------------------------------------------------
# Paths
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

PRODUCTS_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "products_final.csv"
)

MODEL_DIR = BASE_DIR / "models" / "bm25"

BM25_MODEL_FILE = MODEL_DIR / "bm25_model.joblib"
PRODUCT_IDS_FILE = MODEL_DIR / "product_ids.json"
TOKENIZED_CORPUS_FILE = MODEL_DIR / "tokenized_corpus.joblib"


# -------------------------------------------------
# Tokenizer
# -------------------------------------------------

def tokenize(text):
    text = str(text).lower()

    # keep only words and numbers
    tokens = re.findall(
        r"\b[a-z0-9]+\b",
        text
    )

    return tokens


# -------------------------------------------------
# Load products
# -------------------------------------------------

products = pd.read_csv(
    PRODUCTS_FILE,
    dtype={"product_id": str}
)


# -------------------------------------------------
# Validate columns
# -------------------------------------------------

required_columns = [
    "product_id",
    "search_text"
]

missing_columns = [
    column
    for column in required_columns
    if column not in products.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


# -------------------------------------------------
# Prepare corpus
# -------------------------------------------------

documents = (
    products["search_text"]
    .fillna("")
    .astype(str)
    .tolist()
)

tokenized_corpus = [
    tokenize(document)
    for document in documents
]


# -------------------------------------------------
# Build BM25 model
# -------------------------------------------------

bm25 = BM25Okapi(
    tokenized_corpus
)


# -------------------------------------------------
# Product ID mapping
# -------------------------------------------------

product_ids = (
    products["product_id"]
    .astype(str)
    .tolist()
)


# -------------------------------------------------
# Save files
# -------------------------------------------------

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

joblib.dump(
    bm25,
    BM25_MODEL_FILE
)

joblib.dump(
    tokenized_corpus,
    TOKENIZED_CORPUS_FILE
)

with open(
    PRODUCT_IDS_FILE,
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        product_ids,
        f,
        indent=2
    )


# -------------------------------------------------
# Output
# -------------------------------------------------

total_tokens = sum(
    len(tokens)
    for tokens in tokenized_corpus
)

print("\n--- BM25 INDEX CREATED ---")

print(
    "Products:",
    len(products)
)

print(
    "Documents:",
    len(tokenized_corpus)
)

print(
    "Total tokens:",
    total_tokens
)

print("\nCreated:")
print(BM25_MODEL_FILE)
print(TOKENIZED_CORPUS_FILE)
print(PRODUCT_IDS_FILE)