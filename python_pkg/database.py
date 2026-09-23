import os

import psycopg
from dotenv import load_dotenv


# ============================================================
# Load environment variables
# ============================================================

load_dotenv()


# ============================================================
# PostgreSQL configuration
# ============================================================

DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")


# ============================================================
# Validate configuration
# ============================================================

def validate_database_config():
    """
    Validate PostgreSQL configuration.
    """

    required = {
        "DATABASE_HOST": DATABASE_HOST,
        "DATABASE_PORT": DATABASE_PORT,
        "DATABASE_NAME": DATABASE_NAME,
        "DATABASE_USER": DATABASE_USER,
    }

    missing = [
        name
        for name, value in required.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            "Missing database configuration: "
            + ", ".join(missing)
        )


# ============================================================
# PostgreSQL connection
# ============================================================

def get_connection():
    """
    Create and return a PostgreSQL connection.
    """

    validate_database_config()

    return psycopg.connect(
        host=DATABASE_HOST,
        port=DATABASE_PORT,
        dbname=DATABASE_NAME,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
    )


# ============================================================
# Connection test
# ============================================================

if __name__ == "__main__":

    print("======================================")
    print("PostgreSQL Connection Test")
    print("======================================")
    print()

    try:

        connection = get_connection()

        print("Connected to PostgreSQL successfully!")
        print()

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    current_database(),
                    current_user,
                    version();
                """
            )

            result = cursor.fetchone()

            print(f"Database: {result[0]}")
            print(f"User:     {result[1]}")
            print(f"Version:  {result[2]}")

        connection.close()

        print()
        print("Connection closed.")
        print()

        print("======================================")
        print("Test complete")
        print("======================================")

    except Exception as error:

        print("ERROR: Could not connect to PostgreSQL.")
        print()
        print(error)