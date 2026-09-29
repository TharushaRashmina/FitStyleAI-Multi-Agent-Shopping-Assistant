from pathlib import Path
import sys

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams
)


# -------------------------------------------------
# Project root
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


# -------------------------------------------------
# Qdrant local storage
# -------------------------------------------------

QDRANT_PATH = (
    BASE_DIR
    / "data"
    / "qdrant"
)

COLLECTION_NAME = (
    "fitstyle_products"
)

VECTOR_SIZE = 384


# -------------------------------------------------
# Connect to local Qdrant
# -------------------------------------------------

client = QdrantClient(
    path=str(QDRANT_PATH)
)


# -------------------------------------------------
# Create collection if it does not exist
# -------------------------------------------------

existing_collections = [
    collection.name
    for collection
    in client.get_collections().collections
]


if COLLECTION_NAME not in existing_collections:

    client.create_collection(

        collection_name=
            COLLECTION_NAME,

        vectors_config=
            VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
    )

    print(
        "\nQdrant collection created."
    )

else:

    print(
        "\nQdrant collection already exists."
    )


# -------------------------------------------------
# Verify
# -------------------------------------------------

collection_info = (
    client.get_collection(
        COLLECTION_NAME
    )
)


print(
    "\n--- QDRANT SETUP ---"
)

print(
    "Collection:",
    COLLECTION_NAME
)

print(
    "Vector Size:",
    VECTOR_SIZE
)

print(
    "Distance:",
    "COSINE"
)

print(
    "Points:",
    collection_info.points_count
)

# Close Qdrant cleanly
client.close()