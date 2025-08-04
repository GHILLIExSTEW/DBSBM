import os
import sys
import mysql.connector
import asyncpg
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), 'bot', '.env'))

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DB'),
}

POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'password'),
    'database': os.getenv('POSTGRES_DB', 'DBSBM'),
}

# Helper to convert MySQL types to PostgreSQL
MYSQL_TO_PG_TYPES = {
    'int': 'INTEGER',
    'tinyint': 'SMALLINT',
    'smallint': 'SMALLINT', 
    'mediumint': 'INTEGER',
    'bigint': 'BIGINT',
    'varchar': 'VARCHAR',
    'char': 'CHAR',
    'text': 'TEXT',
    'longtext': 'TEXT',
    'datetime': 'TIMESTAMP',
    'timestamp': 'TIMESTAMP',
    'date': 'DATE',
    'time': 'TIME',
    'float': 'REAL',
    'double': 'DOUBLE PRECISION',
    'decimal': 'NUMERIC',
    'blob': 'BYTEA',
    'json': 'JSONB',
}

def get_pg_type(mysql_type):
    base = mysql_type.split('(')[0].lower()
    return MYSQL_TO_PG_TYPES.get(base, 'TEXT')

async def migrate():
    print('Connecting to MySQL...')
    mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
    mysql_cursor = mysql_conn.cursor(dictionary=True)

    print('Connecting to PostgreSQL...')
    pg_conn = await asyncpg.connect(**POSTGRES_CONFIG)

    # Get all tables
    mysql_cursor.execute("SHOW TABLES")
    tables = [row[f'Tables_in_{MYSQL_CONFIG["database"]}'] for row in mysql_cursor.fetchall()]
    print(f'Found tables: {tables}')

    for table in tables:
        print(f'Processing table: {table}')
        # Get columns
        mysql_cursor.execute(f"SHOW COLUMNS FROM `{table}`")
        columns = mysql_cursor.fetchall()
        col_defs = []
        col_names = []
        for col in columns:
            col_name = col['Field']
            col_type = get_pg_type(col['Type'])
            nullable = '' if col['Null'] == 'NO' else 'NULL'
            col_defs.append(f'"{col_name}" {col_type} {nullable}')
            col_names.append(col_name)
        # Create table in PostgreSQL
        create_sql = f'CREATE TABLE IF NOT EXISTS "{table}" ({", ".join(col_defs)});'
        await pg_conn.execute(create_sql)
        print(f'Created table {table} in PostgreSQL.')
        # Fetch all data
        mysql_cursor.execute(f'SELECT * FROM `{table}`')
        rows = mysql_cursor.fetchall()
        if not rows:
            print(f'No data in {table}.')
            continue
        # Insert data
        for row in rows:
            values = []
            for col in col_names:
                value = row[col]
                # Convert datetime objects to the proper format for PostgreSQL
                if hasattr(value, 'strftime'):  # datetime/date object
                    # Keep as datetime object for PostgreSQL
                    values.append(value)
                else:
                    values.append(value)
            placeholders = ', '.join(f'${i+1}' for i in range(len(values)))
            insert_sql = f'INSERT INTO "{table}" ({", ".join(f'"{col}"' for col in col_names)}) VALUES ({placeholders})'
            try:
                await pg_conn.execute(insert_sql, *values)
            except Exception as e:
                print(f'Error inserting row into {table}: {e}')
                continue  # Continue with next row instead of stopping
        print(f'Imported {len(rows)} rows into {table}.')
    await pg_conn.close()
    mysql_conn.close()
    print('Migration complete.')

if __name__ == '__main__':
    asyncio.run(migrate())
