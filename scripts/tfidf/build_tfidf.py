from pathlib import Path
import json

import joblib
import pandas as pd
from scipy.sparse import save_npz
from sklearn.feature_extraction.text import TfidfVectorizer


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

MODEL_DIR = BASE_DIR / "models" / "tfidf"

VECTORIZER_FILE = MODEL_DIR / "tfidf_vectorizer.joblib"
MATRIX_FILE = MODEL_DIR / "tfidf_matrix.npz"
PRODUCT_IDS_FILE = MODEL_DIR / "product_ids.json"


# -------------------------------------------------
# Load products
# -------------------------------------------------

products = pd.read_csv(
    PRODUCTS_FILE,
    dtype={"product_id": str}
)


# -------------------------------------------------
# Validate required columns
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
# Prepare documents
# -------------------------------------------------

documents = (
    products["search_text"]
    .fillna("")
    .astype(str)
)


# -------------------------------------------------
# Create TF-IDF vectorizer
# -------------------------------------------------

vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words="english",

    # Use single words + two-word phrases
    # Examples:
    # "formal"
    # "formal shirt"
    # "casual wear"
    ngram_range=(1, 2),

    min_df=1,

    # Reduce the effect of words repeated
    # many times in the same product
    sublinear_tf=True,

    # Normalization helps cosine similarity
    norm="l2"
)


# -------------------------------------------------
# Build TF-IDF matrix
# -------------------------------------------------

tfidf_matrix = vectorizer.fit_transform(
    documents
)


# -------------------------------------------------
# Save model files
# -------------------------------------------------

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

joblib.dump(
    vectorizer,
    VECTORIZER_FILE
)

save_npz(
    MATRIX_FILE,
    tfidf_matrix
)

product_ids = (
    products["product_id"]
    .astype(str)
    .tolist()
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

print("\n--- TF-IDF INDEX CREATED ---")
print("Products:", len(products))
print(
    "Vocabulary size:",
    len(vectorizer.vocabulary_)
)
print(
    "Matrix shape:",
    tfidf_matrix.shape
)

print("\nCreated:")
print(VECTORIZER_FILE)
print(MATRIX_FILE)
print(PRODUCT_IDS_FILE)