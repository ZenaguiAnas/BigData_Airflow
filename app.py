import pandas as pd
from dash import Dash, Input, Output, dcc, html
from sqlalchemy import create_engine

# Connect to the MySQL database
engine = create_engine("mysql+mysqlconnector://root:@localhost:3307/dw_ecom")

# Load data from MySQL
data = (
    pd.read_sql("""
        SELECT DISTINCT 
            p.product_name, 
            p.product_category,
            p.product_brand,
            c.full_name, 
            d.date AS order_date,
            d.quarter,
            s.total_amount
        FROM sales_fact s
        JOIN product_dim p ON s.product_id = p.product_id
        JOIN customer_dim c ON s.customer_id = c.customer_id
        JOIN date_dim d ON s.date = d.date
        """, con=engine)
    .assign(Date=lambda data: pd.to_datetime(data["order_date"]))
    .sort_values(by="Date")
)

# Get unique values for filters
products = ["All"] + data["product_name"].sort_values().unique().tolist()
customers = ["All"] + data["full_name"].sort_values().unique().tolist()
categories = ["All"] + data["product_category"].sort_values().unique().tolist()
brands = ["All"] + data["product_brand"].sort_values().unique().tolist()

app = Dash(__name__)
app.title = "Enhanced Sales Analytics"

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.H1("Sales Analytics"),
                html.P("Analyze sales trends and customer interactions."),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        # Dropdowns and Date Picker Range
                        dcc.Dropdown(
                            id="product-filter",
                            options=[{"label": product, "value": product} for product in products],
                            value="All",
                            clearable=False,
                            placeholder="Select Product",
                            className="dropdown",
                        ),
                        dcc.Dropdown(
                            id="customer-filter",
                            options=[{"label": customer, "value": customer} for customer in customers],
                            value="All",
                            clearable=False,
                            placeholder="Select Customer",
                            className="dropdown",
                        ),
                        dcc.Dropdown(
                            id="category-filter",
                            options=[{"label": category, "value": category} for category in categories],
                            value="All",
                            clearable=False,
                            placeholder="Select Category",
                            className="dropdown",
                        ),
                        dcc.Dropdown(
                            id="brand-filter",
                            options=[{"label": brand, "value": brand} for brand in brands],
                            value="All",
                            clearable=False,
                            placeholder="Select Brand",
                            className="dropdown",
                        ),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=data["Date"].min().date(),
                            max_date_allowed=data["Date"].max().date(),
                            start_date=data["Date"].min().date(),
                            end_date=data["Date"].max().date(),
                            className="datepicker",
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flexWrap": "wrap",
                        "justifyContent": "space-between",
                        "gap": "10px",  # Increased gap
                        "padding": "10px",
                        "maxWidth": "1200px",  # Max width for the container
                        "margin": "auto",  # Center the filters
                        "marginBottom": "150px",  # Add bottom margin for spacing between filters and charts
                    },
                    className="filters",
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                dcc.Graph(id="sales-by-category-quarter"),
                html.Div(
                    children=[
                        dcc.Graph(id="products-by-brand"),
                        dcc.Graph(id="products-by-category"),
                    ],
                    style={'display': 'flex', 'justify-content': 'space-around'}
                ),
                dcc.Graph(id="sales-trend-chart"),
                dcc.Graph(id="total-sales-chart"),
            ],
            className="charts",
        ),
    ]
)



@app.callback(
    Output("sales-trend-chart", "figure"),
    Output("total-sales-chart", "figure"),
    Output("sales-by-category-quarter", "figure"),
    Output("products-by-brand", "figure"),
    Output("products-by-category", "figure"),
    Input("product-filter", "value"),
    Input("customer-filter", "value"),
    Input("category-filter", "value"),
    Input("brand-filter", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
)

def update_charts(product_name, customer_name, category, brand, start_date, end_date):
    query_conditions = []
    
    # Filtering conditions based on selected options
    if product_name != "All":
        query_conditions.append(f"p.product_name = '{product_name}'")
    if customer_name != "All":
        query_conditions.append(f"c.full_name = '{customer_name}'")
    if category != "All":
        query_conditions.append(f"p.product_category = '{category}'")
    if brand != "All":
        query_conditions.append(f"p.product_brand = '{brand}'")
    query_conditions.append(f"s.date BETWEEN '{start_date}' AND '{end_date}'")
    
    # Build the WHERE clause
    where_clause = "WHERE " + " AND ".join(query_conditions)
    query = f"""
    SELECT s.date, p.product_name, p.product_category, p.product_brand, c.full_name, d.quarter, s.total_amount
    FROM sales_fact s
    JOIN product_dim p ON s.product_id = p.product_id
    JOIN customer_dim c ON s.customer_id = c.customer_id
    JOIN date_dim d ON s.date = d.date
    {where_clause}
    """
    filtered_data = pd.read_sql(query, con=engine)

    # Monthly Sales Trend Line Chart
    filtered_data["date"] = pd.to_datetime(filtered_data["date"])
    monthly_data = (
        filtered_data.set_index("date")
        .resample("M")
        .sum()
        .reset_index()
    )

    sales_trend_figure = {
        "data": [
            {
                "x": monthly_data["date"],
                "y": monthly_data["total_amount"],
                "type": "scatter",
                "mode": "lines+markers",
                "line": {"shape": "spline", "color": "#1f77b4"},
            },
        ],
        "layout": {
            "title": "Monthly Sales Trend",
            "xaxis": {"title": "Month"},
            "yaxis": {"title": "Sales Amount"},
        },
    }

    # Total Sales Chart
    total_sales_figure = {
        "data": [
            {
                "x": filtered_data["date"],
                "y": filtered_data["total_amount"],
                "type": "bar",
                "marker": {"color": "#ff7f0e"},
            },
        ],
        "layout": {
            "title": "Total Sales Amount",
            "xaxis": {"title": "Date"},
            "yaxis": {"title": "Total Amount"},
            "barmode": "stack",
        },
    }

    # Sales by Category and Quarter
    category_quarter_data = (
        filtered_data.groupby(["quarter", "product_category"])["total_amount"]
        .sum()
        .reset_index()
    )

    sales_by_category_quarter = {
        "data": [
            {
                "x": category_quarter_data[category_quarter_data["product_category"] == category]["quarter"],
                "y": category_quarter_data[category_quarter_data["product_category"] == category]["total_amount"],
                "type": "bar",
                "name": category,
            }
            for category in category_quarter_data["product_category"].unique()
        ],
        "layout": {
            "title": "Total Sales by Product Category and Quarter",
            "xaxis": {"title": "Quarter"},
            "yaxis": {"title": "Total Sales Amount"},
            "barmode": "stack",
        },
    }

    # Pie chart for Products by Brand
    brand_data = filtered_data["product_brand"].value_counts()
    products_by_brand = {
        "data": [
            {
                "labels": brand_data.index,
                "values": brand_data.values,
                "type": "pie",
                "hole": 0.3,
            }
        ],
        "layout": {
            "title": "Products by Brand",
        },
    }

    # Pie chart for Products by Category
    category_data = filtered_data["product_category"].value_counts()
    products_by_category = {
        "data": [
            {
                "labels": category_data.index,
                "values": category_data.values,
                "type": "pie",
                "hole": 0.3,
            }
        ],
        "layout": {
            "title": "Products by Category",
        },
    }

    return sales_trend_figure, total_sales_figure, sales_by_category_quarter, products_by_brand, products_by_category

if __name__ == "__main__":
    app.run_server(debug=True)
