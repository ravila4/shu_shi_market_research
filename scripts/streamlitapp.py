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
from bs4 import BeautifulSoup
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


# Navigation via sidebar for a more slide-show feel
slide = st.sidebar.selectbox("Go to Slide", ["Intro", "Product Prices", "Summary"])
if slide == "Intro":
    st.header("Welcome to Slide 1")
    st.write("Here's some introductory content.")
elif slide == "Product Prices":
    st.header("Product Prices")
    st.write("Detailed information with visualizations.")
    st.plotly_chart(plot_median_price_by_product(all_product_data))
elif slide == "Summary":
    st.header("Summary on Slide 3")
    st.write("Summary of the presentation with key takeaways.")
