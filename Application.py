import os
import streamlit as st
import pandas as pd
import plotly.express as px

# ----------------------------------
# CONFIGURATION & DATA LOADING
# ----------------------------------

def setup_page():
    st.set_page_config(
        page_title="OLA Ride Insights Dashboard",
        layout="wide",
        page_icon="🚕"
    )

@st.cache_data
def load_data():
    """Load and return the dataset."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "ola_data.csv")
    
    if not os.path.exists(file_path):
        # Fallback if running from a higher level directory
        fallback_path = os.path.join(base_dir, "ola-ride-insights-dashboard", "project", "Dashboard", "ola_data.csv")
        if os.path.exists(fallback_path):
            file_path = fallback_path

    # Define the precise column names to map the data to since the CSV lacks headers
    # Based on the usage in the code, we need at least:
    # Date, Time (optional), Booking_ID, Booking_Status, Customer_ID, Vehicle_Type, Pickup_Location, Drop_Location,
    # V_TAT, C_TAT, Canceled_Rides_by_Customer, Canceled_Rides_by_Driver, Incomplete_Rides, Incomplete_Rides_Reason,
    # Booking_Value, Payment_Method, Ride_Distance, Driver_Ratings, Customer_Rating
    # From the python print out we saw 19 columns total.
    columns = [
        "Date", "Time", "Booking_ID", "Booking_Status", "Customer_ID", 
        "Vehicle_Type", "Pickup_Location", "Drop_Location", "V_TAT", "C_TAT", 
        "Canceled_Rides_by_Customer", "Canceled_Rides_by_Driver", "Incomplete_Rides", 
        "Incomplete_Rides_Reason", "Booking_Value", "Payment_Method", "Ride_Distance", 
        "Driver_Ratings", "Customer_Rating"
    ]
            
    df = pd.read_csv(file_path, header=None, names=columns)
    return df

def clean_data(df):
    """Perform data cleaning on the dataset."""

    # Convert Date column properly
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date

    df["Ride_Distance"] = df["Ride_Distance"].astype(str).str.replace(" km", "", regex=False)
    df["Ride_Distance"] = pd.to_numeric(df["Ride_Distance"], errors="coerce")

    df["Booking_Value"] = pd.to_numeric(df["Booking_Value"], errors="coerce")

    df["Driver_Ratings"] = pd.to_numeric(df["Driver_Ratings"], errors="coerce")
    df["Customer_Rating"] = pd.to_numeric(df["Customer_Rating"], errors="coerce")

    return df

# ----------------------------------
# UI COMPONENTS
# ----------------------------------

def render_sidebar(df):
    """Render the sidebar filters and return the filtered dataframe."""
    st.sidebar.header("Filters")

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
    return filtered_df

def render_kpi(filtered_df):
    st.subheader("Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    total_rides = filtered_df["Booking_ID"].count()
    total_revenue = filtered_df["Booking_Value"].sum()
    avg_distance = filtered_df["Ride_Distance"].mean()
    avg_rating = filtered_df["Customer_Rating"].mean()

    col1.metric("Total Rides", f"{total_rides:,}")
    col2.metric("Total Revenue", f"₹ {total_revenue:,.0f}")
    col3.metric("Average Distance", f"{avg_distance:.2f} km")
    col4.metric("Avg Customer Rating", f"{avg_rating:.2f}")

    st.divider()

def render_charts(filtered_df):
    st.subheader("Ride Trend Over Time")
    ride_trend = filtered_df.dropna(subset=["Date"]).groupby("Date")["Booking_ID"].count().reset_index()
    fig_trend = px.line(
        ride_trend, x="Date", y="Booking_ID", markers=True, title="Ride Trends Over Time"
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Revenue by Vehicle Type")
        revenue = filtered_df.groupby("Vehicle_Type")["Booking_Value"].sum().reset_index()
        fig_revenue = px.bar(
            revenue, x="Vehicle_Type", y="Booking_Value", color="Vehicle_Type", title="Revenue by Vehicle Type"
        )
        st.plotly_chart(fig_revenue, use_container_width=True)

    with col2:
        st.subheader("Ride Status Distribution")
        cancel_data = filtered_df.groupby("Booking_Status")["Booking_ID"].count().reset_index()
        fig_cancel = px.pie(
            cancel_data, names="Booking_Status", values="Booking_ID", title="Ride Status Distribution"
        )
        st.plotly_chart(fig_cancel, use_container_width=True)

    st.subheader("Driver vs Customer Ratings")
    ratings = filtered_df.groupby("Vehicle_Type")[["Driver_Ratings","Customer_Rating"]].mean().reset_index()
    fig_ratings = px.bar(
        ratings, x="Vehicle_Type", y=["Driver_Ratings","Customer_Rating"], barmode="group", title="Ratings Comparison by Vehicle Type"
    )
    st.plotly_chart(fig_ratings, use_container_width=True)

    with st.expander("Show Filtered Dataset"):
        st.dataframe(filtered_df)

def render_tables(df):
    st.header("Normalized Tables")
    customer_df = df[["Customer_Rating"]].drop_duplicates()
    driver_df = df[["Driver_Ratings"]].drop_duplicates()
    ride_df = df[["Booking_ID", "Vehicle_Type", "Ride_Distance", "Booking_Status", "Booking_Value"]]
    payment_df = df[["Booking_ID", "Payment_Method"]]

    tab1, tab2, tab3, tab4 = st.tabs(["Customers", "Drivers", "Rides", "Payments"])

    with tab1:
        st.subheader("Customer Table")
        st.dataframe(customer_df)
    with tab2:
        st.subheader("Driver Table")
        st.dataframe(driver_df)
    with tab3:
        st.subheader("Ride Table")
        st.dataframe(ride_df)
    with tab4:
        st.subheader("Payment Table")
        st.dataframe(payment_df)

# ----------------------------------
# MAIN APP ENTRY
# ----------------------------------

def main():
    setup_page()
    
    st.title("🚕 OLA Ride Insights Dashboard")
    st.markdown("Operational dashboard for analyzing ride trends, revenue, cancellations, and ratings.")
    
    try:
        df_raw = load_data()
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return

    df_clean = clean_data(df_raw.copy())
    
    filtered_df = render_sidebar(df_clean)
    
    if not filtered_df.empty:
        render_kpi(filtered_df)
        render_charts(filtered_df)
    else:
        st.warning("No data matches the selected filters.")
        
    render_tables(df_clean)

if __name__ == "__main__":
    main()