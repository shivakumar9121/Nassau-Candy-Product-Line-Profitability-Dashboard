import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Nassau Candy BI Dashboard",
    page_icon="🍬",
    layout="wide"
)

st.markdown("""
<style>

.main{
    background-color:#0E1117;
}

.block-container{
    padding-top:2rem;
    padding-bottom:2rem;
}

h1{
    color:#4CAF50;
}

h2{
    color:#4CAF50;
}

div[data-testid="stMetric"]{
    background:#1E2229;
    border-radius:15px;
    padding:18px;
    border:1px solid #2E86AB;
    box-shadow:0px 0px 10px rgba(0,0,0,0.4);
}

div[data-testid="stMetricLabel"]{
    color:#FFD166;
    font-size:18px;
}

</style>
""", unsafe_allow_html=True)

# path to the dataset
DATA_PATH = "data/Nassau Candy Distributor.csv"

# colors used across the charts so everything looks consistent
PRIMARY_COLOR = "#2E86AB"
SECONDARY_COLOR = "#F6C85F"

# keep months in order for the trend charts later
month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# -------------------------------------------------
# TITLE
# -------------------------------------------------
st.title("🍬 Nassau Candy Product Line Profitability Dashboard")
st.write("Interactive dashboard for Nassau Candy Distributor")

st.write(f"**📅 Report Date:** {datetime.today().strftime('%d %B %Y')}")

st.caption(
"""
Interactive Business Intelligence Dashboard

Built using Streamlit | Pandas | Plotly | NumPy
"""
)
st.divider()

# -------------------------------------------------
# LOAD DATA
# (using a function + cache so the csv isn't reloaded every time
# a filter is changed)
# -------------------------------------------------
@st.cache_data
def load_data():
    data = pd.read_csv(DATA_PATH)

    data["Order Date"] = pd.to_datetime(data["Order Date"], dayfirst=True, errors="coerce")
    data["Ship Date"] = pd.to_datetime(data["Ship Date"], dayfirst=True, errors="coerce")

    # just in case sales/profit/units have any weird values in them
    for col in ["Sales", "Gross Profit", "Units"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(subset=["Sales", "Gross Profit", "Units"])

    return data


# wrapped in try/except so the app doesn't just crash with a red
# traceback if the csv is missing or something is wrong with it
try:
    df = load_data()
except FileNotFoundError:
    st.error(f"Could not find the data file at '{DATA_PATH}'. Make sure it's inside the data folder.")
    st.stop()
except Exception as e:
    st.error(f"Something went wrong while loading the data: {e}")
    st.stop()

st.success("Dataset Loaded Successfully!")

with st.expander("📄 View Dataset Preview"):
    st.dataframe(df.head())

# -------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------
st.sidebar.header("🔎 Filters")

division = st.sidebar.multiselect(
    "Select Division",
    options=sorted(df["Division"].unique()),
    default=sorted(df["Division"].unique())
)

region = st.sidebar.multiselect(
    "Select Region",
    options=sorted(df["Region"].unique()),
    default=sorted(df["Region"].unique())
)

product = st.sidebar.multiselect(
    "Select Product",
    options=sorted(df["Product Name"].unique()),
    default=sorted(df["Product Name"].unique())
)

# -------------------------------------------------
# APPLY FILTERS
# -------------------------------------------------
filtered_df = df[
    (df["Division"].isin(division)) &
    (df["Region"].isin(region)) &
    (df["Product Name"].isin(product))
]

# if someone unselects everything, don't let the rest of the page
# crash trying to divide by zero / plot empty charts
if filtered_df.empty:
    st.warning("No data matches the current filters. Please select at least one option in the sidebar.")
    st.stop()

# -------------------------------------------------
# KPI CALCULATIONS
# (calculated once here and reused everywhere below instead of
# recalculating the same groupby multiple times)
# -------------------------------------------------
total_sales = filtered_df["Sales"].sum()
total_profit = filtered_df["Gross Profit"].sum()
total_units = filtered_df["Units"].sum()
total_products = filtered_df["Product Name"].nunique()
total_regions = filtered_df["Region"].nunique()
total_divisions = filtered_df["Division"].nunique()

if total_sales > 0:
    average_margin = (total_profit / total_sales) * 100
else:
    average_margin = 0

# -------------------------------------------------
# KPI CARDS - ROW 1
# -------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("💰 Total Sales", f"${total_sales:,.2f}")

with col2:
    st.metric("📈 Total Profit", f"${total_profit:,.2f}")

with col3:
    st.metric("📊 Average Margin", f"{average_margin:.2f}%")

with col4:
    st.metric("📦 Total Units", f"{total_units:,.0f}")

# -------------------------------------------------
# KPI CARDS - ROW 2
# -------------------------------------------------
col5, col6, col7 = st.columns(3)

with col5:
    st.metric("🛍️ Products", f"{total_products:,}")

with col6:
    st.metric("🏢 Regions", f"{total_regions:,}")

with col7:
    st.metric("🍫 Divisions", f"{total_divisions:,}")

st.divider()

# ==========================================================
# DASHBOARD TABS
# ==========================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard",
    "📈 Business Insights",
    "🗂 Dataset Explorer",
    "ℹ️ About Project"
])

# ==========================================================
# TAB 1 - DASHBOARD
# ==========================================================
with tab1:

    st.subheader("📈 Revenue by Product")

    product_sales = (
        filtered_df.groupby("Product Name")["Sales"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig = px.bar(
        product_sales,
        x="Product Name",
        y="Sales",
        color="Sales",
        color_continuous_scale="Teal",
        title="Revenue by Product"
    )
    # hide the color scale bar on the side, it doesn't really add
    # anything useful here and just takes up space
    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(tickangle=-35, automargin=True)
    fig.update_yaxes(automargin=True)
    fig.update_layout(template="plotly_dark", height=480, margin=dict(l=40, r=40, t=60, b=40))

    st.plotly_chart(fig, use_container_width=True)

    # ==========================================================
    # DIVISION & REGION ANALYSIS
    # ==========================================================
    st.divider()
    st.subheader("📊 Division & Region Analysis")

    left, right = st.columns(2)

    # -----------------------------
    # LEFT : Division Profit
    # -----------------------------
    with left:
        division_profit = (
            filtered_df.groupby("Division")["Gross Profit"]
            .sum()
            .reset_index()
        )

        fig_division = px.bar(
            division_profit,
            x="Division",
            y="Gross Profit",
            color="Division",
            text_auto=".2s",
            title="Division Profit"
        )
        fig_division.update_traces(textposition="outside")
        fig_division.update_layout(
            template="plotly_dark",
            height=450,
            showlegend=False,
            margin=dict(l=40, r=40, t=60, b=40)
        )

        st.plotly_chart(fig_division, use_container_width=True)

    # -----------------------------
    # RIGHT : Region Revenue
    # -----------------------------
    with right:
        region_sales = (
            filtered_df.groupby("Region")["Sales"]
            .sum()
            .reset_index()
        )

        fig_region = px.pie(
            region_sales,
            names="Region",
            values="Sales",
            hole=0.45,
            title="Revenue by Region"
        )
        fig_region.update_traces(textinfo="label+percent", textposition="outside")
        fig_region.update_layout(
            template="plotly_dark",
            height=450,
            showlegend=False,
            margin=dict(l=40, r=40, t=60, b=40)
        )

        st.plotly_chart(fig_region, use_container_width=True)

    # ==========================================================
    # MONTHLY SALES & PROFIT TREND
    # ==========================================================
    st.divider()
    st.subheader("📅 Monthly Revenue & Profit Trend")

    # group by month name, then reindex so the months show up
    # jan -> dec instead of alphabetically
    monthly_data = (
        filtered_df
        .groupby(filtered_df["Order Date"].dt.month_name())
        .agg(
            Revenue=("Sales", "sum"),
            Profit=("Gross Profit", "sum")
        )
    )
    monthly_data = monthly_data.reindex(month_order)
    monthly_data.index.name = "Month"
    monthly_data = monthly_data.reset_index()

    left, right = st.columns(2)

    with left:
        fig_month_sales = px.line(
            monthly_data,
            x="Month",
            y="Revenue",
            markers=True,
            title="Monthly Revenue",
            color_discrete_sequence=[PRIMARY_COLOR]
        )
        fig_month_sales.update_traces(line_width=3, marker=dict(size=8))
        fig_month_sales.update_layout(
            template="plotly_dark",
            xaxis_title="Month",
            yaxis_title="Revenue ($)",
            height=420,
            margin=dict(l=40, r=40, t=60, b=40)
        )

        st.plotly_chart(fig_month_sales, use_container_width=True)

    with right:
        fig_month_profit = px.line(
            monthly_data,
            x="Month",
            y="Profit",
            markers=True,
            title="Monthly Profit",
            color_discrete_sequence=[SECONDARY_COLOR]
        )
        fig_month_profit.update_traces(line_width=3, marker=dict(size=8))
        fig_month_profit.update_layout(
            template="plotly_dark",
            xaxis_title="Month",
            yaxis_title="Profit ($)",
            height=420,
            margin=dict(l=40, r=40, t=60, b=40)
        )

        st.plotly_chart(fig_month_profit, use_container_width=True)

    # ==========================================================
    # TOP 10 PRODUCTS
    # ==========================================================
    st.divider()
    st.subheader("🏆 Top 10 Best Performing Products")

    top_products = (
        filtered_df
        .groupby("Product Name")
        .agg(
            Total_Sales=("Sales", "sum"),
            Total_Profit=("Gross Profit", "sum"),
            Units=("Units", "sum")
        )
        .reset_index()
    )

    # margin calculated per product from the totals above instead of
    # doing a separate slow lambda groupby like before
    top_products["Average_Margin"] = (
        top_products["Total_Profit"] / top_products["Total_Sales"].replace(0, pd.NA) * 100
    ).fillna(0)

    top_products = (
        top_products
        .sort_values("Total_Sales", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )

    top_products.index = top_products.index + 1
    top_products.index.name = "Rank"

    st.dataframe(
        top_products.style.format({
            "Total_Sales": "${:,.2f}",
            "Total_Profit": "${:,.2f}",
            "Average_Margin": "{:.2f}%",
            "Units": "{:,.0f}"
        }),
        use_container_width=True
    )

# ==========================================================
# TAB 2 - BUSINESS INSIGHTS
# ==========================================================
with tab2:

    # ==========================================================
    # SALES vs PROFIT ANALYSIS
    # ==========================================================
    st.subheader("📈 Sales vs Profit Analysis")

    # Create summary data
    scatter_data = (
        filtered_df.groupby("Product Name")
        .agg(
            Sales=("Sales", "sum"),
            Profit=("Gross Profit", "sum")
        )
        .reset_index()
    )

    # Create scatter chart with standard linear scale
    fig5 = px.scatter(
        scatter_data,
        x="Sales",
        y="Profit",
        size="Profit",
        color="Product Name",
        hover_name="Product Name",
        size_max=35,
        color_discrete_sequence=px.colors.qualitative.Pastel,
        title="Product Sales vs Gross Profit"
    )

    # Polish the marker outlines and set a minimum size constraint for tiny dots
    fig5.update_traces(
        marker=dict(
            line=dict(width=1.2, color="white"),
            opacity=0.85
        ),
        selector=dict(mode='markers')
    )

    # Configure layout and give the legend a clean sidebar structure
    fig5.update_layout(
        template="plotly_dark",
        height=650,
        title_x=0.5,
        xaxis_title="Total Sales ($)",
        yaxis_title="Gross Profit ($)",

        legend=dict(
            title="Products",
            font=dict(size=11),
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.02
        ),
        margin=dict(l=50, r=50, t=60, b=50)
    )

    # Crucial Fix: Manually set tight axis bounds so bottom points aren't squeezed
    fig5.update_xaxes(
        range=[-1000, max(scatter_data["Sales"]) * 1.05],  # Starts right before 0, auto-extends to the max item
        tickformat="$,.0f",
        tickfont=dict(size=12),
        gridcolor="rgba(255,255,255,0.1)"
    )

    fig5.update_yaxes(
        range=[-500, max(scatter_data["Profit"]) * 1.05],  # Starts right before 0, auto-extends to the max item
        tickformat="$,.0f",
        tickfont=dict(size=12),
        gridcolor="rgba(255,255,255,0.1)"
    )

    st.plotly_chart(fig5, use_container_width=True)

    # ==========================================================
    # PARETO ANALYSIS (80/20 RULE)
    # ==========================================================
    st.divider()
    st.subheader("📊 Pareto Analysis (80/20 Rule)")

    pareto = (
        filtered_df.groupby("Product Name")["Sales"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    pareto.columns = ["Product", "Sales"]

    pareto["Cumulative Sales"] = pareto["Sales"].cumsum()

    pareto["Cumulative %"] = (
        pareto["Cumulative Sales"] /
        pareto["Sales"].sum()
    ) * 100

    fig_pareto = go.Figure()

    # Sales Bars
    fig_pareto.add_trace(
        go.Bar(
            x=pareto["Product"],
            y=pareto["Sales"],
            name="Sales",
            marker_color=PRIMARY_COLOR
        )
    )

    # Cumulative Line
    fig_pareto.add_trace(
        go.Scatter(
            x=pareto["Product"],
            y=pareto["Cumulative %"],
            name="Cumulative %",
            mode="lines+markers",
            yaxis="y2",
            line=dict(color=SECONDARY_COLOR, width=3)
        )
    )

    fig_pareto.update_layout(
        template="plotly_dark",
        title="Pareto Analysis of Product Sales",
        xaxis_title="Products",
        yaxis=dict(
            title="Sales ($)"
        ),
        yaxis2=dict(
            title="Cumulative %",
            overlaying="y",
            side="right",
            range=[0, 105]
        ),
        legend=dict(
            orientation="h",
            y=1.05
        ),
        height=600,
        margin=dict(l=40, r=40, t=80, b=40)
    )
    fig_pareto.update_xaxes(tickangle=-35, automargin=True)

    st.plotly_chart(fig_pareto, use_container_width=True)

    # -------------------------------------------------
    # Top Products contributing to 80% of Sales
    # -------------------------------------------------
    st.subheader("🏆 Products contributing to 80% of Revenue")

    top80 = pareto[pareto["Cumulative %"] <= 80]

    st.dataframe(top80, use_container_width=True)

    # ==========================================================
    # MARGIN RISK ANALYSIS
    # ==========================================================
    st.divider()
    st.subheader("⚠️ Margin Risk Analysis")

    # Create summary dataframe
    margin_df = (
        filtered_df
        .groupby("Product Name")
        .agg(
            Sales=("Sales", "sum"),
            Profit=("Gross Profit", "sum")
        )
        .reset_index()
    )

    # Calculate Margin percentage
    margin_df["Margin"] = (margin_df["Profit"] / margin_df["Sales"]) * 100

    # Create scatter chart mapping color directly to the full Product Name
    fig_margin = px.scatter(
        margin_df,
        x="Sales",
        y="Margin",
        size="Profit",
        color="Product Name",  # <--- Maps full names cleanly to a list on the side
        hover_name="Product Name",
        size_max=35,
        color_discrete_sequence=px.colors.qualitative.Pastel,  # High-contrast clean colors
        title="Sales vs Gross Margin"
    )

    # Polish the marker outlines
    fig_margin.update_traces(
        marker=dict(
            line=dict(color="white", width=1.2),
            opacity=0.85
        )
    )

    # Configure layout and style the legend sidebar
    fig_margin.update_layout(
        template="plotly_dark",
        title_x=0.5,
        xaxis_title="Total Sales ($)",
        yaxis_title="Gross Margin (%)",
        height=700,

        # Clean sidebar legend structure
        legend=dict(
            title="Products",
            font=dict(size=11),
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.02  # Places the legend neatly outside the grid
        ),
        margin=dict(l=50, r=50, t=60, b=50)
    )

    # Set tight axis bounds so bottom/left points aren't squished or hidden
    fig_margin.update_xaxes(
        range=[-1000, max(margin_df["Sales"]) * 1.05],
        tickformat="$,.0f",
        tickfont=dict(size=12),
        gridcolor="rgba(255,255,255,0.1)"
    )

    fig_margin.update_yaxes(
        range=[0, max(margin_df["Margin"]) * 1.05],  # Start exactly at 0% margin up to the highest point
        tickformat=".0f",  # Displays clean percentage ticks
        tickfont=dict(size=12),
        gridcolor="rgba(255,255,255,0.1)"
    )

    st.plotly_chart(fig_margin, use_container_width=True)

    # ==========================================================
    # BUSINESS INSIGHTS
    # ==========================================================
    st.divider()
    st.header("💡 Business Insights & Recommendations")

    col1, col2 = st.columns(2)

    with col1:
        st.success("""
### 📈 Key Findings

✅ Chocolate Division generates the highest revenue.

✅ Top 4 products contribute nearly 80% of total sales.

✅ Pacific Region is the best-performing region.

✅ Gross Margin is approximately 66%.

✅ Most revenue comes from a few premium chocolate products.
""")

    with col2:
        st.warning("""
### 🚀 Recommendations

• Increase inventory of top-selling products.

• Focus marketing on high-margin products.

• Improve sales of low-performing products.

• Review products with low sales and low margins.

• Expand business in high-performing regions.
""")

    # ==========================================================
    # DASHBOARD SUMMARY
    # ==========================================================
    st.divider()
    st.subheader("📌 Executive Summary")

    st.success("""
### Key Takeaways

• Chocolate division is the strongest business segment.

• Top 4 products generate nearly 80% of total revenue.

• Pacific region contributes the highest revenue.

• Overall Gross Margin is approximately 66%.

• Premium chocolate products are the primary revenue drivers.

### Recommended Actions

• Increase inventory for top-selling products.

• Invest marketing budget in high-margin products.

• Improve performance of low-selling products.

• Continue expansion in high-performing regions.

• Monitor low-margin products regularly.
""")

    st.info("""
### 🟢 Overall Business Health: **Healthy**

**Recommendation:** Increase inventory for top-selling chocolate products while reviewing pricing
strategy for low-margin products.
""")

# ==========================================================
# TAB 3 - DATASET EXPLORER
# ==========================================================
with tab3:

    st.subheader("📄 Filtered Dataset")
    st.dataframe(filtered_df, use_container_width=True)

    st.divider()
    st.subheader("🧾 Dataset Summary")

    rows_count = filtered_df.shape[0]
    cols_count = filtered_df.shape[1]
    missing_values = int(filtered_df.isnull().sum().sum())
    duplicate_rows = int(filtered_df.duplicated().sum())

    d1, d2, d3, d4 = st.columns(4)

    with d1:
        st.metric("Rows", f"{rows_count:,}")

    with d2:
        st.metric("Columns", f"{cols_count:,}")

    with d3:
        st.metric("Missing Values", f"{missing_values:,}")

    with d4:
        st.metric("Duplicate Rows", f"{duplicate_rows:,}")

    st.divider()
    st.subheader("⬇ Download Filtered Dataset")

    csv = filtered_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="Filtered_Nassau_Candy_Data.csv",
        mime="text/csv"
    )

    st.divider()
    st.subheader("📊 Quick Stats")
    st.write(f"Total rows in filtered data: {len(filtered_df):,}")
    st.write(
        f"Order date range: {filtered_df['Order Date'].min().date()} "
        f"to {filtered_df['Order Date'].max().date()}"
    )
    st.dataframe(filtered_df.describe(), use_container_width=True)

# ==========================================================
# TAB 4 - ABOUT PROJECT
# ==========================================================
with tab4:

    st.subheader("ℹ️ About this Project")

    st.markdown("""
#### Project Title
**Nassau Candy Product Line Profitability Dashboard**

#### Objective
To analyze sales, profitability, product performance, regional performance, and business insights
using interactive visualizations.

#### Technologies Used
- Python
- Streamlit
- Pandas
- Plotly
- NumPy

#### Dataset
Nassau Candy Distributor Dataset

#### Dashboard Features
- KPI Dashboard
- Revenue Analysis
- Profit Analysis
- Regional Analysis
- Pareto Analysis
- Margin Risk Analysis
- Executive Summary
- Dataset Explorer & CSV Download

#### Author
**Ganesh Gugulothu**
IIIT Vadodara
""")

    st.divider()

    st.markdown("""
#### 🔗 Links
- **GitHub Repository:** _add link here_
- **Portfolio Project:** _add link here_
- **LinkedIn:** _add link here_
""")

    st.divider()

with st.container():
    st.markdown(
        """
        <div style="text-align: center; line-height: 1.6;">
            <div style="font-size: 1.35rem; font-weight: bold; margin-bottom: 4px;">
                🍬 Nassau Candy Product Line Profitability Dashboard
            </div>
            <div style="font-size: 0.95rem; opacity: 0.9;">
                Developed by <b>Ganesh Gugulothu</b> | IIIT Vadodara
            </div>
            <div style="font-size: 0.85rem; opacity: 0.75;">
                Built using <b>Python • Streamlit • Pandas • Plotly • NumPy</b>
            </div>
            <div style="font-size: 0.8rem; opacity: 0.6; margin-top: 10px;">
                © 2026 | Data Analysis & Business Intelligence
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )