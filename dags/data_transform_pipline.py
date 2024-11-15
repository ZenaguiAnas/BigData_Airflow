from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.email import send_email
from mysql.connector import Connect
import pandas as pd

# Airflow Variables 
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": True,  # Set this to True to enable email notifications on failure
    "email_on_retry": False,  # Set this to False to prevent emails on retries
    "email": ["zenaguianas20@gmail.com"],  # Replace with your email address
    "retries": 3,  # Number of retries before failing a task
    "retry_delay": timedelta(minutes=1000),  # Delay between retries
}


def task_failure_alert(context):
    task_instance = context.get("task_instance")
    task_id = task_instance.task_id
    dag_id = task_instance.dag_id
    execution_date = context.get("execution_date")
    message = f"Task {task_id} in DAG {dag_id} failed on {execution_date}."
    
    send_email(
        to=["anas.zenagui@etu.uae.ac.ma"],  # Recipient email
        subject=f"Airflow Task Failed: {task_id}",
        html_content=message
    )


'''
# 
# Extract Functions 
# 
# 
''' 
def extract_customer_data(**kawrgs):
    conn = Connect(
        host="host.docker.internal",  # your host, usually localhost
        user="root",  # your username
        password="",  # password leave it blank if there isn't any
        port="3307",  # port (3306 default)
        db="ecommercedb", # name of the database
    )  

    pd.read_sql(sql=f"select * from `customer`", con=conn).to_csv("/tmp/extract_customer_data.csv", index=False)


def extract_product_data(**kawrgs):
    conn = Connect(
        host="host.docker.internal",  # your host, usually localhost
        user="root",  # your username
        password="",  # password leave it blank if there isn't any
        port="3307",  # port (3306 default)
        db="ecommercedb", # name of the database
    )  

    pd.read_sql(sql=f"select * from `product`", con=conn).to_csv("/tmp/extract_product_data.csv", index=False)

def extract_order_data(**kawrgs):
    conn = Connect(
        host="host.docker.internal",  # your host, usually localhost
        user="root",  # your username
        password="",  # password leave it blank if there isn't any
        port="3307",  # port (3306 default)
        db="ecommercedb", # name of the database
    )  

    pd.read_sql(sql=f"SELECT * FROM `order` o JOIN `order-item` oi ON o.order_id=oi.order_id ", con=conn).to_csv("/tmp/extract_order_data.csv", index=False)

def extract_date_data():

    # create a date range for the date dimension
    start_date = "2021-01-01"
    end_date = "2022-12-31"

    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    date_dimension = pd.DataFrame(date_range, columns=["date"])

    # add columns for year, quarter, month, day, and weekday
    date_dimension["day"] = date_dimension["date"].dt.day
    date_dimension["month"] = date_dimension["date"].dt.month
    date_dimension["quarter"] = date_dimension["date"].dt.quarter
    date_dimension["year"] = date_dimension["date"].dt.year
    date_dimension["month_name"] = date_dimension["date"].dt.strftime('%B')
    date_dimension['dayName'] =  date_dimension["date"].dt.strftime('%A')
    date_dimension["dayOfWeek"] = date_dimension["date"].dt.weekday
    date_dimension['dayOfMonth'] = date_dimension["date"].dt.strftime('%d') 

    date_dimension.to_csv("/tmp/date.csv", index=False)


'''
# 
# Transform Functions
# 
# 
''' 
def transform_customer_data():
    df = pd.read_csv("/tmp/extract_customer_data.csv")

    # drop null values
    df = df.dropna(axis="index", how="any")

    df["first_name"] = df["first_name"].str.strip().str.title()
    df["last_name"] = df["last_name"].str.strip().str.title()
    df["full_name"] = df["first_name"] + " " + df["last_name"]
    df["email"] = df["email"].str.strip().str.lower()

    # transform process ...

    # final columns
    cols = [
        "customer_id", "full_name", "phone_number", "email", "address"
    ]

    df = df[cols]

    # store data locally
    df.to_csv("/tmp/transformed_customer_data.csv", index=False)


def transform_product_data():
    
    df = pd.read_csv("/tmp/extract_product_data.csv")

    # drop null values
    df = df.dropna(axis="index", how="any")

    # transform process ...

    cols = [
        "product_id",
        "product_name",
        "product_brand",
        "product_category",
        "product_price",
    ]

    df = df[cols]

    df.to_csv("/tmp/transformed_product_data.csv", index=False)


def transform_order_data():
    
    df = pd.read_csv("/tmp/extract_order_data.csv")

    # drop null values
    df = df.dropna(axis="index", how="any")

    # transform process ...

    cols = [
        "order_id",
        "order_date",
        "customer_id",
        "product_id",
        "order_status", 
        "product_price",
        "quantity" 
    ]

    df = df[cols]

    df.to_csv("/tmp/transformed_order_data.csv", index=False)


'''
# 
# Load Functions 
# 
# 
''' 
def load_customer_data():
    
    try :
        conn = Connect(
            host="host.docker.internal",  # your host, usually localhost
            user="root",  # your username
            password="",  # password leave it blank if there isn't any
            port="3307",  # port (3306 default)
            db="dw_ecom", # name of the database
        )

        conn.autocommit = False

        cur = conn.cursor()
    except :
            raise Exception("MySql db connection error")

#  stagged data 
    df = pd.read_csv('/tmp/transformed_customer_data.csv')

    # sql statement
    sql_into_dim = f"""
        INSERT INTO `customer_dim` (customer_id, full_name, phone_number, email, address)  VALUES(%s, %s, %s, %s, %s)
    """

    # insert rows to dimension table
    for i, row in df.iterrows():
        cur.execute(sql_into_dim, list(row))

    # commit changes
    conn.commit()
    
    conn.close()


def load_product_data():
    try :
        
        conn = Connect(
            host="host.docker.internal",  # your host, usually localhost
            user="root",  # your username
            password="",  # password leave it blank if there isn't any
            port="3307",  # port (3306 default)
            db="dw_ecom", # name of the database
        )

        conn.autocommit = False
        
        cur = conn.cursor()
    except :
            raise Exception("MySql db connection error")

    #  stagged data 
    df = pd.read_csv('/tmp/transformed_product_data.csv')

    # sql statement
    sql_into_dim = f"""
        INSERT INTO `product_dim` (product_id, product_name, product_brand, product_category, product_price)  VALUES(%s, %s, %s, %s, %s);
    """

    # insert rows to dimension table
    for i, row in df.iterrows():
        cur.execute(sql_into_dim, list(row))

    # commit changes
    conn.commit()
    
    conn.close()
    

def load_order_data():
    try:
        conn = Connect(
            host="host.docker.internal",  # your host, usually localhost
            user="root",  # your username
            password="",  # password leave it blank if there isn't any
            port="3307",  # port (3306 default)
            db="dw_ecom",  # name of the database
        )
        conn.autocommit = False
        cur = conn.cursor()

        # Load staged order data
        df = pd.read_csv('/tmp/transformed_order_data.csv')

        # Insert date entries to the date_dim table
        order_dates = df['order_date'].unique()
        for order_date in order_dates:
            # Check if the order_date already exists in the date_dim table
            check_sql = f"SELECT COUNT(*) FROM date_dim WHERE date = '{order_date}'"
            cur.execute(check_sql)
            if cur.fetchone()[0] == 0:
                # Insert missing date into date_dim
                insert_date_sql = f"INSERT INTO date_dim (date) VALUES ('{order_date}')"
                cur.execute(insert_date_sql)

        # Now insert the data into the order_dim table
        sql_into_dim = """
            INSERT INTO `order_dim` (order_id, order_date, customer_id, product_id, order_status, product_price, quantity)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        for i, row in df.iterrows():
            cur.execute(sql_into_dim, list(row))

        # Commit the transaction
        conn.commit()

    except Exception as e:
        print(f"Error loading order data: {e}")
        conn.rollback()
    finally:
        conn.close()

       
       
def load_date_data():
    try :
        
        conn = Connect(
            host="host.docker.internal",  # your host, usually localhost
            user="root",  # your username
            password="",  # password leave it blank if there isn't any
            port="3307",  # port (3306 default)
            db="dw_ecom", # name of the database
        )  

        conn.autocommit = False
        
        cur = conn.cursor()
    except :
            raise Exception("MySql db connection error")

    #  stagged data 
    df = pd.read_csv('/tmp/date.csv')

    # sql statement
    sql_into_dim = f"""
        INSERT INTO `date_dim`  VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    # insert rows to dimension table
    for i, row in df.iterrows():
        cur.execute(sql_into_dim, list(row))

    # commit changes
    conn.commit()
    
    conn.close()
    
    
def create_fact_table():
    conn = Connect(
        host="host.docker.internal",  # your host, usually localhost
        user="root",  # your username
        password="",  # password leave it blank if there isn't any
        port="3307",  # port (3306 default)
        db="dw_ecom", # name of the database
    )
    
    cur = conn.cursor()
    
    # Check if the table exists, and drop it if it does (optional)
    cur.execute('DROP TABLE IF EXISTS sales_fact;')
    
    # Create the sales_fact table if it doesn't exist
    sql = '''
        CREATE TABLE IF NOT EXISTS sales_fact (
            `date` DATE,
            `order_id` INT,
            `product_id` INT,
            `customer_id` INT,
            `total_amount` DECIMAL(19, 4)
        );
    ''' 
    cur.execute(sql)

    # Insert data into the sales_fact table
    sql_insert = '''
        INSERT INTO sales_fact (`date`, `order_id`, `product_id`, `customer_id`, `total_amount`)
        SELECT o.order_date AS `date`, 
               o.order_id, 
               p.product_id, 
               c.customer_id, 
               (o.quantity * o.product_price) AS `total_amount`
        FROM order_dim AS o
        JOIN product_dim p ON p.product_id = o.product_id
        JOIN customer_dim c ON c.customer_id = o.customer_id;
    '''
    cur.execute(sql_insert)

    # Add foreign key constraints
    cur.execute('ALTER TABLE sales_fact ADD FOREIGN KEY (`date`) REFERENCES date_dim(`date`);')
    cur.execute('ALTER TABLE sales_fact ADD FOREIGN KEY (`customer_id`) REFERENCES customer_dim(`customer_id`);')
    cur.execute('ALTER TABLE sales_fact ADD FOREIGN KEY (`product_id`) REFERENCES product_dim(`product_id`);')

    # Commit the transaction
    conn.commit()
    
    # Close the connection
    conn.close()



dag = DAG(
    "example_of_ecommerce_pipeline",
    start_date=datetime(2022, 3, 5),
    default_args=default_args,
    schedule_interval="@daily",
)

extract_customer_task = PythonOperator(
    task_id="extract_customer_data", 
    python_callable=extract_customer_data, 
    dag=dag,
    on_failure_callback=task_failure_alert
)

extract_product_task = PythonOperator(
    task_id="extract_product_data", 
    python_callable=extract_product_data, 
    dag=dag,
    on_failure_callback=task_failure_alert
)

extract_order_task = PythonOperator(
    task_id="extract_order_data", 
    python_callable=extract_order_data, 
    dag=dag,
    on_failure_callback=task_failure_alert
)

extract_date_task = PythonOperator(
    task_id="extract_date_data", 
    python_callable=extract_date_data, 
    dag=dag,
    on_failure_callback=task_failure_alert
)

transform_customer_task = PythonOperator(
    task_id="transform_customer_data", 
    python_callable=transform_customer_data, 
    dag=dag,
    on_failure_callback=task_failure_alert
)

transform_product_task = PythonOperator(
    task_id="transform_product_data", 
    python_callable=transform_product_data, 
    dag=dag,
    on_failure_callback=task_failure_alert
)

transform_order_task = PythonOperator(
    task_id="transform_order_data", 
    python_callable=transform_order_data, 
    dag=dag,
    on_failure_callback=task_failure_alert
)

load_data_task = PythonOperator(
    task_id="load_dim_dimension", 
    python_callable=load_date_data, 
    dag=dag,
    on_failure_callback=task_failure_alert
)

# load customer dimension data task 
load_customer_dim_task = PythonOperator(
    task_id="load_customer_dim_data",
    python_callable=load_customer_data,
    dag=dag,
    on_failure_callback=task_failure_alert
)

# load product dimension data task 
load_product_dim_task = PythonOperator(
    task_id="load_product_dim_data",
    python_callable=load_product_data,
    dag=dag,
    on_failure_callback=task_failure_alert
)

# load order dimension data task 
load_order_dim_task = PythonOperator(
    task_id="load_order_dim_data",
    python_callable=load_order_data,
    dag=dag,
    on_failure_callback=task_failure_alert
)


# create fact sales table task 
create_fact_sales = PythonOperator(
    task_id="create_fact_table",
    python_callable=create_fact_table,
    dag=dag,
    on_failure_callback=task_failure_alert
)

[extract_customer_task >> transform_customer_task >> load_customer_dim_task,
extract_product_task >> transform_product_task >> load_product_dim_task,
extract_order_task >> transform_order_task >> load_order_dim_task,
extract_date_task >> load_data_task] >> create_fact_sales 