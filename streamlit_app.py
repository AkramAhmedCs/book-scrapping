import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px

# ======================
# MongoDB Connection
# ======================
def get_data():
    try:
        client = MongoClient(st.secrets["MONGODB_URI"])
        db = client['book_database']
        books = list(db['books'].find({}))
        df = pd.DataFrame(books)
        st.success(f"✅ Loaded {len(df)} books from MongoDB Atlas")
        return df
    except Exception as e:
        st.error(f"❌ MongoDB Error: {str(e)}")
        try:
            df = pd.read_csv('cleaned_books.csv')
            st.warning("⚠️ Using local CSV data instead")
            return df
        except:
            st.error("No data available!")
            return pd.DataFrame()

# ======================
# Dashboard UI
# ======================
st.set_page_config(page_title="Book Dashboard", layout="wide")
st.title("📚 Book Analysis Dashboard")

# Load data
df = get_data()

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

    # Apply filters with proper syntax
    genre_mask = df['genre'].isin(genre_filter) if genre_filter else True
    price_mask = (df['price'] >= price_range[0]) & (df['price'] <= price_range[1])
    filtered_df = df[genre_mask & price_mask]

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Books", len(filtered_df))
    col2.metric("Average Price", f"${filtered_df['price'].mean():.2f}")
    col3.metric("Unique Genres", filtered_df['genre'].nunique())

    # Data Display
    with st.expander("📄 View Raw Data"):
        st.dataframe(filtered_df)

    # Visualizations
    st.header("📊 Visualizations")
    tab1, tab2 = st.tabs(["Genre Distribution", "Price Analysis"])
    
    with tab1:
        fig1 = px.bar(filtered_df, x='genre', title='Books by Genre')
        st.plotly_chart(fig1, use_container_width=True)
        
    with tab2:
        fig2 = px.box(filtered_df, x='genre', y='price', title='Price Distribution by Genre')
        st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("No book data available. Please check your connection.")
