import streamlit as st

import glob
import io
import logging
import random
import os
import time
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import seaborn
from IPython.display import HTML, Image, display
from PIL import Image
from plotly.io import to_image
from plotly.offline import plot
from plotly.subplots import make_subplots
from tenacity import retry, stop_after_attempt, wait_fixed, wait_random
from tqdm import tqdm
import os

current_file_path = os.path.abspath(__file__)
current_directory = os.path.dirname(current_file_path)
data_folder = os.path.join(current_directory, "../data/products/")
output_folder = os.path.join(current_directory, "../output/")

# Load the data
all_product_data = pd.read_csv(os.path.join(output_folder, "all_product_data.csv"))


def to_html(fig, file_name: str):
    """Save a Plotly figure to an HTML file."""
    plot(fig, filename=file_name)


def format_col_for_title(col: str) -> str:
    """Format a column name for a title."""
    return " ".join(col.split("_")).title()


def plot_bar_chart_plotly(
    data, x, y, sorted=True, title=None, x_label=None, y_label=None
):
    if sorted:
        data = data.sort_values(by=y, ascending=False)
    fig = go.Figure(
        go.Bar(
            x=data[x],
            y=data[y],
            name=format_col_for_title(y),
            text=data[y],
            textposition="auto",
        )
    )
    fig.update_layout(
        title=f"Bar Chart of {format_col_for_title(y)} by {format_col_for_title(x)}",
        xaxis_title=format_col_for_title(x) if x_label is None else x_label,
        yaxis_title=format_col_for_title(y) if y_label is None else y_label,
        template="simple_white",
    )
    if title:
        fig.update_layout(title=title)

    fig.update_traces(texttemplate="%{text:.2f}")
    return fig


def plot_bar_chart_plotly_with_dropdown(
    data_list, x, y, labels, sorted=True, title=None, x_label=None, y_label=None
):
    traces = []
    for data, label in zip(data_list, labels):
        if sorted:
            data = data.sort_values(by=y, ascending=False)
        trace = go.Bar(
            x=data[x],
            y=data[y],
            name=label,
            text=data[y],
            textposition="auto",
            visible=True if label == labels[0] else False,
        )
        traces.append(trace)

    fig = go.Figure(data=traces)

    # Add the dropdown menu
    fig.update_layout(
        updatemenus=[
            dict(
                buttons=[
                    dict(
                        args=[{"visible": [label == selected for label in labels]}],
                        label=selected,
                        method="update",
                    )
                    for selected in labels
                ],
                direction="down",
                pad={"r": 2, "t": 12},
                showactive=True,
                x=0,
                xanchor="left",
                y=1.3,
                yanchor="top",
            )
        ]
    )

    fig.update_layout(
        title=(
            f"Bar Chart of {format_col_for_title(y)} by {format_col_for_title(x)}"
            if title is None
            else title
        ),
        xaxis_title=format_col_for_title(x) if x_label is None else x_label,
        yaxis_title=format_col_for_title(y) if y_label is None else y_label,
        template="simple_white",
    )

    fig.update_traces(texttemplate="%{text:.2f}")

    return fig


def plot_median_price_by_product(data):
    fig = plot_bar_chart_plotly(
        data.groupby("product_name_chinese_name")
        .agg({"price": "median"})
        .reset_index(),
        x="product_name_chinese_name",
        y="price",
        title="Median Price by Product （产品价格中位数）",
        x_label="Product Name",
        y_label="Median Price ($)",
    )
    return fig


def plot_unique_products(all_product_data):
    data_list = [
        all_product_data.groupby("product_name_chinese_name")["Product URL"]
        .nunique()
        .reset_index(),
        all_product_data[all_product_data["has_sales"] == True]
        .groupby("product_name_chinese_name")["Product URL"]
        .nunique()
        .reset_index(),
    ]

    fig = plot_bar_chart_plotly_with_dropdown(
        data_list,
        labels=["All Products", "Products with Sales"],
        x="product_name_chinese_name",
        y="Product URL",
        title="Number of Unique Products （产品数目）",
        x_label="Product Name",
        y_label="Number of Unique Products",
    )
    return fig


def plot_percentage_of_products_with_sales(all_product_data):
    fig = plot_bar_chart_plotly(
        all_product_data.groupby("product_name_chinese_name")["has_sales"]
        .mean()
        .reset_index(),
        x="product_name_chinese_name",
        y="has_sales",
        title="Percentage of Products with Sales （有销售量的产品的百分比）",
        x_label="Product Name",
        y_label="Percentage of Products with Sales (%)",
    )
    return fig


def plot_total_sales_by_product(data):
    fig = plot_bar_chart_plotly(
        data.groupby("product_name_chinese_name")["Total Sales"].sum().reset_index(),
        x="product_name_chinese_name",
        y="Total Sales",
        title="Total Sales by Product（产品总销售量）",
        x_label="Product Name",
        y_label="Total Sales",
    )
    return fig


def generate_median_sales_figure(all_product_data):
    data_list = [
        all_product_data.groupby("product_name_chinese_name")["Total Sales"]
        .median()
        .reset_index(),
        all_product_data[all_product_data["has_sales"] == True]
        .groupby("product_name_chinese_name")["Total Sales"]
        .median()
        .reset_index(),
    ]

    # Median total sales by product
    fig = plot_bar_chart_plotly_with_dropdown(
        data_list,
        labels=["All Products", "Products with Sales"],
        x="product_name_chinese_name",
        y="Total Sales",
        title="Median Total Sales by Product（产品平均销售量）",
        x_label="Product Name",
        y_label="Median Total Sales",
    )
    return fig


def plot_total_revenue_by_product(all_product_data):
    data_list = [
        all_product_data.groupby("product_name_chinese_name")["proceeds"]
        .sum()
        .reset_index()
    ]

    fig = plot_bar_chart_plotly(
        data_list[0],
        x="product_name_chinese_name",
        y="proceeds",
        title="Total Revenue by Product（产品总销售额）",
        x_label="Product Name",
        y_label="Total Revenue",
    )

    return fig


def generate_median_revenue_figure(all_product_data):
    data_list = [
        all_product_data.groupby("product_name_chinese_name")["proceeds"]
        .median()
        .reset_index(),
        all_product_data[all_product_data["has_sales"] == True]
        .groupby("product_name_chinese_name")["proceeds"]
        .median()
        .reset_index(),
    ]

    labels = ["All Products", "Products with Sales"]

    fig = plot_bar_chart_plotly_with_dropdown(
        data_list=data_list,
        x="product_name_chinese_name",
        y="proceeds",
        labels=labels,
        title="Median Revenue by Product（产品销售额中位数）",
        x_label="Product Name",
        y_label="Median Revenue ($)",
    )
    return fig


def plot_heatmap_plotly(
    data,
    x,
    y,
    z,
    title=None,
    x_label=None,
    y_label=None,
    log_scale=False,
    colorbar_title=None,
):
    if log_scale:
        data[z] = np.log(data[z] + 1)
    fig = go.Figure(
        data=go.Heatmap(
            x=data[x],
            y=data[y],
            z=data[z],
            colorscale="blues_r",
            hoverongaps=False,
            colorbar_title=colorbar_title,
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        template="plotly_dark",
        width=1000,
        height=1000,
    )

    return fig


def calculate_sales_heatmap(all_product_data):
    product_store_sales = (
        all_product_data[all_product_data["has_sales"] == True]
        .groupby(["product_name_chinese_name", "Store Name"])["Total Sales"]
        .sum()
        .reset_index()
    )

    # Calculate the total sales for each product
    product_total_revenue = (
        all_product_data[all_product_data["has_sales"] == True]
        .groupby("product_name_chinese_name")["Total Sales"]
        .sum()
    )

    # Calculate the percentage of total sales for each product in each store
    product_store_sales["Percentage of Total Sales"] = product_store_sales.apply(
        lambda row: row["Total Sales"]
        / product_total_revenue[row["product_name_chinese_name"]],
        axis=1,
    )

    # Create the heatmap
    fig = plot_heatmap_plotly(
        data=product_store_sales,
        x="product_name_chinese_name",
        y="Store Name",
        z="Percentage of Total Sales",
        title="Percentage of Total Sales by Product and Store (With Sales)",
        x_label="Product Name",
        y_label="Store Name",
        colorbar_title="%",
    )

    return fig


# Navigation via sidebar for a more slide-show feel
slide = st.sidebar.selectbox(
    "Go to Slide",
    [
        "Intro",
        "Overview of Search Results",
        "Product Pricing",
        "Product Sales",
        "Product Revenue",
        "Competitor Analysis",
    ],
)
if slide == "Intro":
    st.header("Etsy Product Research")
    st.image(
        "https://cdn.shopify.com/s/files/1/0643/9262/6408/files/image1_7be85aec-6deb-413b-ba96-c23fa38dec3e.png?v=1701654032"
    )
    st.markdown(
        """
        ### We collected statistics on a total of 3,500+ unique products across 13 categories.
        - bead bracelets and necklaces: 珠子手链和项链
        - chinese mid autumn gift sets: 中秋节礼品套装
        - chinese pottery: 中国陶器
        - chinese incense: 中国香
        - chinese magnets: 中国冰箱贴
        - paper lanterns: 纸灯笼
        - chinese bamboo art: 中国竹艺
        - chinese washi tape: 中国和纸胶带
        - chinese art stickers: 中国艺术贴纸
        - brushes and calligraphy tools: 笔和书法工具
        - calligraphy prints: 书法印刷品
        - chinese bookmarks: 中国书签
        - name seals: 印章

        For each product, we generated a list of synonymous search terms, and collected combined the results of the first 60 pages.
        For example, for the product "calligraphy prints", we searched for "chinese calligraphy prints", "chinese art prints", "chinese wall art", etc.
        """
    )

elif slide == "Overview of Search Results":
    st.header("Overview of Search Results")
    st.plotly_chart(plot_unique_products(all_product_data))
    # Let's add some bullet points
    st.markdown(
        """
        - The search results with the most hits were for calligraphy prints and name seals. This may indicate more competition in these categories.

        ## Top 10 products for each category
        """
    )
    st.image(os.path.join(current_directory, "top_products_1.png"))
    st.image(os.path.join(current_directory, "top_products_2.png"))

elif slide == "Product Pricing":
    st.header("Evaluating Product Pricing")
    st.plotly_chart(plot_median_price_by_product(all_product_data))
    st.markdown(
        """
            - We can see that the price of products varies significantly between categories.
            - Chinese pottery, bracelets and necklaces, and name seals have the highest median prices, as expected.
        """
    )

elif slide == "Product Sales":
    st.header("Product Sales")
    st.markdown(
        """
        - The Total Sales column represents the total number of sales across all search results for each product.
        - It is important to consider that the number of search results for each product varies, so we also calculate the median sales.
        """
    )
    st.plotly_chart(plot_total_sales_by_product(all_product_data))
    st.plotly_chart(generate_median_sales_figure(all_product_data))
    st.plotly_chart(plot_percentage_of_products_with_sales(all_product_data))
    st.markdown(
        """
        - Items with a high percentage of sales (over 50%) may be worth exploring further.
        - Mid-autumn festival gifts seems to have a high percentage of sales, but it is a broad category, so we need to explore further.
        """
    )


elif slide == "Product Revenue":
    st.header("Product Revenue")
    st.markdown(
        """
        - Revenue is calculated as the total sales multiplied by the price.
        - In the case of total revenue, we sum the total revenue for each product, this is affected by the number of search results that we have for each product.
        - Therefore, it is important to also consider the median revenue, which is less affected by the number of search results.
        """
    )
    st.plotly_chart(plot_total_revenue_by_product(all_product_data))
    st.plotly_chart(generate_median_revenue_figure(all_product_data))

    st.markdown(
        """
        - The product with the highest median revenue is name seals, this is due to their higher price, while still having high demand.
        - Mid-autumn festival gift sets also have high median revenue, which is consistent with their high percentage of sales.
        - Washi tape also shows up as a high revenue product. Interestingly, it is also one of the least expensive products.
        """
    )

elif slide == "Competitor Analysis":
    st.header("Competitor Analysis")
    st.markdown(
        """
        - We can also analyze the percentage of total sales for each product in each store. This can help us identify which stores are selling the most of each product.
        - In this plot, we show the percentage of product sold in each store for products that have sales.
        """
    )
    st.plotly_chart(calculate_sales_heatmap(all_product_data))
