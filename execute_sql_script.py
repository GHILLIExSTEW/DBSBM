import pymysql

# Database configuration
MYSQL_HOST = "na05-sql.pebblehost.com"
MYSQL_PORT = 3306
MYSQL_USER = "customer_990306_Server_database"
MYSQL_PASSWORD = "NGNrWmR@IypQb4k@tzgk+NnI"
MYSQL_DB = "customer_990306_Server_database"

# Path to the SQL script
SQL_SCRIPT_PATH = "fix_bets_table.sql"

def execute_sql_script():
    try:
        # Connect to the database
        connection = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )

        with connection.cursor() as cursor:
            # Read the SQL script
            with open(SQL_SCRIPT_PATH, "r") as file:
                sql_script = file.read()

            # Execute the SQL script
            for statement in sql_script.split(";"):
                if statement.strip():
                    cursor.execute(statement)

            # Commit changes
            connection.commit()

        print("SQL script executed successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    execute_sql_script()
