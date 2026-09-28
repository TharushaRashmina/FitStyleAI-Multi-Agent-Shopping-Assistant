import pyodbc


# -------------------------------------------------
# SQL Server Repository
# -------------------------------------------------

class SQLServerRepository:

    def __init__(self):

        self.connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            "SERVER=localhost\\MSSQLSERVER4;"
            "DATABASE=FitStyleAI;"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )


    # -------------------------------------------------
    # Connection
    # -------------------------------------------------

    def _connect(self):

        return pyodbc.connect(
            self.connection_string
        )


    # -------------------------------------------------
    # Convert rows to dictionaries
    # -------------------------------------------------

    def _rows_to_dicts(
        self,
        cursor,
        rows
    ):

        columns = [
            column[0]
            for column
            in cursor.description
        ]

        return [
            dict(
                zip(
                    columns,
                    row
                )
            )
            for row in rows
        ]


    # -------------------------------------------------
    # Get total product count
    # -------------------------------------------------

    def get_product_count(self):

        connection = self._connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM dbo.Products
            """
        )

        count = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        return count


    # -------------------------------------------------
    # Get one product
    # -------------------------------------------------

    def get_product_by_id(
        self,
        product_id
    ):

        connection = self._connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM dbo.Products
            WHERE product_id = ?
            """,
            str(product_id)
        )

        row = cursor.fetchone()

        if row is None:

            cursor.close()
            connection.close()

            return None

        columns = [
            column[0]
            for column
            in cursor.description
        ]

        product = dict(
            zip(
                columns,
                row
            )
        )

        cursor.close()
        connection.close()

        return product


    # -------------------------------------------------
    # Get multiple products
    # -------------------------------------------------

    def get_products_by_ids(
        self,
        product_ids
    ):

        if not product_ids:
            return []

        product_ids = [
            str(product_id)
            for product_id
            in product_ids
        ]

        placeholders = ",".join(
            "?"
            for _ in product_ids
        )

        query = f"""
            SELECT *
            FROM dbo.Products
            WHERE product_id IN (
                {placeholders}
            )
        """

        connection = self._connect()
        cursor = connection.cursor()

        cursor.execute(
            query,
            product_ids
        )

        rows = cursor.fetchall()

        products = (
            self._rows_to_dicts(
                cursor,
                rows
            )
        )

        cursor.close()
        connection.close()

        # Preserve original ranking order
        product_lookup = {
            str(product["product_id"]):
                product
            for product
            in products
        }

        ordered_products = [
            product_lookup[product_id]
            for product_id
            in product_ids
            if product_id in product_lookup
        ]

        return ordered_products


    # -------------------------------------------------
    # Get product variants
    # -------------------------------------------------

    def get_variants_by_product(
        self,
        product_id
    ):

        connection = self._connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM dbo.ProductVariants
            WHERE product_id = ?
            """,
            str(product_id)
        )

        rows = cursor.fetchall()

        variants = (
            self._rows_to_dicts(
                cursor,
                rows
            )
        )

        cursor.close()
        connection.close()

        return variants


    # -------------------------------------------------
    # Get available variants
    # -------------------------------------------------

    def get_available_variants(
        self,
        product_id
    ):

        connection = self._connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM dbo.ProductVariants
            WHERE product_id = ?
              AND available = 1
            """,
            str(product_id)
        )

        rows = cursor.fetchall()

        variants = (
            self._rows_to_dicts(
                cursor,
                rows
            )
        )

        cursor.close()
        connection.close()

        return variants


    # -------------------------------------------------
    # Check exact available size
    # -------------------------------------------------

    def has_available_size(
        self,
        product_id,
        size
    ):

        connection = self._connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM dbo.ProductVariants
            WHERE product_id = ?
              AND UPPER([size]) = UPPER(?)
              AND available = 1
            """,
            str(product_id),
            str(size)
        )

        count = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        return count > 0


    # -------------------------------------------------
    # Filter ranked candidate IDs
    # -------------------------------------------------

    def filter_product_ids(
        self,
        candidate_ids,
        filters=None
    ):

        if not candidate_ids:
            return []

        filters = filters or {}

        candidate_ids = [
            str(product_id)
            for product_id
            in candidate_ids
        ]

        placeholders = ",".join(
            "?"
            for _ in candidate_ids
        )

        conditions = [
            f"""
            p.product_id IN (
                {placeholders}
            )
            """
        ]

        parameters = list(
            candidate_ids
        )


        # -----------------------------------------
        # Category - exact match
        # -----------------------------------------

        if filters.get("category"):

            conditions.append(
                """
                LOWER(
                    COALESCE(
                        p.category,
                        ''
                    )
                ) = ?
                """
            )

            parameters.append(
                str(
                    filters["category"]
                ).strip().lower()
            )


        # -----------------------------------------
        # Target group - exact match
        # -----------------------------------------

        if filters.get("target_group"):

            conditions.append(
                """
                LOWER(
                    COALESCE(
                        p.target_group,
                        ''
                    )
                ) = ?
                """
            )

            parameters.append(
                str(
                    filters["target_group"]
                ).strip().lower()
            )


        # -----------------------------------------
        # Material
        # -----------------------------------------

        if filters.get("material"):

            conditions.append(
                """
                LOWER(
                    COALESCE(
                        p.material,
                        ''
                    )
                ) LIKE ?
                """
            )

            parameters.append(
                "%"
                + str(
                    filters["material"]
                ).strip().lower()
                + "%"
            )


        # -----------------------------------------
        # Style
        # -----------------------------------------

        if filters.get("style"):

            conditions.append(
                """
                LOWER(
                    COALESCE(
                        p.style,
                        ''
                    )
                ) LIKE ?
                """
            )

            parameters.append(
                "%"
                + str(
                    filters["style"]
                ).strip().lower()
                + "%"
            )


        # -----------------------------------------
        # Occasion
        # -----------------------------------------

        if filters.get("occasion"):

            conditions.append(
                """
                LOWER(
                    COALESCE(
                        p.occasion,
                        ''
                    )
                ) LIKE ?
                """
            )

            parameters.append(
                "%"
                + str(
                    filters["occasion"]
                ).strip().lower()
                + "%"
            )


        # -----------------------------------------
        # Color
        # -----------------------------------------

        if filters.get("color"):

            conditions.append(
                """
                LOWER(
                    COALESCE(
                        p.color,
                        ''
                    )
                ) LIKE ?
                """
            )

            parameters.append(
                "%"
                + str(
                    filters["color"]
                ).strip().lower()
                + "%"
            )


        # -----------------------------------------
        # Maximum price
        # -----------------------------------------

        if filters.get("max_price") is not None:

            conditions.append(
                """
                p.base_price <= ?
                """
            )

            parameters.append(
                float(
                    filters["max_price"]
                )
            )


        # -----------------------------------------
        # Exact available size
        # -----------------------------------------

        if filters.get("size"):

            conditions.append(
                """
                EXISTS (
                    SELECT 1
                    FROM dbo.ProductVariants v
                    WHERE
                        v.product_id = p.product_id

                        AND UPPER(
                            v.[size]
                        ) = UPPER(?)

                        AND v.available = 1
                )
                """
            )

            parameters.append(
                str(
                    filters["size"]
                ).strip()
            )


        # -----------------------------------------
        # Build query
        # -----------------------------------------

        where_clause = (
            " AND ".join(
                conditions
            )
        )

        query = f"""
            SELECT p.product_id
            FROM dbo.Products p
            WHERE {where_clause}
        """

        connection = self._connect()
        cursor = connection.cursor()

        cursor.execute(
            query,
            parameters
        )

        rows = cursor.fetchall()

        eligible_set = {
            str(row[0])
            for row in rows
        }

        cursor.close()
        connection.close()

        # Preserve BM25 / Hybrid ranking order
        filtered_ids = [
            product_id
            for product_id
            in candidate_ids
            if product_id in eligible_set
        ]

        return filtered_ids

    # -------------------------------------------------
    # Get products for vector indexing
    # -------------------------------------------------

    def get_products_for_vector_index(self):
    
        connection = self._connect()
        cursor = connection.cursor()
    
        cursor.execute(
            """
            SELECT
                product_id,
                product_name,
                search_text
            FROM dbo.Products
            ORDER BY product_id
            """
        )
    
        rows = cursor.fetchall()
    
        products = (
            self._rows_to_dicts(
                cursor,
                rows
            )
        )
    
        cursor.close()
        connection.close()
    
        return products
