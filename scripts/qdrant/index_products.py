from pathlib import Path
import sys
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from sentence_transformers import (
    SentenceTransformer
)


# -------------------------------------------------
# Project root
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


# -------------------------------------------------
# Imports
# -------------------------------------------------

from database.sqlserver_repository import (
    SQLServerRepository
)


# -------------------------------------------------
# Configuration
# -------------------------------------------------

QDRANT_PATH = (
    BASE_DIR
    / "data"
    / "qdrant"
)

COLLECTION_NAME = (
    "fitstyle_products"
)

MODEL_NAME = (
    "sentence-transformers/"
    "all-MiniLM-L6-v2"
)

BATCH_SIZE = 64


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def build_text(product):

    search_text = (
        product.get(
            "search_text"
        )
    )

    if search_text:

        return str(
            search_text
        ).strip()


    # Fallback if search_text is empty
    return str(
        product.get(
            "product_name",
            ""
        )
    ).strip()


def create_point_id(
    product_id
):

    # Qdrant IDs should be integer or UUID.
    # Keep original product_id in payload.
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            str(product_id)
        )
    )


# -------------------------------------------------
# Main
# -------------------------------------------------

if __name__ == "__main__":

    repository = (
        SQLServerRepository()
    )


    print(
        "\n--- QDRANT PRODUCT INDEXING ---"
    )


    # ---------------------------------------------
    # Load products from SQL Server
    # ---------------------------------------------

    products = (
        repository
        .get_products_for_vector_index()
    )


    print(
        "Products loaded from SQL Server:",
        len(products)
    )


    if not products:

        raise RuntimeError(
            "No products found in SQL Server."
        )


    # ---------------------------------------------
    # Load embedding model
    # ---------------------------------------------

    print(
        "\nLoading embedding model..."
    )


    model = (
        SentenceTransformer(
            MODEL_NAME,
            local_files_only=True
        )
    )


    vector_size = (
       model.get_embedding_dimension()
    )


    print(
        "Embedding dimension:",
        vector_size
    )


    # ---------------------------------------------
    # Connect Qdrant
    # ---------------------------------------------

    client = (
        QdrantClient(
            path=str(
                QDRANT_PATH
            )
        )
    )


    try:

        # -----------------------------------------
        # Index in batches
        # -----------------------------------------

        total_indexed = 0


        for start in range(
            0,
            len(products),
            BATCH_SIZE
        ):

            batch = products[
                start:
                start + BATCH_SIZE
            ]


            texts = [
                build_text(
                    product
                )
                for product
                in batch
            ]


            embeddings = (
                model.encode(
                    texts,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )
            )


            points = []


            for product, embedding in zip(
                batch,
                embeddings
            ):

                product_id = str(
                    product[
                        "product_id"
                    ]
                )


                points.append(

                    PointStruct(

                        id=create_point_id(
                            product_id
                        ),

                        vector=(
                            embedding.tolist()
                        ),

                        payload={
                            "product_id":
                                product_id
                        }
                    )
                )


            client.upsert(

                collection_name=
                    COLLECTION_NAME,

                points=
                    points
            )


            total_indexed += len(
                points
            )


            print(
                f"Indexed: "
                f"{total_indexed}"
                f"/"
                f"{len(products)}"
            )


        # -----------------------------------------
        # Verify collection
        # -----------------------------------------

        collection_info = (
            client.get_collection(
                COLLECTION_NAME
            )
        )


        print(
            "\n--- INDEXING COMPLETE ---"
        )

        print(
            "Collection:",
            COLLECTION_NAME
        )

        print(
            "Products indexed:",
            total_indexed
        )

        print(
            "Qdrant points:",
            collection_info.points_count
        )


    finally:

        client.close()