from pathlib import Path
import json

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


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

MODEL_DIR = BASE_DIR / "models" / "semantic"

EMBEDDINGS_FILE = MODEL_DIR / "product_embeddings.npy"
PRODUCT_IDS_FILE = MODEL_DIR / "product_ids.json"
MODEL_INFO_FILE = MODEL_DIR / "model_info.json"


# -------------------------------------------------
# Model
# -------------------------------------------------

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

model = SentenceTransformer(
    MODEL_NAME
)


# -------------------------------------------------
# Load products
# -------------------------------------------------

products = pd.read_csv(
    PRODUCTS_FILE,
    dtype={"product_id": str}
)


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
# Prepare documents
# -------------------------------------------------

documents = (
    products["search_text"]
    .fillna("")
    .astype(str)
    .tolist()
)

product_ids = (
    products["product_id"]
    .astype(str)
    .tolist()
)


# -------------------------------------------------
# Generate embeddings
# -------------------------------------------------

print("\nGenerating semantic embeddings...")

embeddings = model.encode(
    documents,
    batch_size=32,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True
)


# -------------------------------------------------
# Save files
# -------------------------------------------------

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

np.save(
    EMBEDDINGS_FILE,
    embeddings
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

with open(
    MODEL_INFO_FILE,
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        {
            "model_name": MODEL_NAME,
            "products": len(product_ids),
            "embedding_dimension": int(
                embeddings.shape[1]
            )
        },
        f,
        indent=2
    )


# -------------------------------------------------
# Output
# -------------------------------------------------

print("\n--- SEMANTIC INDEX CREATED ---")

print(
    "Products:",
    len(product_ids)
)

print(
    "Embedding shape:",
    embeddings.shape
)

print(
    "Embedding dimension:",
    embeddings.shape[1]
)

print("\nCreated:")
print(EMBEDDINGS_FILE)
print(PRODUCT_IDS_FILE)
print(MODEL_INFO_FILE)