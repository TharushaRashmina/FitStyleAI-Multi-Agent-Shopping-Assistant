import pyodbc


# -------------------------------------------------
# SQL Server connection
# -------------------------------------------------

connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=FitStyleAI;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)


try:

    connection = pyodbc.connect(
        connection_string
    )

    cursor = connection.cursor()

    cursor.execute(
        "SELECT DB_NAME();"
    )

    database_name = (
        cursor.fetchone()[0]
    )

    print(
        "\n--- SQL SERVER CONNECTION ---"
    )

    print(
        "Status: SUCCESS"
    )

    print(
        "Connected Database:",
        database_name
    )


    # Check tables
    cursor.execute("""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME;
    """)

    tables = cursor.fetchall()

    print(
        "\nTables:"
    )

    for table in tables:

        print(
            "-",
            table[0]
        )


    cursor.close()
    connection.close()


except Exception as error:

    print(
        "\n--- SQL SERVER CONNECTION ---"
    )

    print(
        "Status: FAILED"
    )

    print(
        "Error:",
        error
    )