import pyodbc


class UserRepository:

    def __init__(self):
        # Same SQL Server database used by FitStyle AI.
        self.connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            "SERVER=localhost\\MSSQLSERVER4;"
            "DATABASE=FitStyleAI;"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )


    def _connect(self):
        """
        Create a connection to SQL Server.
        """
        return pyodbc.connect(
            self.connection_string
        )


    def _row_to_dict(
        self,
        cursor,
        row
    ):
        """
        Convert a SQL Server row into a Python dictionary.
        """

        if row is None:
            return None

        columns = [
            column[0]
            for column in cursor.description
        ]

        return dict(
            zip(columns, row)
        )


    def get_user_by_email(
        self,
        email: str
    ):
        """
        Find one user using their email address.
        Used mainly during login and registration.
        """

        connection = self._connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    user_id,
                    name,
                    email,
                    password_hash,
                    created_at
                FROM dbo.Users
                WHERE LOWER(email) = LOWER(?)
                """,
                email.strip()
            )

            row = cursor.fetchone()

            return self._row_to_dict(
                cursor,
                row
            )

        finally:
            connection.close()


    def get_user_by_id(
        self,
        user_id: int
    ):
        """
        Find one user using their user ID.
        """

        connection = self._connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    user_id,
                    name,
                    email,
                    password_hash,
                    created_at
                FROM dbo.Users
                WHERE user_id = ?
                """,
                user_id
            )

            row = cursor.fetchone()

            return self._row_to_dict(
                cursor,
                row
            )

        finally:
            connection.close()


    def create_user(
        self,
        name: str,
        email: str,
        password_hash: str
    ):
        """
        Create a new user.

        Important:
        password_hash must already be hashed.
        Never pass a plain-text password here.
        """

        connection = self._connect()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO dbo.Users (
                    name,
                    email,
                    password_hash
                )
                OUTPUT INSERTED.user_id
                VALUES (?, ?, ?)
                """,
                name.strip(),
                email.strip().lower(),
                password_hash
            )

            new_user_id = (
                cursor.fetchone()[0]
            )

            connection.commit()

            return self.get_user_by_id(
                new_user_id
            )

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()