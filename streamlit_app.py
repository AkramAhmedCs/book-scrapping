import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient

# Connect to MongoDB
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    db = client['book_database']
    df = pd.DataFrame(list(db['books'].find({})))
except Exception as e:
    st.error(f"Database connection failed: {e}")
    df = pd.DataFrame()

st.title("📚 Book Analysis Dashboard")

if not df.empty:
    # Filters
    genre_filter = st.sidebar.multiselect('Filter by Genre', df['genre'].unique())
    price_range = st.sidebar.slider('Price Range', 
                                  float(df['price'].min()), 
                                  float(df['price'].max()),
                                  (float(df['price'].min()), float(df['price'].max())))

    # Apply filters
    filtered_df = df[
        (df['genre'].isin(genre_filter) if genre_filter else True) &
        (df['price'].between(price_range[0], price_range[1]))
    ]

    # Metrics
    col1, col2 = st.columns(2)
    col1.metric("Total Books", len(filtered_df))
    col2.metric("Average Price", f"${filtered_df['price'].mean():.2f}")

    # Visualizations
    if not filtered_df.empty:
        st.plotly_chart(px.bar(filtered_df, x='genre', title='📊 Books by Genre'))
        st.plotly_chart(px.box(filtered_df, x='genre', y='price', title='💰 Price Distribution'))
    
    # Raw data
    if st.checkbox('Show Raw Data'):
        st.dataframe(filtered_df)
else:
    st.warning("No book data available. Please run the scraper first.")
