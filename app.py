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
                dcc.Dropdown(
                    id="product-filter",
                    options=[{"label": product, "value": product} for product in products],
                    value="All",
                    clearable=False,
                    className="dropdown",
                    placeholder="Select Product",
                ),
                dcc.Dropdown(
                    id="customer-filter",
                    options=[{"label": customer, "value": customer} for customer in customers],
                    value="All",
                    clearable=False,
                    className="dropdown",
                    placeholder="Select Customer",
                ),
                dcc.Dropdown(
                    id="category-filter",
                    options=[{"label": category, "value": category} for category in categories],
                    value="All",
                    clearable=False,
                    className="dropdown",
                    placeholder="Select Category",
                ),
                dcc.Dropdown(
                    id="brand-filter",
                    options=[{"label": brand, "value": brand} for brand in brands],
                    value="All",
                    clearable=False,
                    className="dropdown",
                    placeholder="Select Brand",
                ),
                dcc.DatePickerRange(
                    id="date-range",
                    min_date_allowed=data["Date"].min().date(),
                    max_date_allowed=data["Date"].max().date(),
                    start_date=data["Date"].min().date(),
                    end_date=data["Date"].max().date(),
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                dcc.Graph(id="sales-by-category-quarter"),  # Move this chart to the top
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

    # Aggregate data by month
    filtered_data["date"] = pd.to_datetime(filtered_data["date"])
    monthly_data = (
        filtered_data.set_index("date")
        .resample("M")
        .sum()
        .reset_index()
    )

    # Monthly Sales Trend Line Chart
    sales_trend_figure = {
        "data": [
            {
                "x": monthly_data["date"],
                "y": monthly_data["total_amount"],
                "type": "scatter",
                "mode": "lines+markers",
                "line": {"shape": "spline", "color": "#1f77b4"},
                "name": "Sales Trend (Monthly)",
                "hovertemplate": "Date: %{x|%Y-%m}<br>Sales Amount: %{y}<extra></extra>",
            },
        ],
        "layout": {
            "title": "Monthly Sales Trend",
            "xaxis": {"title": "Month"},
            "yaxis": {"title": "Sales Amount"},
        },
    }



    # Stacked Bar Chart for Total Sales Amount by Product and Customer
    total_sales_figure = {
        "data": [
            {
                "x": filtered_data["date"],
                "y": filtered_data["total_amount"],
                "type": "bar",
                "marker": {"color": "#ff7f0e"},
                "name": "Total Sales",
                "hovertemplate": "Date: %{x}<br>Amount: %{y}<extra></extra>",
            },
        ],
        "layout": {
            "title": "Total Sales Amount",
            "xaxis": {"title": "Date"},
            "yaxis": {"title": "Total Amount"},
            "barmode": "stack",
        },
    }

    # New Chart: Stacked Bar Chart for Sales by Product Category and Quarter
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
                "hovertemplate": "Quarter: %{x}<br>Total Sales: %{y}<extra></extra>",
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

    return sales_trend_figure, total_sales_figure, sales_by_category_quarter

if __name__ == "__main__":
    app.run_server(debug=True)
