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
products = data["product_name"].sort_values().unique()
customers = data["full_name"].sort_values().unique()

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
                    value=products[0],
                    clearable=False,
                    className="dropdown",
                    placeholder="Select Product",
                ),
                dcc.Dropdown(
                    id="customer-filter",
                    options=[{"label": customer, "value": customer} for customer in customers],
                    value=customers[0],
                    clearable=False,
                    className="dropdown",
                    placeholder="Select Customer",
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
                dcc.Graph(id="sales-trend-chart"),
                dcc.Graph(id="total-sales-chart"),
                dcc.Graph(id="sales-by-category-quarter"),  # New chart for sales by category and quarter
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
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
)
def update_charts(product_name, customer_name, start_date, end_date):
    query = f"""
    SELECT s.date, p.product_name, p.product_category, c.full_name, d.quarter, s.total_amount
    FROM sales_fact s
    JOIN product_dim p ON s.product_id = p.product_id
    JOIN customer_dim c ON s.customer_id = c.customer_id
    JOIN date_dim d ON s.date = d.date
    WHERE p.product_name = '{product_name}'
      AND c.full_name = '{customer_name}'
      AND s.date BETWEEN '{start_date}' AND '{end_date}'
    """
    filtered_data = pd.read_sql(query, con=engine)

    # Sales Trend Line Chart
    sales_trend_figure = {
        "data": [
            {
                "x": filtered_data["date"],
                "y": filtered_data["total_amount"],
                "type": "scatter",
                "mode": "lines+markers",
                "line": {"shape": "spline", "color": "#1f77b4"},  # Smooth line with spline
                "name": "Sales Trend",
                "hovertemplate": "Date: %{x}<br>Sales Amount: %{y}<extra></extra>",
            },
        ],
        "layout": {
            "title": f"Sales Trend for {product_name}",
            "xaxis": {"title": "Date"},
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
                "name": f"Total Sales for {customer_name}",
                "hovertemplate": "Date: %{x}<br>Amount: %{y}<extra></extra>",
            },
        ],
        "layout": {
            "title": f"Total Sales Amount for {customer_name}",
            "xaxis": {"title": "Date"},
            "yaxis": {"title": "Total Amount"},
            "barmode": "stack",  # Enable stacked bar mode
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
