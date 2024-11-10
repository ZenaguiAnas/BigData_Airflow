import os
import pandas as pd
from mysql.connector import connect, Error

# Database connection details
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "port": "3307",
    "database": "ecommercedb"
}

# Load data from CSV to MySQL table
def load_csv_to_mysql(table_name, file_path):
    try:
        # Connect to MySQL
        with connect(**DB_CONFIG) as connection:
            print(f"Connected to MySQL database: {DB_CONFIG['database']}")

            # Read the CSV file
            df = pd.read_csv(file_path)

            # Load data into MySQL
            for _, row in df.iterrows():
                # Dynamically create insert statement based on columns
                placeholders = ", ".join(["%s"] * len(row))
                columns = ", ".join(row.index)
                sql = f"INSERT INTO `{table_name}` ({columns}) VALUES ({placeholders})"

                # Execute insert
                with connection.cursor() as cursor:
                    cursor.execute(sql, tuple(row))
            connection.commit()
            print(f"Data from {file_path} loaded successfully into {table_name}.")

    except Error as e:
        print(f"Error: {e}")

def main():
    # Absolute path to the data directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')

    # Define CSV files and target MySQL tables in loading order
    csv_files = {
        "product": os.path.join(data_dir, "products.csv"),
        "customer": os.path.join(data_dir, "customers.csv"),
        "order": os.path.join(data_dir, "orders.csv"),
        "order-item": os.path.join(data_dir, "order-items.csv")
    }

    # Load each CSV file into the corresponding MySQL table
    for table, file_path in csv_files.items():
        if os.path.exists(file_path):
            print(f"Loading {file_path} into {table} table...")
            load_csv_to_mysql(table, file_path)
        else:
            print(f"File {file_path} not found.")


if __name__ == "__main__":
    main()
