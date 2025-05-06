import streamlit as st
import pandas as pd
import plotly.express as px

# ======================
# Load Data from CSV
# ======================
@st.cache_data  # Cache for better performance
def load_data():
    try:
        df = pd.read_csv('cleaned_books.csv')
        return df
    except FileNotFoundError:
        st.error("❌ Error: cleaned_books.csv not found!")
        st.stop()

# ======================
# Dashboard UI
# ======================
st.set_page_config(page_title="Book Dashboard", layout="wide")
st.title("📚 Book Analysis Dashboard")

# Load data
df = load_data()

# Filters
st.sidebar.header("Filters")
genre_filter = st.sidebar.multiselect(
    "Select Genres",
    options=df['genre'].unique()
)
price_range = st.sidebar.slider(
    "Price Range",
    float(df['price'].min()),
    float(df['price'].max()),
    (float(df['price'].min()), float(df['price'].max()))
)

# Apply filters
filtered_df = df[
    (df['genre'].isin(genre_filter) if genre_filter else True) &
    (df['price'].between(price_range[0], price_range[1]))
]

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Books", len(filtered_df))
col2.metric("Average Price", f"${filtered_df['price'].mean():.2f}")
col3.metric("Unique Genres", filtered_df['genre'].nunique())

# Data Display - Modified to exclude ISBN column
with st.expander("📄 View Raw Data"):
    st.dataframe(filtered_df.drop(columns=['isbn'], errors='ignore'))  # Modified line

# Visualizations
st.header("📊 Visualizations")
tab1, tab2 = st.tabs(["Genre Distribution", "Price Analysis"])

with tab1:
    fig1 = px.bar(filtered_df, x='genre', title='Books by Genre')
    st.plotly_chart(fig1, use_container_width=True)
    
with tab2:
    fig2 = px.box(filtered_df, x='genre', y='price', title='Price Distribution by Genre')
    st.plotly_chart(fig2, use_container_width=True)
