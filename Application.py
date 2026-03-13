import os
import streamlit as st
import pandas as pd
import plotly.express as px

# ----------------------------------
# PAGE CONFIG
# ----------------------------------

st.set_page_config(
    page_title="OLA Ride Insights Dashboard",
    layout="wide",
    page_icon="🚕"
)

st.title("OLA Ride Insights Dashboard")

st.markdown(
    "Operational analytics dashboard for monitoring ride activity, revenue performance, cancellation trends, and customer experience."
)

st.divider()

# ----------------------------------
# LOAD DATA
# ----------------------------------

@st.cache_data
def load_data():

    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "ola_data.csv")

    columns = [
        "Time",
        "Booking_ID",
        "Booking_Status",
        "Customer_ID",
        "Vehicle_Type",
        "Pickup_Location",
        "Drop_Location",
        "V_TAT",
        "C_TAT",
        "Canceled_Rides_by_Customer",
        "Canceled_Rides_by_Driver",
        "Incomplete_Rides",
        "Incomplete_Rides_Reason",
        "Booking_Value",
        "Payment_Method",
        "Ride_Distance",
        "Driver_Ratings",
        "Customer_Rating"
    ]

    df = pd.read_csv(file_path, header=None, names=columns)

    return df


df = load_data()

# ----------------------------------
# DATA CLEANING
# ----------------------------------

def clean_data(df):

    df["Ride_Distance"] = df["Ride_Distance"].astype(str).str.replace(" km", "", regex=False)
    df["Ride_Distance"] = pd.to_numeric(df["Ride_Distance"], errors="coerce")

    df["Booking_Value"] = pd.to_numeric(df["Booking_Value"], errors="coerce")
    df["Driver_Ratings"] = pd.to_numeric(df["Driver_Ratings"], errors="coerce")
    df["Customer_Rating"] = pd.to_numeric(df["Customer_Rating"], errors="coerce")

    return df


df = clean_data(df)

# ----------------------------------
# SIDEBAR FILTERS
# ----------------------------------

st.sidebar.header("Filter Options")

vehicle_filter = st.sidebar.multiselect(
    "Vehicle Type",
    df["Vehicle_Type"].dropna().unique(),
    default=df["Vehicle_Type"].dropna().unique()
)

status_filter = st.sidebar.multiselect(
    "Booking Status",
    df["Booking_Status"].dropna().unique(),
    default=df["Booking_Status"].dropna().unique()
)

payment_filter = st.sidebar.multiselect(
    "Payment Method",
    df["Payment_Method"].dropna().unique(),
    default=df["Payment_Method"].dropna().unique()
)

filtered_df = df[
    (df["Vehicle_Type"].isin(vehicle_filter)) &
    (df["Booking_Status"].isin(status_filter)) &
    (df["Payment_Method"].isin(payment_filter))
]

# ----------------------------------
# KPI METRICS
# ----------------------------------

st.subheader("Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

total_rides = filtered_df["Booking_ID"].count()
total_revenue = filtered_df["Booking_Value"].sum()
avg_distance = filtered_df["Ride_Distance"].mean()
avg_rating = filtered_df["Customer_Rating"].mean()

col1.metric("Total Rides", f"{total_rides:,}")
col2.metric("Total Revenue", f"₹ {total_revenue:,.0f}")
col3.metric("Average Ride Distance", f"{avg_distance:.2f} km")
col4.metric("Average Customer Rating", f"{avg_rating:.2f}")

st.divider()

# ----------------------------------
# REVENUE & STATUS CHARTS
# ----------------------------------

col1, col2 = st.columns(2)

with col1:

    st.subheader("Revenue by Vehicle Type")

    revenue = filtered_df.groupby("Vehicle_Type")["Booking_Value"].sum().reset_index()

    fig_revenue = px.bar(
        revenue,
        x="Vehicle_Type",
        y="Booking_Value",
        color="Vehicle_Type"
    )

    st.plotly_chart(fig_revenue, use_container_width=True)

with col2:

    st.subheader("Ride Status Distribution")

    cancel_data = filtered_df.groupby("Booking_Status")["Booking_ID"].count().reset_index()

    fig_cancel = px.pie(
        cancel_data,
        names="Booking_Status",
        values="Booking_ID"
    )

    st.plotly_chart(fig_cancel, use_container_width=True)

# ----------------------------------
# RATINGS ANALYSIS
# ----------------------------------

st.subheader("Driver and Customer Rating Analysis")

ratings = filtered_df.groupby("Vehicle_Type")[["Driver_Ratings","Customer_Rating"]].mean().reset_index()

fig_ratings = px.bar(
    ratings,
    x="Vehicle_Type",
    y=["Driver_Ratings","Customer_Rating"],
    barmode="group"
)

st.plotly_chart(fig_ratings, use_container_width=True)

# ----------------------------------
# DATASET VIEW
# ----------------------------------

with st.expander("Show Filtered Dataset"):
    st.dataframe(filtered_df)

# ----------------------------------
# NORMALIZED TABLES
# ----------------------------------

st.subheader("Normalized Data Tables")

customer_df = df[["Customer_Rating"]].drop_duplicates()
driver_df = df[["Driver_Ratings"]].drop_duplicates()

ride_df = df[
    [
        "Booking_ID",
        "Vehicle_Type",
        "Ride_Distance",
        "Booking_Status",
        "Booking_Value"
    ]
]

payment_df = df[
    [
        "Booking_ID",
        "Payment_Method"
    ]
]

tab1, tab2, tab3, tab4 = st.tabs(["Customers", "Drivers", "Rides", "Payments"])

with tab1:
    st.write("Customer Data")
    st.dataframe(customer_df)

with tab2:
    st.write("Driver Data")
    st.dataframe(driver_df)

with tab3:
    st.write("Ride Data")
    st.dataframe(ride_df)

with tab4:
    st.write("Payment Data")
    st.dataframe(payment_df)