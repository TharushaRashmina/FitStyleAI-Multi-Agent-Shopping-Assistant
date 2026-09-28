from pathlib import Path

import pandas as pd
import pyodbc


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

VARIANTS_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "product_variants_final.csv"
)


# -------------------------------------------------
# SQL Server connection
# -------------------------------------------------

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=FitStyleAI;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def clean_value(value):

    if pd.isna(value):
        return None

    return value


def to_bit(value):

    if pd.isna(value):
        return None

    if isinstance(value, bool):
        return int(value)

    text = str(value).strip().lower()

    if text in {
        "true",
        "1",
        "yes"
    }:
        return 1

    if text in {
        "false",
        "0",
        "no"
    }:
        return 0

    return None


# -------------------------------------------------
# Load CSV files
# -------------------------------------------------

products_df = pd.read_csv(
    PRODUCTS_FILE,
    dtype={"product_id": str}
)

variants_df = pd.read_csv(
    VARIANTS_FILE,
    dtype={
        "variant_id": str,
        "product_id": str,
        "size": str
    }
)


print(
    "\n--- SOURCE DATA ---"
)

print(
    "Products:",
    len(products_df)
)

print(
    "Variants:",
    len(variants_df)
)


# -------------------------------------------------
# Connect
# -------------------------------------------------

connection = pyodbc.connect(
    CONNECTION_STRING
)

cursor = connection.cursor()


try:

    # -------------------------------------------------
    # Check existing rows
    # -------------------------------------------------

    cursor.execute(
        "SELECT COUNT(*) FROM dbo.Products"
    )

    existing_products = (
        cursor.fetchone()[0]
    )

    cursor.execute(
        "SELECT COUNT(*) FROM dbo.ProductVariants"
    )

    existing_variants = (
        cursor.fetchone()[0]
    )


    print(
        "\n--- CURRENT DATABASE ---"
    )

    print(
        "Existing Products:",
        existing_products
    )

    print(
        "Existing Variants:",
        existing_variants
    )


    # Prevent accidental duplicate import
    if (
        existing_products > 0
        or existing_variants > 0
    ):

        print(
            "\nImport stopped."
        )

        print(
            "Database tables already contain data."
        )

        raise SystemExit


    # -------------------------------------------------
    # Insert Products
    # -------------------------------------------------

    product_sql = """
        INSERT INTO dbo.Products (
            product_id,
            source,
            product_name,
            brand,
            product_type_raw,
            tags,
            description,
            base_price,
            image_url,
            product_url,
            available_any,
            category,
            sub_category,
            target_group,
            material,
            fit_type,
            pattern,
            style,
            occasion,
            color,
            search_text
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """


    product_rows = []

    for _, row in products_df.iterrows():

        product_rows.append((

            clean_value(
                row["product_id"]
            ),

            clean_value(
                row["source"]
            ),

            clean_value(
                row["product_name"]
            ),

            clean_value(
                row["brand"]
            ),

            clean_value(
                row["product_type_raw"]
            ),

            clean_value(
                row["tags"]
            ),

            clean_value(
                row["description"]
            ),

            float(
                row["base_price"]
            ),

            clean_value(
                row["image_url"]
            ),

            clean_value(
                row["product_url"]
            ),

            to_bit(
                row["available_any"]
            ),

            clean_value(
                row["category"]
            ),

            clean_value(
                row["sub_category"]
            ),

            clean_value(
                row["target_group"]
            ),

            clean_value(
                row["material"]
            ),

            clean_value(
                row["fit_type"]
            ),

            clean_value(
                row["pattern"]
            ),

            clean_value(
                row["style"]
            ),

            clean_value(
                row["occasion"]
            ),

            clean_value(
                row["color"]
            ),

            clean_value(
                row["search_text"]
            )
        ))


    cursor.fast_executemany = True

    cursor.executemany(
        product_sql,
        product_rows
    )


    print(
        "\nProducts inserted:",
        len(product_rows)
    )


    # -------------------------------------------------
    # Insert Product Variants
    # -------------------------------------------------

    variant_sql = """
        INSERT INTO dbo.ProductVariants (
            variant_id,
            product_id,
            size,
            color,
            available,
            price,
            sku
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?
        )
    """


    variant_rows = []

    for _, row in variants_df.iterrows():

        variant_rows.append((

            clean_value(
                row["variant_id"]
            ),

            clean_value(
                row["product_id"]
            ),

            clean_value(
                row["size"]
            ),

            clean_value(
                row["color"]
            ),

            to_bit(
                row["available"]
            ),

            float(
                row["price"]
            ),

            clean_value(
                row["sku"]
            )
        ))


    cursor.executemany(
        variant_sql,
        variant_rows
    )


    print(
        "Variants inserted:",
        len(variant_rows)
    )


    # -------------------------------------------------
    # Commit
    # -------------------------------------------------

    connection.commit()


    # -------------------------------------------------
    # Verify counts
    # -------------------------------------------------

    cursor.execute(
        "SELECT COUNT(*) FROM dbo.Products"
    )

    final_products = (
        cursor.fetchone()[0]
    )


    cursor.execute(
        "SELECT COUNT(*) FROM dbo.ProductVariants"
    )

    final_variants = (
        cursor.fetchone()[0]
    )


    print(
        "\n--- IMPORT COMPLETE ---"
    )

    print(
        "Products in SQL Server:",
        final_products
    )

    print(
        "Variants in SQL Server:",
        final_variants
    )


except Exception as error:

    connection.rollback()

    print(
        "\n--- IMPORT FAILED ---"
    )

    print(
        "Error:",
        error
    )


finally:

    cursor.close()
    connection.close()