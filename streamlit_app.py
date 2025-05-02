import streamlit as st
from pymongo import MongoClient
import pandas as pd
import os

# Set page config (optional)
st.set_page_config(page_title="Book Dashboard", layout="wide")

# MongoDB Atlas Connection
try:
    # Get connection string from Streamlit secrets
    client = MongoClient(st.secrets["MONGODB_URI"])
    db = client['book_database']
    collection = db['books']
    
    # Fetch data with progress indicator
    with st.spinner("📡 Connecting to MongoDB Atlas..."):
        books_data = list(collection.find({}))
        df = pd.DataFrame(books_data)
    
    st.success(f"✅ Success! Loaded {len(df)} books from MongoDB Atlas")
    
except Exception as e:
    st.error(f"❌ MongoDB connection failed: {str(e)}")
    
    # CSV Fallback with caching
    @st.cache_data
    def load_csv():
        return pd.read_csv('cleaned_books.csv')
    
    try:
        df = load_csv()
        st.warning("⚠️ Using local CSV data instead")
    except:
        st.error("No data available!")
        df = pd.DataFrame()

# Dashboard UI
st.title("📚 Book Analysis Dashboard")

if not df.empty:
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
        (df['genre'].isin(genre_filter) if genre_filter else True
    ].query("price >= @price_range[0] & price <= @price_range[1]")

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Books", len(filtered_df))
    col2.metric("Average Price", f"${filtered_df['price'].mean():.2f}")
    col3.metric("Unique Genres", filtered_df['genre'].nunique())

    # Display data
    st.dataframe(filtered_df, height=500)
    
    # Visualizations
    st.plotly_chart(px.histogram(filtered_df, x='genre', title='Books by Genre'))
    st.plotly_chart(px.box(filtered_df, x='genre', y='price', title='Price Distribution'))
else:
    st.info("No book data available")
