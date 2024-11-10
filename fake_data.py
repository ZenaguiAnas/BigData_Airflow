from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()

# Data to store SQL statements
sql_statements = []

# Create a customer
customer_id = 1
first_name = fake.first_name()
last_name = fake.last_name()
email = fake.email()
phone_number = fake.phone_number()
address = fake.street_address()
city = fake.city()
state = fake.state()
zip_code = fake.zipcode()

sql_statements.append(f"INSERT INTO `customer` VALUES ({customer_id}, '{first_name}', '{last_name}', '{email}', '{phone_number}', '{address}', '{city}', '{state}', '{zip_code}');")

# Generate products
categories = ["PC", "Phones", "Headphones", "Watches"]
brands = ["Apple", "Samsung", "LG", "Redmi"]
product_data = []

for product_id in range(1, 51):
    product_name = fake.word().capitalize()
    product_description = fake.sentence(nb_words=6)
    product_category = random.choice(categories)
    product_brand = random.choice(brands)
    product_price = round(random.uniform(100, 2000), 2)
    product_quantity = random.randint(1, 100)

    sql_statements.append(f"INSERT INTO `product` VALUES ({product_id}, '{product_name}', '{product_description}', '{product_category}', '{product_brand}', {product_price}, {product_quantity});")
    product_data.append((product_id, product_name, product_price))

# Generate orders and order items
order_id = 1
start_date = datetime(2020, 1, 1)
end_date = datetime(2023, 12, 31)

for _ in range(50):  # 50 purchases
    order_date = fake.date_between_dates(date_start=start_date, date_end=end_date)
    order_status = random.choice(["Completed", "Shipped", "Delivered", "Pending"])
    shipping_address = fake.address().replace('\n', ', ')
    billing_address = fake.address().replace('\n', ', ')

    sql_statements.append(f"INSERT INTO `order` VALUES ({order_id}, {customer_id}, '{order_date}', '{order_status}', '{shipping_address}', '{billing_address}');")

    # Add order items (assuming each order has one product for simplicity)
    product_id, product_name, product_price = random.choice(product_data)
    quantity = random.randint(1, 5)
    order_item_id = order_id  # same as order_id for simplicity

    sql_statements.append(f"INSERT INTO `order-item` VALUES ({order_item_id}, {order_id}, {product_id}, '{product_name}', {product_price}, {quantity});")

    order_id += 1

# Write SQL statements to a file
with open('ecommerce_data.sql', 'w') as file:
    for statement in sql_statements:
        file.write(statement + '\n')

print("SQL data generated and saved to ecommerce_data.sql.")
